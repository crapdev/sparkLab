# Corrección del módulo 1: explicar la SparkSession

## El problema

La teoría del módulo 1 (`src/content/modules/01-fundamentos/theory.md`) nombra la
`SparkSession` una sola vez, en la tabla "Colab frente a Databricks", pero nunca
explica qué es ni cómo se crea. Sin embargo:

- el objetivo 6 del módulo dice "Crear una SparkSession y medir los jobs...";
- la Tarea 1 del lab pide crearla con `SparkSession.builder.master(...).appName(...).getOrCreate()`;
- el ejercicio `ex-session` (fill-code) pide completar `master` y `getOrCreate`;
- la chuleta tiene `SparkSession.builder` y `spark.conf.set` enlazados al módulo 1.

El estudiante llega al lab sin saber qué es `spark`, qué hace `builder`, qué
significa `local[*]` ni por qué se llama `getOrCreate`.

## Dónde encaja

Nueva sección **"La SparkSession: tu puerta de entrada"** justo después de
"Las piezas de un clúster" y antes de "Transformaciones y acciones". Motivo: la
sección del clúster acaba hablando del driver, y la SparkSession es el objeto que
vive en el driver y representa tu aplicación. Así el orden queda:
clúster → la sesión que habla con ese clúster → lo que haces con ella
(transformaciones y acciones).

## Contenido de la sección (todo medido con PySpark real)

1. **Qué es.** Un solo objeto, por convención llamado `spark`, que representa tu
   aplicación dentro del clúster. Con él lees datos (`spark.read`), creas
   DataFrames (`spark.range`, `spark.createDataFrame`), ejecutas SQL (`spark.sql`)
   y cambias configuración (`spark.conf`). Vive en el driver. Mencionar que por
   debajo tiene un `SparkContext` (`spark.sparkContext`), la API antigua, y que
   en el curso solo se usa para mirar el `master` y las particiones.
2. **La receta, pieza a pieza:**
   ```python
   from pyspark.sql import SparkSession

   spark = SparkSession.builder.master("local[*]").appName("mi-app").getOrCreate()
   ```
   - `builder`: un constructor al que vas añadiendo opciones encadenadas; no
     crea nada por sí solo.
   - `master("local[*]")`: dónde se ejecuta. `local[*]` = esta máquina con
     todos los núcleos; `local[2]` = dos núcleos; en un clúster real sería la URL
     de YARN/Kubernetes y normalmente no la pones tú. Medir y mostrar
     `spark.sparkContext.defaultParallelism` en Colab (2 núcleos) y explicar que
     por eso `spark.range(...)` sale con ese número de particiones.
   - `appName`: el nombre que ves en la Spark UI y en los logs.
   - `getOrCreate()`: el único paso que crea algo. Si ya existe una sesión en el
     proceso, devuelve esa y **ignora** el master y el nombre nuevos. Medirlo:
     crear una segunda sesión con otro `appName` y mostrar que
     `spark2.sparkContext.appName` sigue siendo el primero y que
     `spark2 is spark` es `True`.
3. **Qué sabe la sesión de sí misma.** Bloque ```output real con
   `spark.version`, `spark.sparkContext.master`, `spark.sparkContext.appName`,
   `spark.sparkContext.defaultParallelism`.
4. **Configuración.** `spark.conf.get("spark.sql.shuffle.partitions")` → `200`
   por defecto, y `spark.conf.set(...)` para cambiarlo; adelantar que en los
   módulos de rendimiento se verá por qué importa. Mencionar que algunas
   opciones (como `spark.driver.memory`) solo se pueden fijar al crear la
   sesión, con `.config("clave", valor)` en el builder, y no después con `conf.set`.
5. **El final: `spark.stop()`.** Cierra la aplicación y libera executors. En
   Colab no suele hacer falta; en scripts sí. Avisar: después de `stop()`
   cualquier DataFrame antiguo falla, y `getOrCreate()` crea una sesión nueva.
6. **Callout [!NOTE]**: En Databricks y en `pyspark` interactivo `spark` ya
   existe; en Colab, en un script `.py` o en un `spark-submit` la creas tú. Eso
   es lo que resume la tabla "Colab frente a Databricks" más abajo.
7. **Callout [!WARNING]**: Una sesión por proceso. Llamar al builder dos veces
   no te da dos clústeres; `getOrCreate` devuelve la misma sesión.
8. **Diagrama SVG nuevo `spark-session.svg`** (clases `d-*` como los demás,
   ancho ~800): tu código → `spark` (SparkSession, dentro del driver) con sus
   cuatro puertas `read`, `createDataFrame`, `sql`, `conf` → executors. Caption:
   "Todo lo que pides a Spark pasa por la sesión". Revisarlo en el navegador
   para que no se solapen etiquetas.

Añadir a "Errores comunes" dos puntos:

- Olvidar `getOrCreate()`: `spark` es un `Builder`, y `spark.read` da
  `AttributeError: 'Builder' object has no attribute 'read'` (verificar el
  mensaje exacto con PySpark 4.2).
- Cambiar `master`/`appName` en un segundo builder y esperar que haga efecto.

## Cambios en module.json

- Objetivo 6: separar en dos, "Explicar qué es la SparkSession y qué hace cada
  paso de `builder...getOrCreate()`" y "Medir los jobs que lanza tu código".
- Ejercicios (mantener 10 en total, sustituyendo o añadiendo):
  - `ex-session`: conservar, pero ampliar la explicación con lo de "`getOrCreate`
    devuelve la que exista".
  - Nuevo `choice` "¿Qué devuelve `SparkSession.builder.appName('x')` sin
    `getOrCreate()`?" → un Builder, no una sesión.
  - Nuevo `predict-output`: dos `getOrCreate` seguidos con nombres distintos,
    ¿qué imprime `spark2.sparkContext.appName`? → el primero.
- Quiz: nueva pregunta "¿Dónde vive la SparkSession?" → en el driver; y otra
  sobre `local[*]`.
- `lab.tasks[0]`: "Crear una `SparkSession` en modo local y comprobar su
  configuración".

## Cambios en el lab 1 (`labs/01-fundamentos/source.py`)

- Tarea 1: antes del código, una celda markdown corta que remita a la sección
  nueva y explique `local[*]` en una línea. Añadir una celda de demostración
  (no evaluada) tras los tests: imprimir `spark.version`, `master`, `appName`,
  `defaultParallelism`, y el experimento de `getOrCreate` con otro nombre.
- Nuevo test en Tarea 1: `spark.sparkContext.appName == "lab-01-fundamentos"`.
- Mutación nueva en `mutations.json`: quitar `.getOrCreate()` → debe fallar en
  "Tarea 1 · spark es una SparkSession"; cambiar el appName → falla el test nuevo.
- Volver a correr `npm run labs:build`, `npm run labs:check` y
  `.venv/bin/python scripts/mutate-lab.py 01-fundamentos`.
- Ojo: el lab 1 ya está publicado; al terminar hay que resubirlo a Colab.

## Chuleta (`src/content/cheatsheet.json`, categoría Sesión)

- `SparkSession.builder`: ampliar el "Ojo" con lo del Builder sin `getOrCreate`.
- Nuevas entradas: `spark.sparkContext` (master, appName, defaultParallelism),
  `spark.version`, `spark.stop()`, `builder.config(clave, valor)`.
- Ninguna lleva etiqueta T/A: no son transformaciones ni acciones (como las
  expresiones de columna).

## Verificación

1. `npm run check` (lint, prettier, vitest, build).
2. `npm run labs:check` para el lab 1 y mutaciones.
3. Revisar el módulo 1 en el navegador (`.claude/launch.json` → `pyspark-labs`,
   puerto 5174): diagrama nuevo sin solapes, sin errores de consola.
4. `grep -ri "video\|youtube\|instructor"` sobre el contenido del módulo: nada.
5. Actualizar `docs/plan/HANDOFF.md` (nota "Módulo 1, SparkSession explicada")
   y `README.md` si cambia el número de entradas de la chuleta.
