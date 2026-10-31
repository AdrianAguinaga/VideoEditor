# Timeline format (schema: config/schemas/timeline.schema.json)

Times are integer **milliseconds**, and ranges are half-open `[in_ms, out_ms)` in **source** time.
Output positions are computed: clips play back to back in list order.

```yaml
schema_version: 1
video: curso-contabilidad/clase-001          # must match the video
transcripts: [editorial/transcript/grabacion.20261027T120000.asr.json]
subtitles: true                              # remapped to output time automatically
clips:
  - {kind: asset, asset: cortinilla-entrada, version: 1}      # registered id@version
  - {kind: source, input: grabacion, in_ms: 0, out_ms: 41250}
  - {kind: source, input: grabacion, in_ms: 43800, out_ms: 600000, note: "tras repetición"}
  - {kind: source, input: voz-extra, in_ms: 0, out_ms: 5000, still: slide-3}  # audio over an image
  - {kind: asset, asset: cortinilla-salida, version: 1}
cuts:
  - input: grabacion
    start_ms: 41250
    end_ms: 43800
    reason: "repetición: vuelve a empezar la frase"
    text: "el activo, eh, el activo circulante"
    status: proposed        # proposed | accepted | rejected; a master refuses any `proposed`
blurs:                      # hide personal data without cutting (e-mails, codes, tokens)
  - input: grabacion
    start_ms: 230000        # source time, like cuts
    end_ms: 236000
    x: 1040                 # box in the input's own pixels (e.g. 1920x1080)
    y: 556
    w: 200
    h: 32
    reason: "correo personal en el selector de cuentas"
zooms:                      # punch-in: the box fills the frame (aspect kept); same fields as blurs
  - {input: grabacion, start_ms: 120000, end_ms: 128000, x: 960, y: 0, w: 960, h: 540, reason: "menú pequeño"}
overlays:                   # exactly one of text / asset per item
  - text: "Dra. Ana López\nProfesora de Contabilidad"     # lower third
    input: grabacion        # optional: times are then SOURCE time (follow cuts); without it, OUTPUT time
    start_ms: 5000
    end_ms: 11000           # omit = until the end
    position: bottom-left   # top-left|top|top-right|center|bottom-left|bottom|bottom-right
    size_pct: 4             # text: % of frame height · image: % of frame width
    color: white            # name or #RRGGBB, optional @alpha
    box_color: black@0.6    # null = no bar
    font: {id: fuente-marca, version: 1}   # optional registered font; default: system sans
  - {asset: logo-uabc, version: 1, position: top-right, size_pct: 10, opacity: 0.8}  # watermark, whole video
music:                      # registered music/sfx asset, OUTPUT time, looped if shorter
  - {asset: cama-suave, version: 1, start_ms: 0, volume_db: -20, duck: true, fade_ms: 1500}
  - {asset: whoosh, version: 1, start_ms: 2000, end_ms: 3000, volume_db: -6, duck: false, fade_ms: 0}  # sfx
fade_in_ms: 500             # from black/silence; 0 = none
fade_out_ms: 1000
```

Transitions go on the clip they lead **into** (never the first clip):
```yaml
  - {kind: source, input: grabacion, in_ms: 43800, out_ms: 600000, transition: {type: fade, ms: 500}}
```
Types: `fade` (cross-dissolve, the safe default), `fadeblack`, `fadewhite`, `dissolve`, `wipeleft|right|up|down`, `slideleft|right`, `smoothleft|right`, `circleopen|close`, `radial`, `zoomin`, `pixelize`. `ms` is 100–3000, a multiple of 100. The two clips **overlap** by `ms`, so the output gets that much shorter and every later position shifts earlier (`timeline review` shows real positions). Use transitions between sections or around cortinillas, not to hide each cut: a hard cut is the professional norm inside continuous speech.

## Production settings (series `defaults` / video `overrides`, not the timeline)
```yaml
style:
  background: {id: fondo-curso, version: 1}  # image asset behind source clips
  background_blur: false   # or: fill letterbox with a blurred copy of the clip (vertical/4:3 recordings)
  inset_pct: 8             # shrink source clips so the background frames them (0 = full frame)
audio:                     # all off by default
  highpass_hz: 80          # rumble/hum
  denoise_db: 12           # steady background noise (fan, AC); higher removes more but can sound watery
  compress: true           # even out loud/soft speech
  loudness_lufs: -16       # final mix: -16 web/YouTube/LMS, -23 broadcast; true_peak_db -1.5
  edge_fade_ms: 15         # micro fade at clip edges: no clicks at cuts
color: {brightness: 0.02, contrast: 1.05, saturation: 1.1, gamma: 1.0}  # source clips only
```
Settings are read at render time but approval binds to the timeline hash only: **change settings before the preview that gets approved**, never between approval and master.

Assets for these layers: `asset add FILE --kind image|logo|font|music|sfx ...` (license and permissions required, as for cortinillas).

Rules enforced by `timeline validate`:
- Every input belongs to this video's inventory, and its file still matches the ingested sha256.
- `out_ms` does not exceed the media duration. Images can only be used as `still`.
- Assets are registered with that exact version and an unchanged hash.
- Transcripts were made from the current version of their input.
- Each blur/zoom names a video input of this video, and its box fits inside that input's frame.
- Transitions are shorter than both clips they join; overlays, music and fades fit inside the output; their assets have the right kind and an unchanged hash. Colors only accept `name|#hex[@alpha]`.
- In master mode there are no `proposed` cuts, and an approval must match this file's exact sha256.

To adjust a cut boundary, edit `in_ms`/`out_ms` of the neighboring clips (and the cut entry) in a **new** timeline file. Never write FFmpeg commands.

Clip boundaries: at 30 fps a clip whose length is not a whole number of frames grows by up to 33 ms, and with many clips QA `duration` fails. Keep every source clip length a multiple of 100 ms.

Picking boundaries: use word `start_ms`/`end_ms` from the transcript, plus about 80–150 ms of margin. Cut between words, not inside them. Word times have ~100–300 ms of error, so check the preview.
