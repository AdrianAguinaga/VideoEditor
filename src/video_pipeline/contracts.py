"""Versioned data contracts (domain layer). JSON Schemas in config/schemas/ are generated from these.

Time convention: every time value is an integer number of milliseconds, and every range is
half-open [start_ms, end_ms).
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .util import ID_PATTERN

Id = Annotated[str, StringConstraints(pattern=ID_PATTERN, max_length=64)]
Ms = Annotated[int, Field(ge=0)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
VideoKey = Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]+/[a-z0-9-]+$")]  # "<series>/<video>"
Color = Annotated[str, StringConstraints(pattern=r"^#?[A-Za-z0-9]+(@[0-9.]+)?$")]  # FFmpeg color: goes into a graph


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _unique(values: list[Any], what: str) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {what}: {value}")
        seen.add(value)


# --- configuration -------------------------------------------------------------------------------


class Profile(Model):
    width: Annotated[int, Field(gt=0, multiple_of=2)]
    height: Annotated[int, Field(gt=0, multiple_of=2)]
    fps: Annotated[int, Field(gt=0, le=120)]
    sample_rate: Literal[44100, 48000] = 48000
    video_codec: Literal["libx264"] = "libx264"
    crf: Annotated[int, Field(ge=0, le=51)] = 20
    preset: str = "medium"
    audio_bitrate: str = "192k"
    preview_height: Annotated[int, Field(gt=0, multiple_of=2)] = 480


class AssetRef(Model):
    id: Id
    version: Annotated[int, Field(ge=1)]


class AsrSettings(Model):
    model: str = "faster-whisper-medium"
    language: str = "es"
    device: Literal["cpu", "cuda", "auto"] = "cpu"
    compute_type: str = "int8"
    beam_size: Annotated[int, Field(ge=1, le=10)] = 5
    vad_filter: bool = True
    word_timestamps: bool = True


class StyleSettings(Model):
    intro: AssetRef | None = None
    outro: AssetRef | None = None
    background_color: str = "black"
    background: AssetRef | None = None  # image asset behind every source clip (seen in letterbox or with inset)
    background_blur: bool = False  # fill the letterbox with a blurred, enlarged copy of the clip itself
    inset_pct: Annotated[int, Field(ge=0, le=40)] = 0  # shrink source clips so the background frames them


class AudioSettings(Model):
    """Voice cleanup on source clips and loudness on the final mix. Every step is off unless set."""

    highpass_hz: Annotated[int, Field(ge=20, le=300)] | None = None  # rumble/hum below the voice (80 is typical)
    denoise_db: Annotated[int, Field(ge=1, le=40)] | None = None  # steady background noise reduction (afftdn)
    compress: bool = False  # even out loud and soft speech
    loudness_lufs: Annotated[float, Field(ge=-30, le=-10)] | None = None  # EBU R128 target: -16 web, -23 broadcast
    true_peak_db: Annotated[float, Field(ge=-9, le=0)] = -1.5
    edge_fade_ms: Annotated[int, Field(ge=0, le=200)] = 0  # micro fade at every clip edge: no clicks at cuts


class ColorSettings(Model):
    """Basic correction applied to source clips (cortinillas are finished pieces and stay untouched)."""

    brightness: Annotated[float, Field(ge=-1, le=1)] = 0
    contrast: Annotated[float, Field(ge=0, le=3)] = 1
    saturation: Annotated[float, Field(ge=0, le=3)] = 1
    gamma: Annotated[float, Field(ge=0.1, le=10)] = 1


class QaSettings(Model):
    # One video frame (33 ms @30fps) + one AAC frame (21 ms @48 kHz) + margin.
    duration_tolerance_ms: Annotated[int, Field(ge=0)] = 100


class Settings(Model):
    """Fully resolved settings: workspace < series < video < approved run override."""

    profile: str = "1080p30"
    asr: AsrSettings = AsrSettings()
    style: StyleSettings = StyleSettings()
    audio: AudioSettings = AudioSettings()
    color: ColorSettings = ColorSettings()
    qa: QaSettings = QaSettings()


class Policy(Model):
    originals: Literal["copy"] = "copy"
    processing: Literal["local"] = "local"


class WorkspaceConfig(Model):
    schema_version: Literal[1] = 1
    name: str
    policy: Policy = Policy()
    defaults: dict[str, Any] = {}


class SeriesConfig(Model):
    schema_version: Literal[1] = 1
    id: Id
    title: str
    language: str = "es"
    videos: list[Id] = []  # canonical order; titles live in each video.yaml
    defaults: dict[str, Any] = {}

    @model_validator(mode="after")
    def _check(self) -> SeriesConfig:
        _unique(self.videos, "video id")
        return self


class EditorialPolicy(Model):
    propose: list[str] = ["errores", "repeticiones"]
    preserve: list[str] = ["negaciones", "cifras", "pasos", "pausas pedagógicas"]


class VideoConfig(Model):
    schema_version: Literal[1] = 1
    id: Id
    series: Id
    title: str
    privacy: Literal["private", "internal", "public"] = "private"
    editorial: EditorialPolicy = EditorialPolicy()
    overrides: dict[str, Any] = {}


# --- media and inventories -----------------------------------------------------------------------


class MediaInfo(Model):
    kind: Literal["video", "audio", "image"]
    format_name: str
    duration_ms: Ms | None
    has_video: bool
    has_audio: bool
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    codecs: list[str] = []


InputRole = Literal["originals", "audio", "slides", "images", "broll", "scripts"]


class InputRecord(Model):
    id: Id
    role: InputRole
    original_name: str
    path: str  # relative to the video directory
    sha256: Sha256
    size_bytes: Annotated[int, Field(ge=0)]
    ingested_at: str
    media: MediaInfo


class InputInventory(Model):
    schema_version: Literal[1] = 1
    video: VideoKey
    inputs: list[InputRecord] = []

    @model_validator(mode="after")
    def _check(self) -> InputInventory:
        _unique([i.id for i in self.inputs], "input id")
        return self


class AssetRecord(Model):
    id: Id
    version: Annotated[int, Field(ge=1)]
    kind: Literal["cortinilla", "logo", "image", "font", "music", "sfx", "template"]
    role: str | None = None  # entrada / salida / transicion ...
    path: str  # relative to the workspace root
    sha256: Sha256
    license: str
    permissions: str
    synthetic_fixture: bool = False
    registered_at: str
    media: MediaInfo | None = None


class AssetRegistry(Model):
    schema_version: Literal[1] = 1
    assets: list[AssetRecord] = []

    @model_validator(mode="after")
    def _check(self) -> AssetRegistry:
        _unique([(a.id, a.version) for a in self.assets], "asset id@version")
        return self


# --- editorial -----------------------------------------------------------------------------------


class Word(Model):
    start_ms: Ms
    end_ms: Ms
    text: str
    probability: float | None = None


class Segment(Model):
    id: int
    start_ms: Ms
    end_ms: Ms
    text: str
    words: list[Word] = []


class BackendInfo(Model):
    name: str
    version: str
    model: str
    revision: str | None
    device: str
    compute_type: str


class Transcript(Model):
    """Raw ASR output. Never edited in place; a reviewed text goes in a separate file."""

    schema_version: Literal[1] = 1
    video: VideoKey
    input_id: Id
    input_sha256: Sha256
    language: str
    language_probability: float | None = None
    duration_ms: Ms
    created_at: str
    backend: BackendInfo
    segments: list[Segment]
    limitations: list[str] = []


class Transition(Model):
    """Blend from the previous clip into this one. Both overlap by `ms`, so the output gets that much shorter."""

    type: Literal[
        "fade",  # classic cross-dissolve
        "fadeblack",
        "fadewhite",
        "dissolve",  # pixel dissolve
        "wipeleft",
        "wiperight",
        "wipeup",
        "wipedown",
        "slideleft",
        "slideright",
        "smoothleft",
        "smoothright",
        "circleopen",
        "circleclose",
        "radial",
        "zoomin",
        "pixelize",
    ] = "fade"
    ms: Annotated[int, Field(ge=100, le=3000, multiple_of=100)] = 500  # whole frames at 25/30/50/60 fps


class SourceClip(Model):
    kind: Literal["source"] = "source"
    input: Id
    in_ms: Ms
    out_ms: Ms
    still: Id | None = None  # image input used as picture for audio-only sources
    transition: Transition | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _check(self) -> SourceClip:
        if self.out_ms <= self.in_ms:
            raise ValueError(f"clip {self.input}: out_ms must be greater than in_ms")
        return self


class AssetClip(Model):
    kind: Literal["asset"] = "asset"
    asset: Id
    version: Annotated[int, Field(ge=1)]
    in_ms: Ms = 0
    out_ms: Ms | None = None  # None = until the end of the asset
    transition: Transition | None = None

    @model_validator(mode="after")
    def _check(self) -> AssetClip:
        if self.out_ms is not None and self.out_ms <= self.in_ms:
            raise ValueError(f"asset {self.asset}: out_ms must be greater than in_ms")
        return self


Clip = Annotated[SourceClip | AssetClip, Field(discriminator="kind")]


class Cut(Model):
    """A removed range, kept for editorial review. Only `accepted` cuts may reach a master."""

    input: Id
    start_ms: Ms
    end_ms: Ms
    reason: str
    text: str = ""
    status: Literal["proposed", "accepted", "rejected"] = "proposed"

    @model_validator(mode="after")
    def _check(self) -> Cut:
        if self.end_ms <= self.start_ms:
            raise ValueError("cut end_ms must be greater than start_ms")
        return self


class Region(Model):
    """A rectangle (in the input's pixels) while [start_ms, end_ms) of that input plays."""

    input: Id
    start_ms: Ms
    end_ms: Ms
    x: Annotated[int, Field(ge=0)]
    y: Annotated[int, Field(ge=0)]
    w: Annotated[int, Field(gt=0)]
    h: Annotated[int, Field(gt=0)]
    reason: str

    @model_validator(mode="after")
    def _check(self) -> Region:
        if self.end_ms <= self.start_ms:
            raise ValueError(f"{type(self).__name__.lower()} end_ms must be greater than start_ms")
        return self


class Blur(Region):
    """Blurs the rectangle: hides personal data, never cuts."""


class Zoom(Region):
    """Punch-in: the rectangle fills the frame (aspect kept, edges trimmed) to show a detail of the screen."""


Position = Literal["top-left", "top", "top-right", "center", "bottom-left", "bottom", "bottom-right"]


class Overlay(Model):
    """An image (logo, watermark) or text (lower third, title) drawn over the picture.

    Times are source time of `input` when given (follows the edit, like cuts), else output time.
    """

    asset: Id | None = None  # registered logo/image
    version: Annotated[int, Field(ge=1)] | None = None
    text: str | None = None  # "\n" splits lines
    input: Id | None = None
    start_ms: Ms = 0
    end_ms: Ms | None = None  # None = until the end
    position: Position = "bottom-left"
    size_pct: Annotated[float, Field(gt=0, le=100)] = 5  # image: % of frame width; text: % of frame height
    opacity: Annotated[float, Field(ge=0, le=1)] = 1
    color: Color = "white"  # text
    font: AssetRef | None = None  # registered font for text; default: a system sans font
    box_color: Color | None = "black@0.6"  # text background bar; None = no bar
    margin_pct: Annotated[float, Field(ge=0, le=25)] = 4

    @model_validator(mode="after")
    def _check(self) -> Overlay:
        if (self.asset is None) == (self.text is None):
            raise ValueError("overlay needs exactly one of `asset` or `text`")
        if (self.asset is None) != (self.version is None):
            raise ValueError("overlay `asset` and `version` go together")
        if self.text is not None and not self.text.strip():
            raise ValueError("overlay text is empty")
        if self.font is not None and self.text is None:
            raise ValueError("overlay `font` only applies to text")
        if self.end_ms is not None and self.end_ms <= self.start_ms:
            raise ValueError("overlay end_ms must be greater than start_ms")
        return self


class Music(Model):
    """A registered music/sfx asset under the output range [start_ms, end_ms), looped if shorter."""

    asset: Id
    version: Annotated[int, Field(ge=1)]
    start_ms: Ms = 0  # output time
    end_ms: Ms | None = None  # None = until the end of the video
    volume_db: Annotated[float, Field(ge=-60, le=6)] = -18
    duck: bool = True  # dip under the voice (sidechain); turn off for sound effects
    fade_ms: Ms = 1000

    @model_validator(mode="after")
    def _check(self) -> Music:
        if self.end_ms is not None and self.end_ms <= self.start_ms:
            raise ValueError("music end_ms must be greater than start_ms")
        return self


class Timeline(Model):
    schema_version: Literal[1] = 1
    video: VideoKey
    transcripts: list[str] = []  # paths relative to the video directory
    subtitles: bool = True
    clips: Annotated[list[Clip], Field(min_length=1)]
    cuts: list[Cut] = []
    blurs: list[Blur] = []
    zooms: list[Zoom] = []
    overlays: list[Overlay] = []
    music: list[Music] = []
    fade_in_ms: Annotated[int, Field(ge=0, le=5000)] = 0  # from black/silence at the start of the video
    fade_out_ms: Annotated[int, Field(ge=0, le=5000)] = 0  # to black/silence at the end


# --- approvals and runs --------------------------------------------------------------------------


class Approval(Model):
    schema_version: Literal[1] = 1
    id: str
    video: VideoKey
    run_id: str
    artifact: str
    artifact_sha256: Sha256
    timeline_sha256: Sha256
    scope: Literal["edit-for-master"] = "edit-for-master"
    actor: str
    approved_at: str
    note: str = ""


class Artifact(Model):
    role: str
    path: str  # relative to the run directory
    sha256: Sha256
    size_bytes: int


class QaCheck(Model):
    name: str
    status: Literal["passed", "failed", "skipped"]
    detail: str = ""


class RunRecord(Model):
    schema_version: Literal[1] = 1
    id: str
    video: VideoKey
    mode: Literal["preview", "master"]
    status: Literal["running", "succeeded", "failed"]
    started_at: str
    finished_at: str | None = None
    timeline: str
    timeline_sha256: Sha256
    approval: str | None = None
    expected_duration_ms: Ms | None = None
    inputs: dict[str, str] = {}  # input id -> sha256
    assets: dict[str, str] = {}  # asset id@version -> sha256
    tools: dict[str, str] = {}
    commands: list[list[str]] = []
    artifacts: list[Artifact] = []
    qa: list[QaCheck] = []
    error: str | None = None
    next_action: str | None = None


SCHEMAS: dict[str, type[Model]] = {
    "workspace": WorkspaceConfig,
    "profile": Profile,
    "settings": Settings,
    "series": SeriesConfig,
    "video": VideoConfig,
    "inputs": InputInventory,
    "assets": AssetRegistry,
    "transcript": Transcript,
    "timeline": Timeline,
    "approval": Approval,
    "run": RunRecord,
}
