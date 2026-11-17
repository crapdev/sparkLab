# PySpark Labs

Sitio web para estudiar y practicar PySpark: teoría corta con diagramas, ejercicios
interactivos en el navegador y laboratorios en Google Colab con tests automáticos.

## Estado

| Módulo                  | Estado         |
| ----------------------- | -------------- |
| 1. Fundamentos de Spark | Publicado      |
| 2 a 15                  | En preparación |

El plan completo está en [docs/plan](docs/plan/README.md).

## Cómo funciona

- **Sin backend.** El progreso se guarda en el `localStorage` del navegador y se puede
  exportar e importar como JSON.
- **PySpark no corre en el navegador** porque necesita la JVM. Los ejercicios del sitio
  comparan respuestas; el código de verdad se ejecuta en los laboratorios de Colab.
- **Cada laboratorio se verifica con PySpark real** antes de publicarse.

## Requisitos

| Para               | Necesitas                                   |
| ------------------ | ------------------------------------------- |
| El sitio           | Node.js 20 o superior                       |
| Verificar los labs | Python 3.11 o superior y Java 17 o superior |

Si te falta Java en Ubuntu o Debian:

```bash
sudo apt install openjdk-21-jdk-headless
```

## Puesta en marcha

```bash
npm install
```

```bash
npm run dev
```

Para verificar los laboratorios, crea una vez el entorno de Python:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-labs.txt
```

## Comandos

| Comando              | Qué hace                                                     |
| -------------------- | ------------------------------------------------------------ |
| `npm run dev`        | Servidor de desarrollo                                       |
| `npm run build`      | Build de producción en `dist/`                               |
| `npm run lint`       | ESLint                                                       |
| `npm run format`     | Formatea con Prettier                                        |
| `npm test`           | Tests unitarios y validación del contenido                   |
| `npm run labs:build` | Genera los notebooks a partir de `labs/*/source.py`          |
| `npm run labs:check` | Ejecuta todos los notebooks con PySpark y verifica los tests |
| `npm run check`      | Lint, formato, tests y build, todo seguido                   |

## Estructura

```
├── docs/plan/               # Project plan
├── labs/<module>/           # source.py + generated lab.ipynb and solution.ipynb
├── public/data/             # Datasets served by the site
├── scripts/                 # Lab tooling (build, check, datasets)
├── src/
│   ├── content/
│   │   ├── modules/<module>/  # module.json + theory.md
│   │   ├── diagrams/          # One SVG per diagram
│   │   ├── blocks.json
│   │   └── cheatsheet.json
│   ├── components/          # Exercises, quiz, lab card, progress bar
│   ├── views/               # Home, module, cheatsheet, progress, about
│   ├── services/            # storage.js, content, markdown, checkers
│   └── styles/
├── tests/                   # Vitest
└── site.config.json         # Repo, site URL, PySpark version
```

Todo el acceso a `localStorage` pasa por `src/services/storage.js`. Las claves están
versionadas (`pyspark-labs:v1:progress`, `pyspark-labs:v1:settings`).

## Añadir o completar un módulo

1. Crea `src/content/modules/NN-nombre/` con:
   - `module.json`: metadatos, ejercicios, quiz y datos del laboratorio.
   - `theory.md`: la teoría en Markdown.
2. Escribe el laboratorio en `labs/NN-nombre/source.py` y genera los notebooks con
   `npm run labs:build`.
3. Añade las funciones nuevas a `src/content/cheatsheet.json`.
4. Comprueba con `npm test` y `npm run labs:check`.

No hay que registrar el módulo en ningún sitio: se descubre por la carpeta. Un módulo con
`"status": "planned"` aparece en el inicio como «Próximamente»; con `"published"` tiene
que estar completo o `npm test` falla.

### Extensiones de Markdown en `theory.md`

| Sintaxis                                              | Resultado                                 |
| ----------------------------------------------------- | ----------------------------------------- |
| `![texto alternativo](diagram:nombre "pie")`          | Inserta `src/content/diagrams/nombre.svg` |
| `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!EXTRA]` | Cajas de aviso                            |
| Bloque de código con lenguaje `output`                | Salida de programa, sin resaltado         |

### Tipos de ejercicio

| Tipo             | El usuario…                               |
| ---------------- | ----------------------------------------- |
| `choice`         | Elige una o varias opciones               |
| `predict-output` | Lee un código y elige o escribe la salida |
| `fill-code`      | Rellena huecos marcados con `___`         |

## Laboratorios

Cada laboratorio se escribe una sola vez, en `labs/<módulo>/source.py`, con la solución
marcada entre `### BEGIN SOLUTION` y `### END SOLUTION`. De ahí salen dos notebooks:
`lab.ipynb` (para resolver) y `solution.ipynb`. El formato está documentado al principio
de `scripts/build-labs.py`.

`npm run labs:check` comprueba para cada laboratorio que:

1. los notebooks están al día con su `source.py`;
2. la solución se ejecuta entera y pasa todos los tests;
3. el laboratorio sin resolver **falla** en un test, lo que demuestra que los tests
   comprueban algo.

Los notebooks descargan los datos del sitio publicado y, si no está disponible, del
repositorio de GitHub.

## Publicar

El sitio es estático y está pensado para Vercel conectado a GitHub. El repositorio tiene
que ser **público**: Google Colab abre los notebooks directamente desde GitHub.

Tras el primer despliegue, apunta los notebooks a la URL publicada:

```bash
.venv/bin/python scripts/set-data-url.py https://TU-SITIO.vercel.app
```

## Datos

| Archivo                  | Origen                                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------------------------- |
| `bigmart_sales.csv`      | Reto de práctica BigMart Sales de Analytics Vidhya. Uso educativo.                                      |
| `drivers.json`           | Pilotos de Fórmula 1, de la API [Jolpica-F1](https://github.com/jolpica/jolpica-f1), sucesora de Ergast |
| `drivers_multiline.json` | Los 20 primeros pilotos del anterior, como array con sangría                                            |

`scripts/fetch-drivers.py` regenera los dos archivos de pilotos.
