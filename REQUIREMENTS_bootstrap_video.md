# REQUIREMENTS — Bootstrap de plataforma audiovisual reutilizable

Versión: 2.0 · Fecha: 2026-10-27
Estado: contrato de construcción para Claude Code y Codex; no instalación ejecutada.

## 0. Misión del agente

No te limites a explicar cómo editar videos ni a crear carpetas vacías. Construye, instala dentro del alcance autorizado, configura y verifica una base reutilizable de producción audiovisual multivideo. Al terminar, el usuario debe poder crear una serie, incorporar una introducción y clases, registrar sus cortinillas y ejecutar un primer recorrido de edición sin reconstruir el entorno.

Este archivo es un contrato de bootstrap y aceptación. No es un requirements.txt ni instala nada por sí mismo. El agente debe producir los manifiestos de dependencias, lockfiles, código, documentación, pruebas y adaptadores necesarios.

El workspace incluye tres productos distintos:
1. Un motor de edición y sus contratos de datos.
2. Una estructura de producción para series y videos.
3. Una capacidad reutilizable para agentes, empaquetable como skill una vez validada.

Aplica estas instrucciones al repositorio real. No declares completadas instalaciones, pruebas o compatibilidad que no hayas observado. Mantén pendientes y limitaciones explícitas.

DEBE: obligación. DEBERÍA: excepción justificada. PUEDE: opción. Pendiente no equivale a aprobado.

## 1. Resultado esperado: una fundación utilizable

### Preparado no significa una carpeta con instrucciones

La base solo estará preparada cuando:
- El entorno se pueda reconstruir mediante un procedimiento probado.
- Las dependencias elegidas estén instaladas y sus versiones registradas.
- Los contratos y operaciones esenciales tengan implementación funcional.
- Un smoke test con medios sintéticos recorra el motor sin depender de datos privados.
- Una prueba autorizada con audio español confirme la transcripción real.
- Se haya demostrado aislamiento entre introducción, clase 1 y clase 2.
- Los adaptadores del agente indiquen cómo invocar las operaciones existentes.
- El usuario reciba un reporte de verificación y el siguiente paso exacto.

No aceptar mocks como prueba de integración. Pueden usarse en pruebas unitarias si están identificados.

## 2. Continuidad con el flujo de ingeniería del usuario

Si está disponible, leer selectivamente `REQUIREMENTS_v3_investigacion_comparativa_agentes.md` como política de ingeniería. Mantener GSD/Ponytail/Grill/Graphify como baseline por identificar, no como paquetes que deban reinstalarse.

- Un solo dueño del plan complejo y una fuente canónica de estado.
- No instalar otra metodología integral para construir este proyecto.
- Diagnóstico antes de cambios y caracterización si el repositorio ya existe.
- Bootstrap idempotente y pruebas verificables.
- Scripts para tareas deterministas; agentes para interpretación y decisiones.
- Instrucciones cortas con referencias, no este contrato entero en cada subagente.
- No modificar configuraciones globales de Claude/Codex por defecto.

Esta plataforma es una capacidad de dominio, no otro router ni un sistema multiagente permanente.

## 3. Política de autorización y autonomía

### Fase inicial de solo lectura

Inspeccionar workspace, Git, SO, shell, CPU, RAM, almacenamiento, GPU y herramientas. Advertir si alguna lectura puede ejecutar código del repositorio. No instalar ni reorganizar en esta fase.

### Propuesta de bootstrap

Presentar un plan con:
- Rutas que se crearán o modificarán.
- Comandos o procedimientos de instalación, fuentes y versiones resueltas.
- Dependencias del sistema frente a dependencias aisladas del proyecto.
- Descargas de modelos, tamaño conocido o desconocido y destinos de caché.
- Permisos, proveedores, posibles costes y egreso de datos.
- Pruebas, alcance de aprobación y reversión.

Solicitar aprobación del plan. Después, ejecutar las fases aprobadas sin convertir cada paso rutinario ya autorizado en otra entrevista, salvo que la herramienta o política del entorno exija confirmación adicional.

Nueva aprobación obligatoria ante cambios de alcance, permisos de administrador, configuración global, proveedor externo, gasto, publicación, borrados o cambios destructivos. Nunca eludir los controles de aprobación del harness.

No usar una aprobación de instalación para autorizar decisiones editoriales ni subidas de medios.

## 4. Diagnóstico y selección técnica

Crear `docs/environment-report.md` con:
- Plataforma real y shell; en Windows comprobar PowerShell, PATH y comportamiento de rutas.
- Estado Git y cambios previos del usuario.
- Herramientas presentes y versiones efectivas.
- Disponibilidad de FFmpeg, ffprobe y codecs necesarios.
- Python, gestores disponibles y estrategia de entorno aislado.
- GPU y compatibilidad real de la pila; no asumir CUDA por tener GPU.
- CLI de Claude/Codex disponibles, skills y metodología sin exponer secretos.
- Restricciones de espacio, privacidad y red.
- Decisiones pendientes y bloqueos.

Consultar documentación oficial vigente antes de fijar comandos o compatibilidad. Registrar URLs, fecha, versiones y licencias. No ejecutar instaladores remotos sin inspección ni fijar versiones inventadas.

## 5. Dependencias: selección y preparación

### Núcleo obligatorio

- Python: versión compatible con la pila seleccionada, en entorno aislado.
- FFmpeg y ffprobe: procesamiento e inspección audiovisual.
- Biblioteca de schemas/validación y lectura de configuración.
- Framework de pruebas y controles básicos de calidad proporcionados al proyecto.
- Paquete propio del pipeline, instalable en modo desarrollo cuando corresponda.

### Transcripción obligatoria en la base

Implementar una interfaz de backend y configurar un backend real de transcripción local. Primer candidato: faster-whisper. La selección queda sujeta al diagnóstico, compatibilidad y prueba en español.

Preparar configuración de idioma, modelo, dispositivo, tipo de cómputo y caché. Separar instalación del paquete y descarga de pesos. Descargar y probar al menos un modelo apropiado tras aprobar tamaño/licencia; no declarar ASR listo si faltan pesos o falla la inferencia.

No usar un modelo exclusivo de inglés para las clases en español. No prometer precisión por palabra solo porque el backend devuelve tiempos.

### Alineación opcional justificada

Evaluar WhisperX si la prueba necesita mejor alineación o varios hablantes. No instalarlo junto al backend por simple acumulación. Si se adopta, resolver compatibilidades y modelos de alineación por idioma. La diarización es opcional y requiere revisar modelos, términos, credenciales y descargas específicas.

Diseñar el contrato para soportar alineación sin obligar a instalarla desde el primer día. Una capacidad no instalada debe aparecer como `not_configured`, nunca como lista.

### Gráficos opcionales

Usar inicialmente títulos y cortinillas con el motor más simple que satisfaga el piloto. Incorporar Remotion, HyperFrames u otro motor solo tras comparar necesidad, dependencias y licencia. Node.js no es obligatorio si no se selecciona una tecnología que lo requiera.

### Reproducibilidad

- Declarar dependencias directas y rangos/intenciones en el manifiesto apropiado.
- Generar lockfile con la herramienta escogida; no escribir uno ficticio a mano.
- Registrar binarios externos, ubicación, versión y capacidades por separado.
- Registrar modelos con identificador, revisión resoluble, caché y licencia; no incluir pesos en Git.
- Probar instalación desde entorno limpio cuando sea viable; si no, indicarlo como no verificado.
- No generar requirements.txt y otro lock independiente como dos fuentes contradictorias. Exportarlo solo si hay necesidad de compatibilidad.

## 6. Arquitectura reutilizable

Separar:
1. Dominio: identidades, timelines, políticas editoriales y aprobaciones.
2. Aplicación: ingesta, transcripción, propuesta, render, QA y recuperación.
3. Infraestructura: procesos FFmpeg, backend ASR, filesystem y persistencia.
4. Interfaces: CLI, editor local y adaptadores de agentes.

La lógica crítica debe vivir en el paquete, no exclusivamente en prompts ni en wrappers de skills.

Interfaces mínimas:
- MediaProbe: inspección normalizada de fuentes.
- Transcriber: transcripción estructurada y metadatos del backend.
- Aligner: capacidad opcional con estado explícito.
- TimelineValidator: invariantes antes de renderizar.
- Renderer: plan de ejecución y artefactos trazables.
- QualityChecker: verificaciones técnicas sin inventar aceptación editorial.

Evitar abstracciones vacías y plugins anticipados. Implementar estas fronteras con el mínimo de código necesario para el primer recorrido funcional.

## 7. Estructura objetivo

```text
video-workspace/
├── REQUIREMENTS_bootstrap_video.md
├── README.md
├── CLAUDE.md
├── AGENTS.md
├── pyproject.toml
├── <lockfile-real>
├── .gitignore
├── .env.example
├── config/
│   ├── workspace.yaml
│   ├── toolchain.lock.yaml
│   ├── models.yaml
│   ├── profiles/
│   └── schemas/
├── src/video_pipeline/
├── scripts/                       # Bootstrap/wrappers, no motor duplicado
├── tests/{unit,integration,fixtures}/
├── evals/                         # Fuera de skills activas
├── docs/
│   ├── environment-report.md
│   ├── setup.md
│   ├── workflow.md
│   ├── recovery.md
│   ├── verification-report.md
│   ├── sources.md
│   └── decisions/
├── assets/
│   ├── registry.yaml
│   ├── cortinillas/{entrada,salida,transiciones}/
│   ├── logos/
│   ├── tipografias/
│   ├── musica/
│   ├── efectos-sonoros/
│   └── templates/
├── catalog/
│   ├── series.yaml
│   └── views/                     # Generadas, no editables
├── series/<serie-id>/
│   ├── series.yaml
│   ├── brief.md
│   ├── glossary.yaml
│   ├── assets/
│   └── videos/<video-id>/
│       ├── video.yaml
│       ├── brief.md
│       ├── inputs/{originals,audio,slides,images,broll,scripts}/
│       ├── manifests/
│       ├── editorial/
│       │   ├── transcript/
│       │   ├── decisions/
│       │   └── timelines/
│       ├── approvals/
│       └── runs/<run-id>/
│           ├── run.yaml
│           ├── resolved-config.yaml
│           ├── logs/
│           ├── reports/
│           ├── review/
│           ├── work/
│           └── outputs/{previews,masters,delivery,subtitles,thumbnails}/
├── agent-capabilities/video-series-editor/
│   ├── SKILL.md
│   └── references/
└── .local/                        # Cachés/locks, no secretos versionados
```

Las llaves expresan carpetas hermanas; no crear literalmente nombres con llaves. Crear solo lo necesario, conservando la plantilla para nuevos videos.

## 8. Organización e invariantes

- Series independientes: `curso-contabilidad`, por ejemplo.
- Videos: `introduccion`, `clase-001`, `clase-002`; títulos visibles independientes de IDs.
- Orden canónico en `series.yaml`, no exclusivamente en el nombre del directorio.
- Peticiones por nombre natural deben resolverse a `serie-id/video-id`; ante ambigüedad, preguntar.
- Configuración: global < serie < video < override de ejecución aprobado.
- Cada ejecución guarda configuración resuelta, hashes, comandos y resultados.
- Un run nuevo nunca sobrescribe outputs anteriores.
- Originales inmutables; copiar por defecto, verificar hash y nunca procesar in-place.
- Recursos compartidos con ID/versión/hash; cambiar una cortinilla no altera runs históricos.
- Configuración de serie ordena videos; configuración de video define sus excepciones; run registra una ejecución. No duplicar fuentes editables de estado.
- Un escritor por video y locks para operaciones concurrentes.
- Evitar shell interpolation; validar rutas, symlinks y traversal.

## 9. Contratos de datos que se deben implementar

Crear schemas versionados, ejemplos válidos y pruebas de rechazo para:
- Workspace: política, rutas y perfiles.
- Serie: identidad, videos ordenados, estilo y assets compartidos.
- Video: inputs, overrides, privacidad y requisitos editoriales.
- Inventario de inputs: hash, tamaño, nombre original y metadatos.
- Registro de assets: versión, licencia, permisos y propiedades técnicas.
- Transcripción: texto, segmentos/palabras, tiempos, idioma, backend y limitaciones.
- Timeline: fuentes, intervalos, posición de salida, pistas, assets, subtítulos y audio.
- Aprobaciones: objeto/revisión/hash aprobado, alcance, actor y fecha.
- Run: estado, configuración, herramientas, artefactos, QA y siguiente acción.

Definir unidades temporales explícitas e intervalos semiabiertos o contrato equivalente. Validar límites de medios, duraciones y referencias antes de ejecutar FFmpeg. Recalcular subtítulos al tiempo de salida tras cortes, transiciones y cortinillas.

Separar transcripción automática intacta, texto revisado y alineación. No editar destructivamente el resultado original del ASR.

## 10. Operaciones funcionales mínimas

Implementar una CLI estable. Elegir un nombre y documentar solo los comandos que existan. La siguiente es la interfaz deseada, no software ya disponible:

```text
video-pipeline doctor
video-pipeline bootstrap-check
video-pipeline series create ...
video-pipeline video create ...
video-pipeline ingest ...
video-pipeline inspect ...
video-pipeline transcribe ...
video-pipeline timeline validate ...
video-pipeline preview ...
video-pipeline render ...
video-pipeline qa ...
video-pipeline status ...
```

La propuesta editorial puede prepararla Claude/Codex como timeline estructurada; no necesita una segunda llamada API embebida ni credenciales adicionales. La CLI debe validar esa timeline independientemente del agente que la haya escrito.

`doctor` debe distinguir instalado, detectable, configurado y probado. `bootstrap-check` debe ser de lectura por defecto y no reinstalar por calendario.

Cada comando debe devolver códigos de salida fiables y errores accionables. Registrar stderr relevante, no ocultar fallos con un resumen optimista.

## 11. Primer recorrido real

1. Crear una serie de prueba y tres videos: introducción, clase 1 y clase 2.
2. Generar fixtures sintéticos pequeños de imagen/audio para probar estructura y render sin material privado.
3. Incorporar una muestra de voz española autorizada; no descargar material con licencia incierta para rellenar la prueba.
4. Inspeccionar y transcribir con el backend instalado y modelo descargado.
5. Preparar una timeline con cortes revisables; no convertir silencios detectados en cortes aprobados.
6. Añadir una cortinilla autorizada o una sintética identificada como fixture.
7. Renderizar preview y subtítulos con tiempos remapeados.
8. Revisar y aprobar el artefacto/revisión concreta.
9. Exportar entrega y ejecutar QA técnico.
10. Retomar en sesión nueva y demostrar que se recupera el estado sin repetir el bootstrap.

Si no hay voz autorizada, completar el recorrido sintético y marcar transcripción real como bloqueada. No afirmar preparación completa de ASR con un audio vacío o un mock.

## 12. Revisión editorial e interfaz local

La base debe permitir revisar una lista legible de cortes con fuente, inicio, fin, motivo y texto conservado. Añadir preview reproducible y un mecanismo para corregir límites sin editar comandos FFmpeg.

Un editor local en navegador es una mejora objetivo, no un motivo para bloquear todo el bootstrap. Puede implementarse en fase posterior si el recorrido CLI está validado. Si se construye, usar binding local por defecto, evitar exposición pública y registrar qué revisión guarda.

Política inicial conservadora: proponer errores y repeticiones; preservar negaciones, cifras, pasos y pausas pedagógicas. Detectar voz no equivale a decidir el ritmo de una clase.

No añadir publicación a redes ni edición automática irreversible.

## 13. Adaptadores para Claude Code y Codex

- Crear `CLAUDE.md` y `AGENTS.md` breves con propósito, comandos reales, límites, pruebas y referencias.
- No asumir idénticas reglas de descubrimiento ni rutas de skills en ambas herramientas.
- Consultar la versión instalada y la documentación vigente para preparar instalación local al proyecto cuando sea compatible.
- Mantener una fuente canónica de capacidad en `agent-capabilities/video-series-editor/`.
- Preferir adaptadores generados o enlaces compatibles; si hay copias, automatizar comprobación de sincronía.
- No instalar globalmente ni sobrescribir skills del usuario sin aprobación.
- Verificar descubrimiento/invocación por herramienta realmente disponible. Si Codex o Claude no está instalado, marcar su validación pendiente, no simularla.

El SKILL.md debe indicar cuándo activar, cómo resolver serie/video, qué referencia cargar, operaciones existentes y límites de aprobación. No incluir medios privados ni toda la especificación. El motor vive en el paquete; la skill lo usa.

## 14. Bootstrap reproducible e idempotente

Implementar un procedimiento documentado y verificable, con script si aporta valor:
1. Comprobar plataforma y prerrequisitos.
2. Detectar instalación existente sin modificarla.
3. Mostrar acciones pendientes.
4. Instalar dependencias aprobadas en el ámbito acordado.
5. Descargar modelos aprobados y comprobar disponibilidad.
6. Crear configuración inicial solo si no existe.
7. Validar schemas y perfiles.
8. Instalar el paquete del proyecto.
9. Ejecutar pruebas y smoke test.
10. Guardar reporte saneado y siguiente paso.

Repetirlo no debe sobrescribir configuración, duplicar videos o reinstalar innecesariamente. Actualizar una dependencia es una acción distinta de comprobar que existe.

No exigir soporte de todos los sistemas operativos desde el principio. Probar el del usuario, documentar los demás como no verificados y mantener el núcleo portable cuando sea viable.

## 15. Pruebas obligatorias

### Unitarias

Schemas, precedencia, identidades, temporalidad, remapeo de subtítulos, rutas seguras, hashes, cambios de estado y detección de configuración pendiente.

### Integración

- FFmpeg/ffprobe reales con fixture decodificable.
- Transcripción real en español con modelo instalado.
- Ingesta sin modificar originales.
- Cortes, cortinilla y subtítulos con duración esperada y tolerancia justificada.
- Salidas aisladas para introducción y dos clases.
- Nuevo run sin sobrescritura.
- Fallos por fuente corrupta, backend ausente y timeline inválida.
- Repetición del bootstrap sin daño.
- Interrupción y recuperación con locks.

### Calidad y evaluación

Ejecutar controles proporcionados de estilo/tipos y pruebas. Demostrar que QA detecta al menos un fallo seguro deliberado. Separar decodificación y calidad técnica de aceptación humana.

Comparar un pequeño conjunto de tareas con y sin skill cuando el flujo ya funcione. No evaluar solo activación ni prometer ahorro sin medición. No incorporar un framework de evaluación caro por anticipación.

## 16. Privacidad, backups y limpieza

Procesamiento local por defecto. Una descarga de modelo no autoriza enviar videos a un proveedor. Si se requiere red, describir destinos y datos transmitidos.

Ignorar por defecto secretos, cachés, pesos, originales, transcripciones privadas y renders grandes en Git. Definir qué manifiestos pueden revelar rutas o información sensible.

Git no sustituye respaldo de medios. Proponer política de backup y comprobar restauración cuando se implemente. No decir que existe backup porque hay un commit.

No borrar originales ni outputs aceptados. Limpieza de temporales exige retención definida y alcance aprobado. No usar reset destructivo ni clean para organizar.

Registrar licencias de software, modelos, música, fuentes y cortinillas. Un recurso público no equivale a permiso comercial universal.

## 17. Fases y entregables

### G0 — Diagnóstico y aprobación
Inventario, fuentes, decisiones, comandos previstos, permisos y reversión.

### G1 — Entorno instalado y fijado
Manifiesto y lock reales, binarios verificados, modelo disponible, configuración y reporte de instalación. Si hay bloqueos, no marcar completo.

### G2 — Motor mínimo funcional
Contratos, CLI, ingesta, inspección, transcripción, timeline, preview, exportación y QA con pruebas.

### G3 — Producción multivideo
Introducción y dos clases aisladas, herencia de estilo, cortinillas versionadas, recuperación y bootstrap repetido.

### G4 — Capacidad de agentes
Índices cortos, skill canónica, adaptadores comprobados en herramientas disponibles y evaluación inicial.

### G5 — Handoff
README, setup, workflow, recovery y verification-report. Lista de lo instalado, ejecutado, aprobado, bloqueado y deliberadamente excluido.

Completar cada fase con evidencia. No dejar la implementación en «el usuario podría instalar…» si la instalación está aprobada y el entorno permite realizarla. Si no permite, explicar el bloqueo concreto y preparar el procedimiento pendiente sin fingir ejecución.

## 18. Definición de terminado

- [ ] El diagnóstico corresponde al equipo/repositorio real.
- [ ] Las instalaciones se realizaron dentro del alcance aprobado.
- [ ] Hay dependencias fijadas y procedimiento de reconstrucción.
- [ ] FFmpeg/ffprobe se ejecutaron y generaron/verificaron medios.
- [ ] Backend ASR y modelo se ejecutaron con voz española autorizada.
- [ ] Los comandos documentados existen y sus errores son fiables.
- [ ] Schemas y timeline se validan antes de renderizar.
- [ ] Introducción, clase 1 y clase 2 no mezclan inputs ni outputs.
- [ ] Las cortinillas tienen identidad, versión y trazabilidad.
- [ ] Los originales conservaron sus hashes.
- [ ] Cortes y subtítulos usan tiempos correctos de salida.
- [ ] Un segundo bootstrap no destruye ni duplica contenido.
- [ ] QA detecta fallos y distingue aceptación humana.
- [ ] Los adaptadores se verificaron solo donde las herramientas están disponibles.
- [ ] No hay secretos, subidas, gastos o borrados implícitos.
- [ ] El reporte identifica claramente pendientes y limitaciones.

## 19. Prompt de arranque

```text
Construye la base reutilizable definida en REQUIREMENTS_bootstrap_video.md.
No quiero únicamente una explicación, un árbol de carpetas o un plan futuro:
quiero un bootstrap ejecutable, dependencias instaladas en el ámbito aprobado,
contratos de datos, un motor mínimo funcional, pruebas y adaptadores de agentes.

Primero inspecciona sin modificar. Integra mi metodología existente sin añadir
un segundo dueño del plan. Consulta fuentes oficiales y presenta las decisiones,
comandos, descargas, permisos, costes conocidos y reversión. Solicita aprobación.

Tras aprobarse el alcance, ejecuta por fases hasta dejar un recorrido verificado:
crear serie/video, ingerir, inspeccionar, transcribir español, validar timeline,
generar preview, aplicar cortinilla, remapear subtítulos, renderizar y verificar.

Usa entornos aislados y lockfiles reales. Comprueba las versiones disponibles;
no inventes compatibilidad ni instales todas las opciones a la vez. Whisper /
faster-whisper debe quedar concretado en un backend local probado. WhisperX y
un motor de gráficos se incorporan solo si se justifican.

Organiza introducción, clase 1 y clase 2 sin mezclar medios. Prepara una skill
canónica y adaptadores para Claude/Codex según su soporte real. No publiques,
subas material, uses administrador o borres archivos sin aprobación específica.

Entrega evidencia de lo ejecutado, comandos de uso reales, pendientes y siguiente
paso. Si el entorno bloquea algo, indícalo; no lo declares instalado o listo.
```

## 20. Fuentes iniciales a revalidar durante G0

Estos enlaces son puntos de consulta, no instalaciones autorizadas ni certificación de compatibilidad:
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- WhisperX: https://github.com/m-bain/whisperX
- Whisper: https://github.com/openai/whisper
- FFmpeg: https://ffmpeg.org/documentation.html
- Referencia de edición por transcripción: https://github.com/watzing/claude-video-editor

Consultar además documentación oficial vigente de Claude Code y Codex para el formato y descubrimiento de skills. Registrar en `docs/sources.md` únicamente las fuentes efectivamente revisadas al implementar.

Este contrato sustituye el enfoque meramente descriptivo por un encargo verificable de cimentación. No prueba por sí mismo que la plataforma ya esté construida.
