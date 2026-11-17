# Plan de PySpark Labs

Sitio web para estudiar y practicar PySpark, basado en el curso
"PySpark Tutorial | Full Course (From Zero to Pro!)" de Ansh Lamba, pensado para
usarlo con los compañeros del bootcamp.

Este plan está escrito **antes** de construir nada. Si algo no te convence,
se cambia aquí primero.

## Documentos

| Documento                                  | Qué responde                                                                                |
| ------------------------------------------ | ------------------------------------------------------------------------------------------- |
| [01-architecture.md](01-architecture.md)   | Cómo está hecho el sitio: stack, carpetas, formato del contenido, `storage.js`, componentes |
| [02-curriculum.md](02-curriculum.md)       | Qué se estudia: los 15 módulos, en qué orden y qué trae cada uno                            |
| [03-labs.md](03-labs.md)                   | Cómo funcionan los laboratorios de Colab, los tests y los datasets                          |
| [04-source-review.md](04-source-review.md) | Errores y dudas encontrados en las notas de Gemini y cómo se tratan                         |
| [05-roadmap.md](05-roadmap.md)             | Fases, commits, criterios de "terminado", riesgos y despliegue                              |

## Resumen en un minuto

- **15 módulos** en 5 bloques: 13 salen del video y 2 son extra ("Rendimiento por
  dentro" y "Proyecto integrador"). El orden está pensado para estudiar, no para
  seguir el video minuto a minuto; cada módulo enlaza a sus timestamps.
- **Cada módulo** tiene teoría corta con diagramas, ejercicios en el navegador
  (quiz, predecir salida, completar código) y un laboratorio en Google Colab con
  tests automáticos y solución aparte.
- **Sin backend.** El progreso vive en `localStorage`, centralizado en
  `src/services/storage.js`, con exportar/importar en JSON.
- **PySpark no corre en el navegador.** Todo el código real se ejecuta en Colab.
  Los ejercicios del sitio comparan respuestas, no ejecutan Spark.
- **Cada lab se verifica ejecutándolo de verdad** en local antes de darlo por bueno.

## Decisiones ya tomadas

| Tema                   | Decisión                                                                       | Origen                                       |
| ---------------------- | ------------------------------------------------------------------------------ | -------------------------------------------- |
| Idiomas                | Código y comentarios de código en inglés; contenido del sitio en español       | Encargo inicial                              |
| Stack                  | Vite + HTML/CSS/JS vanilla, ESLint, Prettier, despliegue en Vercel             | Encargo inicial                              |
| `material/`            | Solo fuente; va en `.gitignore`, no se publica                                 | Encargo inicial                              |
| Orden de módulos       | El que resulte más cómodo para estudiar                                        | Tu respuesta del 2026-11-16                  |
| Extras fuera del video | Sí, los que hagan falta para llegar a nivel pro, siempre marcados como "extra" | Tu respuesta del 2026-11-16                  |
| `drivers.json`         | Descargado de la API Jolpica-F1 (sucesora de Ergast)                           | Tu respuesta del 2026-11-16                  |
| Contenido              | Markdown para la teoría + JSON para ejercicios, una carpeta por módulo         | Propuesta mía, ver [01](01-architecture.md)  |
| Imports en el código   | `from pyspark.sql import functions as F` en lugar de `import *`                | Propuesta mía, ver [04](04-source-review.md) |

## Estado actual

Actualizado el 2026-11-16, al terminar la fase 2.

| Fase | Entrega                            | Estado                         |
| ---- | ---------------------------------- | ------------------------------ |
| 1    | Revisión del material y este plan  | Hecha                          |
| 2    | Base del sitio + módulo 1 completo | Hecha, en tu revisión          |
| 3    | Módulos 2 a 15                     | En curso: módulos 2 a 5 hechos |
| 4    | Publicación en GitHub y Vercel     | Pendiente                      |

## Cambios durante la construcción

Lo que se hizo distinto de lo escrito en estos documentos, y por qué:

| Plan                                                   | Lo construido                                                                | Motivo                                                                                    |
| ------------------------------------------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Repo y URL del sitio en `src/config.js`                | Viven en `site.config.json`; `src/config.js` y los scripts de Python lo leen | Una sola fuente para el sitio y para los notebooks                                        |
| Los notebooks descargan datos solo del sitio en Vercel | Prueban primero el sitio y, si no responde, el repositorio de GitHub         | Los labs funcionan en Colab en cuanto el repo está en GitHub, antes de publicar en Vercel |
| La explicación se muestra acierte o no                 | Se muestra al acertar; tras dos fallos se puede pedir la respuesta           | Enseñarla al primer fallo regalaba la solución                                            |
| `set-data-url.py` reescribe todos los notebooks        | Cambia `siteUrl` en `site.config.json` y regenera los notebooks              | Consecuencia del primer cambio                                                            |
| Usuario y repo de GitHub pendientes                    | Tomados del remoto que ya tenía el repositorio: `crapdev/sparkLab`           | Estaba configurado en git                                                                 |

## Lo que necesito de ti

1. **Visto bueno a este plan**, o los cambios que quieras.
2. **Usuario y nombre del repositorio de GitHub**, cuando los tengas. No bloquea
   nada ahora; el motivo está explicado en [03-labs.md](03-labs.md#por-qué-hace-falta-el-repositorio-de-github).
3. **Opcional pero muy útil:** el índice dice que el notebook oficial del curso
   está enlazado en la descripción del video. Si lo descargas y lo dejas en
   `material/`, puedo validar el código contra el original en vez de reconstruirlo.
4. **Opcional:** la v1 de la Parte 1 (la versión con más detalle), si la tienes.
