# 01 · Arquitectura del sitio

## Stack

| Pieza               | Elección                                 | Por qué                                                     |
| ------------------- | ---------------------------------------- | ----------------------------------------------------------- |
| Build               | Vite                                     | Rápido, sin configuración, preset nativo en Vercel          |
| UI                  | HTML + CSS + JS vanilla (ES modules)     | Lo pediste así; el sitio es pequeño y no necesita framework |
| Markdown            | `marked`                                 | Convierte la teoría `.md` en HTML; ligero                   |
| Resaltado de código | `highlight.js` (solo Python, SQL y Bash) | Importando solo esos lenguajes el peso es mínimo            |
| Diagramas           | SVG propio                               | Mermaid pesa demasiado para lo que aporta aquí              |
| Calidad             | ESLint (flat config) + Prettier + Vitest | Lint, formato y tests unitarios                             |
| Hosting             | Vercel conectado a GitHub                | Cada `git push` a `main` despliega                          |

Dependencias de ejecución: solo `marked` y `highlight.js`. Todo lo demás es de desarrollo.

## Estructura de carpetas

```
sparkLab/
├── material/                      # Gemini notes (source only, gitignored)
├── docs/plan/                     # This plan
├── public/
│   └── data/                      # Datasets served by Vercel
│       ├── bigmart_sales.csv
│       ├── drivers.json
│       └── drivers_multiline.json
├── src/
│   ├── content/
│   │   ├── modules/
│   │   │   ├── 01-fundamentos/
│   │   │   │   ├── module.json    # Metadata, exercises, quiz
│   │   │   │   └── theory.md      # Theory in Markdown
│   │   │   └── ...
│   │   ├── diagrams/              # One SVG per diagram
│   │   └── cheatsheet.json        # Function reference
│   ├── components/                # quiz, fill-code, predict-output, diagram, ...
│   ├── views/                     # home, module, cheatsheet, progress, about
│   ├── services/
│   │   ├── storage.js             # ALL localStorage access
│   │   └── content.js             # Loads and validates modules
│   ├── styles/                    # tokens.css, base.css, components.css
│   ├── config.js                  # Repo, video URL, site URL (single place)
│   ├── router.js
│   └── main.js
├── labs/
│   ├── 01-fundamentos/
│   │   ├── source.py              # Single source (solution + markers)
│   │   ├── lab.ipynb              # Generated: starter code + asserts
│   │   └── solution.ipynb         # Generated: solved
│   └── ...
├── scripts/
│   ├── build-labs.py              # source.py -> lab.ipynb + solution.ipynb
│   ├── check-labs.py              # Runs every notebook, verifies tests
│   ├── set-data-url.py            # Rewrites the dataset URL in all notebooks
│   └── fetch-drivers.py           # Rebuilds drivers.json
├── tests/                         # Vitest: storage, checkers, content
├── index.html
├── package.json
├── requirements-labs.txt          # Pinned PySpark for local checks
├── vite.config.js
├── eslint.config.js
├── .prettierrc
├── .gitignore
└── README.md
```

Cambios respecto a tu propuesta, y motivo:

| Cambio                                                                   | Motivo                                                                                                                                             |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Carpeta por módulo (`module.json` + `theory.md`) en vez de un JSON único | La teoría con bloques de código dentro de strings JSON obliga a escapar comillas y saltos de línea; en Markdown se escribe y se revisa mucho mejor |
| `labs/NN/source.py` como fuente única                                    | Dos notebooks mantenidos a mano se desincronizan; así se generan los dos del mismo archivo                                                         |
| `src/views/` separado de `src/components/`                               | Distingue páginas enteras de piezas reutilizables                                                                                                  |
| `src/config.js`                                                          | Repo de GitHub, URL del video y URL del sitio en un solo sitio                                                                                     |
| `tests/`                                                                 | Tests unitarios de `storage.js` y de los correctores de ejercicios                                                                                 |
| El proyecto se queda en la carpeta actual `sparkLab/`                    | Ya tiene el repo git inicializado; el nombre del paquete será `pyspark-labs`                                                                       |

## Navegación

Router por hash, sin dependencias. Funciona en Vercel y en cualquier hosting
estático sin reglas de reescritura.

| Ruta              | Vista                                                                    |
| ----------------- | ------------------------------------------------------------------------ |
| `#/`              | Inicio: bloques y módulos, barra de progreso, "Continuar donde quedaste" |
| `#/modulo/<slug>` | Módulo: pestañas Teoría, Ejercicios, Quiz, Laboratorio                   |
| `#/chuleta`       | Buscador de funciones de PySpark                                         |
| `#/progreso`      | Resumen de progreso, exportar e importar JSON, reiniciar                 |
| `#/acerca`        | Créditos al curso de Ansh Lamba, enlace al video, cómo contribuir        |

Los créditos también van en el pie de todas las páginas.

## Modelo de contenido

Agregar un tema es agregar una carpeta en `src/content/modules/`. Se descubren
solas con `import.meta.glob`; no hay que registrar nada en el código.

`module.json` (ejemplo resumido):

```json
{
  "id": "03-seleccionar-filtrar",
  "order": 3,
  "block": "transformaciones",
  "title": "Seleccionar y filtrar",
  "summary": "Elegir columnas y filas: select, col, alias y filter.",
  "estimatedMinutes": 40,
  "isExtra": false,
  "video": [{ "label": "Select", "start": "0:56:55", "end": "1:02:28" }],
  "lab": { "path": "labs/03-seleccionar-filtrar", "dataset": ["bigmart_sales.csv"] },
  "exercises": [
    {
      "id": "ex-filter-and",
      "type": "fill-code",
      "prompt": "Completa el filtro para quedarte con bebidas de menos de 10 kg.",
      "code": "df.filter((F.col(\"Item_Type\") == \"Soft Drinks\") ___ (F.col(\"Item_Weight\") < 10))",
      "blanks": [{ "answers": ["&"], "hint": "En PySpark el AND entre columnas no es `and`." }],
      "explanation": "Se usa `&` y cada condición va entre paréntesis."
    }
  ],
  "quiz": [
    {
      "id": "q1",
      "type": "single",
      "question": "¿Qué devuelve `df.select(\"Item_Type\")`?",
      "options": ["Una lista de Python", "Un DataFrame nuevo", "Modifica `df`"],
      "answer": 1,
      "explanation": "Los DataFrames son inmutables: cada transformación devuelve uno nuevo."
    }
  ]
}
```

`theory.md` es Markdown normal con bloques de código. Dos extensiones pequeñas:

- `![Texto alternativo](diagram:lazy-evaluation)` inserta el SVG
  `src/content/diagrams/lazy-evaluation.svg` en línea.
- Bloques `> [!NOTE]`, `> [!WARNING]` y `> [!EXTRA]` para notas, errores comunes
  y contenido que no está en el video.

### Tipos de ejercicio

| Tipo                        | Qué hace el usuario                       | Cómo se corrige                                                                               |
| --------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------- |
| `quiz` (`single` / `multi`) | Elige una o varias opciones               | Compara con el índice correcto                                                                |
| `predict-output`            | Lee un código y elige o escribe la salida | Compara con la respuesta esperada                                                             |
| `fill-code`                 | Rellena huecos en un fragmento            | Compara cada hueco con una lista de respuestas válidas, ignorando espacios y tipo de comillas |

Ningún ejercicio ejecuta código. Cada uno trae una explicación que se muestra al
acertar; tras dos fallos se puede pedir la respuesta, que también la muestra. Las salidas de `predict-output` se copian de
ejecuciones reales de PySpark, no se escriben de memoria.

## `src/services/storage.js`

Único archivo que toca `localStorage`. El resto del sitio usa sus funciones.

### Claves

| Clave                      | Contenido            |
| -------------------------- | -------------------- |
| `pyspark-labs:v1:progress` | Progreso del usuario |
| `pyspark-labs:v1:settings` | Preferencias (tema)  |

### Forma de los datos

```json
{
  "schemaVersion": 1,
  "updatedAt": "2026-11-16T20:00:00.000Z",
  "lastVisited": { "moduleId": "03-seleccionar-filtrar", "tab": "ejercicios" },
  "modules": {
    "01-fundamentos": {
      "theoryRead": true,
      "exercises": { "ex-lazy-1": { "correct": true, "attempts": 2 } },
      "quiz": { "bestScore": 4, "total": 5, "attempts": 1 },
      "labDone": true,
      "completedAt": "2026-11-16T20:00:00.000Z"
    }
  }
}
```

```json
{ "theme": "system" }
```

### API

| Función                                                          | Uso                                                         |
| ---------------------------------------------------------------- | ----------------------------------------------------------- |
| `getProgress()`                                                  | Devuelve el progreso, o uno vacío si no hay o está corrupto |
| `saveExerciseResult(moduleId, exerciseId, correct)`              | Registra un intento                                         |
| `saveQuizResult(moduleId, score, total)`                         | Guarda la mejor nota                                        |
| `setTheoryRead(moduleId, value)` / `setLabDone(moduleId, value)` | Marcas manuales                                             |
| `setLastVisited(moduleId, tab)` / `getLastVisited()`             | "Continuar donde quedaste"                                  |
| `getModuleStatus(moduleId, module)`                              | Porcentaje y si está completado                             |
| `getTheme()` / `setTheme(theme)`                                 | `light`, `dark` o `system`                                  |
| `exportProgress()`                                               | Devuelve un JSON descargable                                |
| `importProgress(json)`                                           | Valida y reemplaza; devuelve `{ ok, error }`                |
| `resetProgress()`                                                | Borra el progreso (con confirmación en la interfaz)         |
| `isStorageAvailable()`                                           | Para avisar si el navegador lo bloquea                      |

### Reglas

- **Toda lectura y escritura va en `try/catch`.** Si `localStorage` falla
  (modo privado, cuota llena, bloqueado), el sitio sigue funcionando con el
  progreso en memoria y muestra un aviso discreto.
- **JSON corrupto no rompe nada:** se ignora y se parte de un progreso vacío.
- **Importar valida antes de escribir:** versión del esquema, tipos y que los
  IDs de módulo existan. Un archivo inválido no pisa el progreso actual.
- **Versionado:** si el esquema cambia, la clave pasa a `v2` y una función de
  migración lee `v1`. El archivo exportado incluye `schemaVersion`.
- **Un módulo está completado** cuando el quiz está aprobado (70 % o más) y el
  lab está marcado como hecho. El porcentaje del módulo cuenta teoría leída,
  ejercicios correctos, quiz y lab.

## Tema claro y oscuro

Colores como variables CSS en `tokens.css`. Por defecto sigue al sistema
(`prefers-color-scheme`); el usuario puede fijarlo y se guarda en `settings`.
El tema se aplica con un script mínimo en `index.html` antes de pintar, para que
no parpadee al cargar. Los diagramas SVG usan las mismas variables.

## Chuleta de funciones

`src/content/cheatsheet.json`, una entrada por función:

```json
{
  "name": "dropDuplicates",
  "category": "Limpieza",
  "kind": "transformación",
  "signature": "df.dropDuplicates(subset=None)",
  "description": "Quita filas repetidas; con subset compara solo esas columnas.",
  "example": "df.dropDuplicates(subset=[\"Item_Type\"])",
  "gotcha": "Con subset, la fila que sobrevive no está garantizada.",
  "module": "05-ordenar-limpiar",
  "keywords": ["duplicados", "distinct", "unique"]
}
```

`kind` es opcional y vale `transformación` o `acción`; la chuleta lo muestra como una
etiqueta **T** o **A**, y es obligatorio en las categorías Transformaciones y Acciones.
El buscador filtra en el cliente por nombre, descripción y palabras clave (en
español e inglés), con filtro por categoría y enlace al módulo donde se explica.
Unas 120 entradas al terminar.

## Componentes

| Componente          | Responsabilidad                                                 |
| ------------------- | --------------------------------------------------------------- |
| `quiz.js`           | Preguntas de opción, nota y repaso de errores                   |
| `fill-code.js`      | Código con huecos y validación                                  |
| `predict-output.js` | Código + elección de salida                                     |
| `code-block.js`     | Resaltado y botón de copiar                                     |
| `diagram.js`        | Inserta el SVG y su descripción accesible                       |
| `lab-card.js`       | Botón "Abrir en Google Colab", datasets, marcar como completado |
| `progress-bar.js`   | Barra por módulo y global                                       |
| `theme-toggle.js`   | Cambio de tema                                                  |
| `search.js`         | Buscador de la chuleta                                          |

## Calidad

| Comando                           | Qué hace                                                     |
| --------------------------------- | ------------------------------------------------------------ |
| `npm run dev`                     | Servidor local                                               |
| `npm run build`                   | Build de producción                                          |
| `npm run lint` / `npm run format` | ESLint y Prettier                                            |
| `npm test`                        | Vitest: `storage.js`, correctores y validación del contenido |
| `npm run labs:build`              | Genera los notebooks desde `source.py`                       |
| `npm run labs:check`              | Ejecuta todos los notebooks y verifica los tests             |

El test de contenido recorre todos los `module.json` y comprueba campos
obligatorios, IDs únicos, que cada respuesta apunte a una opción existente y
que el lab y los diagramas referenciados existan. Así un módulo mal escrito
falla en `npm test` y no en producción.

## Accesibilidad y móvil

- Se usa bien en el móvil: los compañeros lo abrirán para repasar.
- Navegable con teclado, foco visible, contraste suficiente en los dos temas.
- Los diagramas llevan texto alternativo que explica lo que muestran.
- Los bloques de código hacen scroll horizontal dentro de su caja, no la página.
