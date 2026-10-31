# PROMPT · Documento profesional de estructura y temática del curso

> Copia todo lo que está debajo de la línea y pégalo en el asistente de IA que redactará el documento.
> Datos tomados directamente de Google Classroom el 30/10/2026.

---

## 1. TU PAPEL Y LA TAREA

Actúa como diseñador instruccional y redactor técnico-académico. Redacta un **documento profesional, formal y en español** que reporte la **estructura y la temática** del curso descrito abajo. Debe servir para presentarlo ante una coordinación académica, colegas docentes o un comité de revisión: alguien que nunca ha entrado al Classroom tiene que entender, solo con este documento, qué se enseña, en qué orden, con qué materiales, cómo se evalúa y qué recursos hay.

Reglas obligatorias:
- Usa **solo** la información de este prompt. No inventes datos (horas, créditos, objetivos institucionales, plan de estudios, nombres). Si falta algo que normalmente llevaría un documento así, deja un marcador visible: **[POR CONFIRMAR: …]**.
- Respeta los **títulos exactos** de temas y publicaciones, y su numeración (0.1, 1.1 … 5.2).
- Cita todas las URL completas (Classroom, YouTube y fuentes oficiales).
- Redacta en tercera persona y con tono institucional. Explica los términos técnicos (CLI, terminal, Node.js, npm, manifiesto) la primera vez que aparezcan.
- Usa tablas cuando ayuden a comparar (mapa del curso, evaluación, videos y recursos).
- Al final, incluye un anexo de **observaciones de consistencia** (ver sección 9) y no las corrijas por tu cuenta en el cuerpo del documento.

---

## 2. DATOS GENERALES DEL CURSO

| Campo | Valor |
|---|---|
| Nombre del curso | Inteligencia Artificial: desde la academia hasta tu profesión |
| Sección (Classroom) | LIDE [POR CONFIRMAR: significado de la sigla] |
| Institución | Universidad Autónoma de Baja California (UABC) [POR CONFIRMAR: facultad o unidad académica] |
| Docente | Adrián Rodríguez Aguiñaga |
| Plataforma | Google Classroom |
| Enlace de la clase | https://classroom.google.com/c/NzYzNTU0MTE1ODc5 |
| Enlace a "Trabajo en clase" | https://classroom.google.com/w/NzYzNTU0MTE1ODc5/t/all |
| Código de la clase | [POR CONFIRMAR: tomar de Classroom solo para versiones de uso interno; no incluir en versiones públicas] |
| Estudiantes inscritos | 27 (al 30/10/2026) |
| Carreras del grupo | Contaduría, Negocios Internacionales, Administración e Inteligencia de Negocios |
| Nivel | Introductorio; no requiere saber programar |
| Duración sugerida | Unas 12 horas en total, ajustables al grupo |
| Inicio de publicación | 13 de octubre de 2026 |
| Periodo de entregas | 5 al 20 de noviembre de 2026 |
| Materiales en video | 10 videos en YouTube (≈79 min en total) |

**Propósito (tal como se le presenta al estudiante):** explorar cómo usar la inteligencia artificial para resolver necesidades reales de la profesión. Primero se ve un resultado terminado, luego se construye paso a paso y al final se demuestra que funciona.

---

## 3. ENFOQUE PEDAGÓGICO (generalidades)

- **Ciclo de cada tema:** explora → predice → construye → prueba → explica → mejora.
- **"Empieza por el resultado":** cada guía abre mostrando el producto final esperado antes de construirlo.
- **Orden de trabajo:** primero la guía (material) del tema y después el reto (tarea).
- **Trabajo en pareja** permitido si una cuenta o instalación limita el acceso. "Ruta de observación": quien no tenga acceso a una herramienta documenta la demostración del docente sin inventar evidencias.
- **Evidencia honesta por encima de la apariencia:** vale más una evidencia honesta del proceso que un resultado que se ve bien pero no se entiende. No se premia afirmar que algo funciona sin mostrar pruebas.
- **Bitácora** en cada práctica: fecha, necesidad, herramienta y versión, instrucción dada, resultado, prueba, corrección y aprendizaje (basta un documento de texto).
- **Acuerdos de práctica (seguridad y ética):** solo datos ficticios; una carpeta exclusiva para el laboratorio; conservar respaldo; leer lo que hará la herramienta antes de autorizarlo; no entregar claves, contraseñas ni documentos privados; no desactivar antivirus, firewall ni restricciones institucionales; no activar la aprobación automática total en los CLI.
- **Herramientas:** Manus (prototipo web sin instalar nada) y un asistente de IA de terminal (CLI) a elegir entre Gemini CLI/Antigravity CLI de Google, Codex CLI o Claude Code (basta con uno). Node.js LTS y npm como base. El acceso, las cuotas y los costos dependen de cada proveedor; ninguna práctica exige pagar servicios.
- **Progresión de competencias:** prototipo en el navegador (Manus) → entorno de terminal → construir un archivo local con IA → controlar archivos con permisos y respaldo → proyecto profesional integrador.
- **Recurso base:** `kit-curso-ia.zip` (adjunto a 0.1). Contiene `ejemplo-asistente.html` (página de ejemplo con cuatro casos, cinco preguntas y botón Reiniciar; funciona local, sin Node.js y sin enviar datos) y cuatro TXT ficticios para el tema de control local: `reunion-equipo.txt`, `propuesta-taller.txt`, `consulta-cliente.txt`, `plan-capacitacion.txt`.
- **Producto que se repite y evoluciona:** "Mi asistente de formación profesional", una página educativa con cuatro tarjetas (reunión, propuesta, cliente, capacitación), un cuestionario de cinco preguntas de opción múltiple con explicación, un marcador y el botón Reiniciar.

---

## 4. ORGANIZACIÓN EN CLASSROOM (orden real de los temas)

Los temas no llevan número; las publicaciones sí. Material = guía o lectura; Tarea = entrega calificada; Pregunta = respuesta breve.

| Orden | Tema en Classroom | Publicaciones |
|---|---|---|
| — | 🎬 Videoteca · Clases en video | Videoteca: todas las clases en video (material) |
| 0 | Introducción: explora el resultado | 0.1 (material), 0.2 (pregunta) |
| 1 | Manus IA: del ejemplo al prototipo | 1.1 (material), 1.2 (tarea) |
| 2 | Instalación: Node.js y herramientas CLI | 2.1 (material), 2.2 (material), 2.3 (tarea) |
| 3 | Crea con IA desde la terminal | 3.1 (material), 3.2 (tarea) |
| 4 | Control local: archivos, permisos y verificación | 4.1 (material), 4.2 (tarea) |
| 5 | Proyecto profesional y portafolio | 5.1 (material), 5.2 (tarea) |

Convención: cada publicación que tiene video lleva la línea "▶ VIDEO DE ESTA SESIÓN: <url>" al inicio y al final de la descripción y el video adjunto. 0.2, 4.2 y 5.2 no tienen video.

---

## 5. DETALLE DE CADA PUBLICACIÓN

### Videoteca: todas las clases en video
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/m/ODk2OTE1MTk2OTUx/details
Reúne los 10 videos en orden, agrupados por tema (ver tabla de la sección 6).

### TEMA · Introducción: explora el resultado

**0.1 · Empieza aquí: explora el ejemplo y conoce la ruta** (material · video 4 min · https://youtu.be/hXDPYzTpDEc)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/m/ODkxOTQzNjI2NDQ3/details · Adjuntos: kit-curso-ia.zip y el video "1. Introducción".
- Bienvenida y propósito; a quién va dirigido (las cuatro carreras; cada guía incluye al menos un ejemplo por carrera).
- "Empieza por el resultado" (15 min): descargar y extraer el kit, abrir `ejemplo-asistente.html` en Chrome/Edge, explorar los cuatro casos, contestar las cinco preguntas, probar Reiniciar y anotar tres cosas: ¿para qué profesión sería útil?, ¿qué cambiarías?, ¿cómo comprobarías que funciona?
- Ruta de aprendizaje: Introducción (conocer el resultado y formular la necesidad) → Manus IA (prototipo desde el navegador) → Instalación (Node.js y un asistente de IA) → Crea con IA desde la terminal (reconstruir con archivos propios) → Control local (organizar archivos, revisar permisos, verificar) → Proyecto profesional y portafolio (adaptar una solución y presentar evidencias).
- Incluye: cómo trabajaremos, bitácora, acuerdos de práctica y evaluación (ver secciones 3 y 7).

**0.2 · Diagnóstico: ¿qué tarea profesional mejorarías con IA?** (pregunta · sin calificación · fecha límite 5 nov)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/sa/ODkxOTgwNjU0NDM1/details
Responder: 1) profesión o área; 2) una tarea concreta que se quiere mejorar; 3) resultado esperado; 4) cómo se comprobaría que funciona; 5) experiencia con IA y terminal (ninguna/básica/frecuente). Casos ficticios; leer la respuesta de un compañero y aportarle una pregunta o una mejora. Se retoma al cierre (5.1) para comparar el antes y el después.

### TEMA · Manus IA: del ejemplo al prototipo

**1.1 · Demostración y guía: crea tu asistente con Manus** (material · video 15 min · https://youtu.be/0BGhDf4vNqQ)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/m/ODkxOTM5OTc4NDQ2/details
- Objetivo: convertir una necesidad profesional en un prototipo y evaluar si funciona; sin programar ni instalar.
- Demostración (10 min): el docente muestra "Mi asistente de formación profesional"; el estudiante predice qué hará cada botón.
- Construcción (35–45 min), 9 pasos: entrar a https://manus.im/; describir el problema (quién, qué aprende, cómo se comprueba); prompt base con requisitos (cuatro tarjetas con casos ficticios, cinco preguntas con retroalimentación, marcador, Reiniciar, accesible con teclado y móvil, sin datos personales ni servicios externos, plan antes de construir); leer el plan; probar la vista previa (respuesta correcta, incorrecta, terminar, Reiniciar); pedir una mejora concreta; volver a probar; exportar si la cuenta lo permite (se reconstruye localmente en 3.1); compartir solo evidencias sin datos privados.
- Comprobación: 4 casos y 5 preguntas; explicación útil ante el error; el marcador y Reiniciar funcionan; navegación con Tab; sin datos personales ni fuentes inventadas.
- Pausa reflexiva, solución de problemas y fuente oficial: https://manus.im/features/webapp (revisada el 13/10/2026).

**1.2 · Reto: adapta Manus a tu profesión y mejora el resultado** (tarea · 100 pts · fecha límite 10 nov · 45–60 min · video 3 min · https://youtu.be/Hk9955qvGIM)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/a/ODcwMTYzMDY2OTM5/details
- Ejemplos por carrera: Contaduría (tipos de comprobantes fiscales), Negocios Internacionales (incoterms o documentos de exportación), Administración (estilos de liderazgo), Inteligencia de Negocios (tipos de KPI).
- Pasos: problema, público y 3 criterios de éxito → prototipo en Manus → probar respuesta correcta, incorrecta y Reiniciar → pedir una corrección precisa y volver a probar → intercambiar con un compañero.
- Entrega: reporte con problema y público, prompt inicial, captura del antes y del después, tabla de 3 pruebas (acción/esperado/observado), mejora solicitada y reflexión sobre los límites de la IA. Ruta de observación si no hay acceso.
- Criterios: problema y criterios claros 20 · prototipo pertinente 30 · pruebas y corrección 30 · reflexión y respuesta a la retroalimentación 20.

### TEMA · Instalación: Node.js y herramientas CLI

**2.1 · Prepara la terminal: instala Node.js y comprueba npm** (material · video 6 min · https://youtu.be/ttOkz_RhJTc)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/m/ODcwMTY3NDQ3MzE2/details
- Objetivo: dejar la computadora lista: Node.js, comprobación y carpeta de práctica.
- Glosario: terminal, CLI, Node.js, npm (instalarlos no instala ninguna IA ni contrata cuentas).
- Paso a paso (20–30 min): instalar Node.js LTS desde https://nodejs.org/en/download (opciones por defecto, con PATH); abrir una terminal nueva (PowerShell en Windows, Terminal en macOS); `node --version` y `npm --version` (`npm.cmd` en Windows); `mkdir laboratorio-ia` y `cd laboratorio-ia`; confirmar la ubicación con `Get-Location` o `pwd`; anotar en la bitácora.
- Comprobación, solución de problemas y fuentes (nodejs.org y docs.npmjs.com, revisadas el 13/10/2026).

**2.2 · Instalación paso a paso: Antigravity CLI (google)** (material · video 15 min · https://youtu.be/vwCNuCimcnY)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/m/ODcwMTY3MzExNjYw/details
- Objetivo: instalar y abrir un asistente de IA en la terminal (basta uno; instalar no garantiza tener acceso al servicio).
- Distingue los comandos de terminal de los mensajes al asistente.
- Instalación en Windows: `irm https://antigravity.google/cli/install.ps1 | iex`; comprobar con `gemini --version`; iniciar con `gemini`; entrar con "Sign in with Google"; confiar solo en la carpeta del laboratorio. Las cuentas institucionales pueden requerir permisos. Alternativas: Codex CLI o Claude Code.
- Primer diálogo (5 min): pedir al asistente que explique qué puede leer, qué requiere permisos y que describa la carpeta sin cambiar nada; comparar con los permisos reales.
- Solución de problemas (comando no reconocido, `.cmd`, cuota, proxy o certificado). Fuentes: https://geminicli.com/docs/get-started/installation/ y https://geminicli.com/docs/get-started/authentication/

**2.3 · Punto de control: tu entorno y tu primer diálogo CLI** (tarea · 100 pts · fecha límite 12 nov · 30–45 min · video 4 min · https://youtu.be/MLjy0OEG3iY)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/a/ODcwMTY3MjkyMDI3/details
- Demostrar que se puede abrir un CLI en la carpeta de práctica; enviar el prompt sobre "directorio de trabajo" y la diferencia entre proponer y ejecutar un comando; registrar la respuesta y los permisos; salir con Ctrl+C.
- Entrega: sistema operativo, versiones (Node/npm/CLI), captura del CLI sin datos de la cuenta, ubicación de la carpeta, respuesta explicada con palabras propias, un problema y su solución.
- Criterios: instalación y versiones 30 · el CLI inicia y responde 30 · explicación de carpeta y permisos 25 · bitácora y manejo de errores 15.

### TEMA · Crea con IA desde la terminal

**3.1 · Del ejemplo al archivo: crea tu asistente desde el CLI** (material · video 6 min · https://youtu.be/1h3A6Q4ojcA)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/m/ODcwMTY3MzMzOTg5/details
- Objetivo: reconstruir con el CLI el ejemplo de 0.1 como un único `index.html` local (con su CSS y JS), sin dependencias ni servicios externos.
- 11 pasos: carpeta `mi-asistente`; iniciar el CLI; prompt de plan sin ejecutar; revisar rutas y permisos; crear el archivo; verificar con `Get-ChildItem` o `ls`; abrirlo con doble clic; probar; respaldar (`index-respaldo.html`); pedir una corrección concreta; recargar y volver a probar.
- Tabla de pruebas: sin selección, respuesta correcta, incorrecta, Siguiente, última pregunta, Reiniciar, además de teclado y ventana angosta.
- Solución de problemas (index.html.txt, recargar, pantalla vacía, el agente quiere instalar dependencias). Concepto: HTML/CSS/JavaScript. Referencias: https://learn.chatgpt.com/docs/codex/cli · https://code.claude.com/docs/en/setup · https://geminicli.com/docs/get-started/installation/

**3.2 · Reto: reconstruye, prueba y mejora tu página local** (tarea · 100 pts · fecha límite 14 nov · 60–90 min · video 9 min · https://youtu.be/aALReikDrRI)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/a/ODcwMTY3NDU1MTY4/details
- Cuatro tarjetas y cinco preguntas; dos casos adaptados a la carrera; seis pruebas; respaldo antes de modificar; un compañero lo prueba con Tab.
- Entrega: `index.html`, bitácora (CLI, versión y prompts), tabla de las seis pruebas, dos capturas del antes y el después, tres diferencias respecto del prototipo de Manus.
- Criterios: funciones y claridad didáctica 35 · casos adaptados 20 · pruebas, teclado y corrección 30 · explicación y bitácora 15. Ampliación opcional: comparar con otro CLI.

### TEMA · Control local: archivos, permisos y verificación

**4.1 · Del ejemplo al flujo: organiza archivos con permisos y respaldo** (material · video 9 min · https://youtu.be/3K4VqDPN3h8)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/m/ODcwMTY3NDA3ODU5/details
- Objetivo: clasificar con IA cuatro TXT de ejemplo en carpetas (reuniones, propuestas, clientes, capacitación) **copiando, no moviendo**, y generar `manifest.csv` (nombre original, destino, categoría, razón).
- Resultado esperado: `laboratorio-ia/entrada/` (originales intactos), `organizado/<categoría>/…` y `manifest.csv`.
- Aclara qué significa "controlar la máquina" en este curso: solo una carpeta local de texto, nunca ventanas ni el mouse.
- 11 pasos: inventario → plan sin cambios → revisar categorías por contenido → revisar permisos y comandos → copiar sin borrar ni sobrescribir → contar (4 y 4) y comparar el contenido → revisar el manifiesto → segunda pasada en modo revisión para detectar duplicados.
- Fuentes sobre permisos: https://code.claude.com/docs/en/permissions · https://geminicli.com/docs/cli/trusted-folders/ · https://learn.chatgpt.com/docs/windows/windows-sandbox

**4.2 · Reto: organiza archivos y demuestra que conservaste los originales** (tarea · 100 pts · fecha límite 17 nov · 45–60 min · sin video)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/a/ODcwMTY3NDM2NTIx/details
- Seis pasos: inventario, plan, autorizar la copia, comprobar (4 originales y 4 copias), contrastar el contenido y el manifiesto, segunda ejecución sin duplicados.
- Entrega: capturas del antes y el después, plan aprobado, `manifest.csv`, tabla original → copia → categoría → comprobación, y una reflexión (qué se autorizó, qué se rechazó, qué se haría con archivos reales).
- Criterios: plan y alcance 25 · clasificación y originales conservados 30 · verificación y duplicados 30 · explicación y bitácora 15.

### TEMA · Proyecto profesional y portafolio

**5.1 · Del resultado al proyecto: aplica IA en tu profesión** (material · video 8 min · https://youtu.be/WluEitpa_DU)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/m/ODkxOTgzNzU0NDI5/details
- Objetivo: integrar el prototipo, la construcción con CLI y la organización de archivos en una necesidad pequeña y real de la profesión.
- Ejemplo de entrega: "Capacitación para atención al cliente".
- Problemas sugeridos por carrera: Contaduría (comprobantes fiscales o registros ficticios, sin asesoría fiscal real); Negocios Internacionales (incoterms, trámites de exportación); Administración (reuniones, propuestas, liderazgo); Inteligencia de Negocios (KPI, lectura de un reporte ficticio).
- 10 pasos: enunciado "Ayudaré a [público] a [tarea] mediante [producto]. Lo comprobaré con [tres pruebas]" → criterios observables → prototipo en Manus → plan con CLI → construir por partes (estructura → interacción → contenido → pruebas) → organizar archivos como en 4.1 → pruebas, incluida una propia → retroalimentación de pares → empaquetar y probar la copia → presentar (resultado → necesidad → pasos → pruebas → limitaciones).
- Plantilla de informe de 10 campos; cierre comparando con el diagnóstico 0.2.

**5.2 · Proyecto final: demuestra una solución para tu profesión** (tarea · 100 pts · fecha límite 20 nov · 2–3 horas · sin video)
URL: https://classroom.google.com/c/NzYzNTU0MTE1ODc5/a/ODkxOTgwNjA1OTU1/details
- Requisitos: problema, público y 3 criterios; prototipo en Manus (o análisis de la demostración); versión local (4 casos, 5 preguntas, reinicio); organización de archivos con manifiesto; pruebas y al menos una mejora tras la retroalimentación de un compañero.
- Entrega: ZIP (`index.html` y los archivos ficticios) y un reporte (problema, proceso, herramientas y versiones, prompts, tabla de pruebas, capturas, manifiesto, limitaciones, recomendaciones). Sin claves, node_modules ni datos reales. Explicación oral de 2 minutos (en sesión o en un video opcional).
- Criterios: pertinencia profesional 20 · funcionamiento y claridad 25 · pruebas y corrección 25 · control de archivos, respaldo y manifiesto 15 · bitácora, explicación y límites 15.
- Revisión entre pares y autoevaluación final.

---

## 6. VIDEOTECA (YouTube)

| Publicación | Título del video en YouTube | Duración | Enlace |
|---|---|---|---|
| 0.1 | 1. Introducción | 4 min | https://youtu.be/hXDPYzTpDEc |
| 1.1 | 2. Sesión introductoria a Manus AI | 15 min | https://youtu.be/0BGhDf4vNqQ |
| 1.2 | Reto 1.2: adapta Manus a tu profesión | 3 min | https://youtu.be/Hk9955qvGIM |
| 2.1 | 2.1: Instala Node.js y abre la terminal | 6 min | https://youtu.be/ttOkz_RhJTc |
| 2.2 | 2.2: Instalación paso a paso: Agy CLI | 15 min | https://youtu.be/vwCNuCimcnY |
| 2.3 | 2.3: Punto de control: tu entorno y tu primer diálogo CLI | 4 min | https://youtu.be/MLjy0OEG3iY |
| 3.1 | 3.1: Del ejemplo al archivo: crea tu asistente desde el CLI | 6 min | https://youtu.be/1h3A6Q4ojcA |
| 3.2 | 3.2: Reto: reconstruye, prueba y mejora tu página local | 9 min | https://youtu.be/aALReikDrRI |
| 4.1 | 4.1: Del ejemplo al flujo: organiza archivos con permisos y respaldo | 9 min | https://youtu.be/3K4VqDPN3h8 |
| 5.1 | 5.1: Del resultado al proyecto: aplica IA en tu profesión | 8 min | https://youtu.be/WluEitpa_DU |

---

## 7. EVALUACIÓN

| Actividad | Tipo | Puntos | Fecha límite |
|---|---|---|---|
| 0.2 Diagnóstico | Pregunta | Sin calificación | 5 nov 2026 |
| 1.2 Reto Manus | Tarea | 100 | 10 nov 2026 |
| 2.3 Punto de control | Tarea | 100 | 12 nov 2026 |
| 3.2 Reto página local | Tarea | 100 | 14 nov 2026 |
| 4.2 Reto archivos | Tarea | 100 | 17 nov 2026 |
| 5.2 Proyecto final | Tarea | 100 | 20 nov 2026 |

Incluye los criterios desglosados de la sección 5. Ponderación entre tareas para la calificación final: [POR CONFIRMAR]. El docente puede ajustar tiempos y ponderaciones. Cada criterio se valora por evidencia observable.

---

## 8. ESTRUCTURA QUE DEBE TENER EL DOCUMENTO

1. Portada: nombre del curso, sección, institución, docente, fecha (30 de octubre de 2026) y la leyenda "Documento de estructura y temática del curso".
2. Resumen ejecutivo (media página).
3. Datos generales (tabla de la sección 2).
4. Propósito y perfil de los participantes.
5. Enfoque pedagógico y principios de trabajo (sección 3).
6. Mapa del curso: tabla de temas, publicaciones, tipo, duración estimada y video.
7. Desarrollo temático: un apartado por tema con su objetivo, contenidos, actividades, productos, criterios y recursos (sección 5). Agrega en cada tema una línea de **"Aprendizaje esperado"** redactada a partir de los objetivos y criterios ya dados, sin agregar contenido nuevo.
8. Progresión y relación entre temas: cómo el ejemplo de 0.1 se convierte en prototipo (1), luego en archivo local (3), luego se suma el control de archivos (4) y todo se integra en el proyecto (5). Incluye un diagrama de flujo simple en texto o en tabla.
9. Sistema de evaluación (sección 7).
10. Herramientas, requisitos técnicos y recursos (kit, software, fuentes oficiales).
11. Lineamientos de seguridad, ética y uso responsable de la IA.
12. Calendario de entregas.
13. Anexo A: Videoteca (sección 6).
14. Anexo B: Enlaces de Classroom de cada publicación.
15. Anexo C: Observaciones de consistencia (sección 9) y lista de todos los [POR CONFIRMAR].

Formato: títulos numerados, tablas con encabezado y una extensión aproximada de 8 a 14 páginas. Debe poder exportarse a Word o PDF.

---

## 9. OBSERVACIONES DE CONSISTENCIA DETECTADAS (inclúyelas en el Anexo C, sin resolverlas)

1. La guía 0.1 dice que los retos "no tienen fecha límite fija", pero en Classroom todas las tareas tienen fecha límite (5–20 nov).
2. La publicación 2.2 se titula "Antigravity CLI (google)" y el video "Agy CLI", pero el cuerpo dice "INSTALA GEMINI CLI" y usa el comando `gemini`, aunque el instalador es de antigravity.google. Hay que unificar el nombre de la herramienta.
3. Las entregas de 2.3, 4.2 y 5.2 piden "un reporte breve (no tan breve)"; conviene definir una extensión esperada.
4. Algunos títulos de video en YouTube no coinciden con el título de su publicación (por ejemplo, 1.1 "Sesión introductoria a Manus AI" y 2.2 "Agy CLI").
5. Las fuentes oficiales se revisaron el 13/10/2026; las instrucciones de instalación de terceros pueden cambiar.
