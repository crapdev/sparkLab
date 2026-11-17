# Punto de retoma

Actualizado el 2026-11-16. Leer esto primero al retomar el proyecto.

## Dónde estamos

| Módulo                         | Estado                                                                                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1. Fundamentos de Spark        | Hecho y verificado. Subido a GitHub por el usuario; **modificado después en disco** (refuerzo de acciones, ver abajo): hay que volver a subirlo. |
| 2. Lectura de datos y esquemas | Hecho y verificado. En disco; falta que el usuario lo suba.                                                                                      |
| 3. Seleccionar y filtrar       | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                 |
| 4. Crear y modificar columnas  | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                 |
| 5. Ordenar y limpiar           | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                 |
| 6. Strings y fechas            | **Siguiente.** Diseñado en [02-curriculum.md](02-curriculum.md), sin empezar.                                                                    |
| 7 a 15                         | Pendientes. Existen como `"status": "planned"` en `src/content/modules/`.                                                                        |

Última comprobación: lint, formato, tests, build y `npm run labs:check` (labs 1 a 5) pasan. El entorno local necesita ahora `pandas` (`requirements-labs.txt`) por el `toPandas()` del lab 1.

## Reglas acordadas con el usuario

1. **La página y los notebooks no mencionan el video ni dan créditos.** Nada de "en el
   video", "el instructor" ni enlaces con minutos. Usar frases neutras ("muchos
   tutoriales…"). El código y `docs/plan/` sí pueden mencionarlo.
2. **No hacer commits ni push.** El usuario los hace. Dejar los cambios en disco.
3. **Código y comentarios en inglés; contenido en español.**
4. **Un módulo cada vez**, y parar para que el usuario lo revise.
5. **Todo dato o salida que aparezca en la teoría o en los ejercicios se copia de una
   ejecución real de PySpark**, no de memoria ni de las notas de `material/`.
6. `material/` no se publica (está en `.gitignore`).

## Pendiente de confirmar por el usuario

- Si el lab 1 abre en Google Colab y la celda de instalación termina bien. El repositorio
  `crapdev/sparkLab` ya es público y sirve el lab 1 y los datos. La rama de la celda que
  instala Java en Colab nunca se ha ejecutado.
- `siteUrl` en `site.config.json` sigue con el marcador. Tras publicar en Vercel:
  `.venv/bin/python scripts/set-data-url.py https://<sitio>.vercel.app`

## Cómo se hace un módulo

1. **Probar con Spark real** lo que se va a enseñar (script temporal con `.venv/bin/python`)
   y guardar salidas, conteos y mensajes de error.
2. **Lab:** escribir `labs/NN-nombre/source.py` (formato explicado al inicio de
   `scripts/build-labs.py`; el lab 2 es el mejor ejemplo). Directivas: `[install]`,
   `[helpers]`, `[session]`, `[measure]`, `[data] archivos`, `[test]`, `[summary]`.
   Generar con `npm run labs:build` y verificar con `npm run labs:check`.
3. **Probar los tests rompiendo la solución:** escribir `labs/NN-nombre/mutations.json`
   (lista de `{name, old, new, expect}`; el lab 3 es el ejemplo) y ejecutar
   `.venv/bin/python scripts/mutate-lab.py NN-nombre`. Cada mutación sustituye un trozo
   de la solución y tiene que hacer fallar el test indicado en `expect`.
4. **Contenido:** en `src/content/modules/NN-nombre/` cambiar `module.json` a
   `"status": "published"` y completarlo (objetivos, lab, 5-8 ejercicios, quiz de 5-8
   preguntas), y escribir `theory.md` con al menos un diagrama SVG en
   `src/content/diagrams/` (usar las clases `d-*` de `src/styles/content.css`).
   Copiar la estructura del módulo 2.
5. **Chuleta:** añadir las funciones nuevas a `src/content/cheatsheet.json`.
6. **Verificar:** `npx prettier --write .`, `npm run check`, `npm run labs:check`, y mirar
   el módulo en el navegador (`npm run dev`).
7. Actualizar la tabla de estado del `README.md` y de este archivo.

El temario completo, con lo que lleva cada módulo, está en
[02-curriculum.md](02-curriculum.md). Los errores conocidos de las notas están en
[04-source-review.md](04-source-review.md).

## Refuerzo de acciones en el módulo 1 (petición del usuario, 2026-11-16)

- Teoría: sección nueva "Las acciones que vas a usar" con tabla de `show`, `count`,
  `take`/`head(n)`, `first`/`head()`, `collect`, `toPandas` y `write`, jobs y tasks medidos
  sobre el pipeline de 142 filas en 8 particiones; `limit()` (transformación, 0 jobs) frente a
  `take()`; aviso sobre `collect()`/`toPandas()` y el driver.
- Ejercicios nuevos: `ex-which-line` (en qué línea se ejecuta) y `ex-limit-take`. Quiz:
  `q-collect-risk` y `q-first-row`. Ya existía `ex-actions` (clasificar T/A).
- Lab 1: tarea 5 nueva (`limit`, `head`, `toPandas`, 4 tests) y demostración de `write` como
  acción (1 job, 8 archivos). Las antiguas tareas 5 y 6 pasan a ser 6 y 7. Se añadió
  `labs/01-fundamentos/mutations.json` (6 mutaciones).
- Chuleta: campo opcional `kind` (`transformación` | `acción`) mostrado como etiqueta T/A;
  obligatorio en las categorías Transformaciones y Acciones (hay test). Las expresiones de
  columna (`F.col`, `when`, `cast`…) pasaron a la categoría nueva **Columnas**, sin etiqueta.
  Entradas nuevas: `limit`, `head`, `toPandas`, `write`.
- Ningún lab usa `display()`; ahora hay un test que lo impide.
- Medido: `limit(5)` 0 jobs; `take(5)`, `head(5)`, `first()`, `show(5)` 1 job y 1 task;
  `collect()`, `toPandas()` y `write.csv()` 1 job y 8 tasks; `count()` 1 job, 2 stages, 9
  tasks (sin AQE). `toPandas()` sin `pyarrow` funciona pero avisa; en Colab hay pyarrow.

## Módulo 3, hecho

Lab de 6 tareas sobre `bigmart_sales.csv` (`labs/03-seleccionar-filtrar/`), con 17 tests y
15 mutaciones que los validan (ninguna bebida pesa exactamente 10, así que `<=` en vez de `<` no se puede distinguir con estos datos). Teoría con el diagrama `select-vs-filter.svg`, 8 ejercicios,
8 preguntas de quiz y 10 entradas nuevas en la chuleta.

Conteos medidos con Spark y usados en el módulo: `Regular` 2889; `Soft Drinks` con peso
menor de 10: 166; `Outlet_Size` nulo en Tier 1 o 2: 1855; Dairy o Meat fuera de Tier 3:
667; `Item_Weight < 10`: 2377 y su negación 4683 (suman 7060: faltan los 1463 nulos);
`~isin("Tier 3")`: 5173; `between(10, 20)`: 4224; `like("FD%")`: 6125; `endswith("Foods")`:
2204; `contains("Drinks")`: 659; `like("low%")`: 112.

Mensajes de error capturados: `and`/`or` y los paréntesis olvidados dan
`PySparkValueError [CANNOT_CONVERT_COLUMN_INTO_BOOL]`; `~F.col("x") == "y"` sin paréntesis
no falla al construirse sino al ejecutar, con `SparkRuntimeException [CAST_INVALID_INPUT]`;
una columna inexistente da `AnalysisException [UNRESOLVED_COLUMN.WITH_SUGGESTION]` con
sugerencias. `== None` devuelve 0 filas. `df.select("a").filter(F.col("b") < 10)` funciona
aunque `b` no esté seleccionada (Spark resuelve la columna del plan anterior): no
presentarlo como error.

## Módulo 4, hecho

Lab de 6 tareas sobre `bigmart_sales.csv` (`labs/04-columnas/`), con 16 tests y 15
mutaciones (ningún precio vale exactamente 100 ni 200, así que `<=` frente a `<` en las
bandas no se distingue con estos datos). Teoría con el diagrama `when-chain.svg`, 8 ejercicios, 8 preguntas de quiz y
9 entradas nuevas en la chuleta (más el `gotcha` de `withColumn` del módulo 1 actualizado).

Conteos medidos con Spark: `Item_Weight * Item_MRP` da 1463 nulos (primer valor
2323.22556); normalizar `Item_Fat_Content` da `Low Fat` 5517 y `Regular` 3006; bandas de
precio `< 100` / `< 200` / resto: 2439, 4644, 1440; `Item_MRP` va de 31.29 a 266.8884, sin
nulos y **sin ningún valor exactamente 100** (el hueco del currículo no se reproduce con
el precio); `Item_Weight` tiene 43 valores exactamente 10, así que `< 10` / `> 10` sin
`otherwise` deja 1506 nulos (43 + 1463). Con `when` invertido (`< 200` antes de `< 100`),
`cheap` queda con 0 filas. `Meat` → `Non-Veg`: 425 frente a 8098.

**Corrección importante al currículo:** en Spark 4 `spark.sql.ansi.enabled` es `true`, y
un `cast` imposible no devuelve `NULL`: lanza `NumberFormatException [CAST_INVALID_INPUT]`
al ejecutar la acción. `F.col(...).try_cast("int")` devuelve `NULL` (`F.try_cast` no
existe). Lo mismo pasa al multiplicar una columna string por un entero (`'9.3'` a `BIGINT`
falla) y al mezclar tipos en las ramas de un `when` (`"cheap"` con `0`). Apuntado en
[04-source-review.md](04-source-review.md). Si en un módulo futuro hace falta el
comportamiento antiguo, `spark.conf.set("spark.sql.ansi.enabled", "false")` **antes** de
construir el DataFrame (cambiarlo después no afecta a los planes ya creados).

Otros detalles: `withColumn("x", "texto")` da `PySparkTypeError [NOT_EXPECTED_TYPE]`;
`withColumnRenamed` con un nombre inexistente no falla; `otherwise()` dos veces da
`IllegalArgumentException`; `regexp_replace(col, ".", ",")` sobre `1.5` da `,,,`.

## Módulo 5, hecho

Lab de 6 tareas (`labs/05-ordenar-limpiar/`) sobre BigMart más un DataFrame `orders` de 8
filas con duplicados reales, 17 tests y 13 mutaciones (con un diccionario, `fillna` acepta `"12.86"` como texto para una
columna double y lo convierte: no sirve como mutación). Teoría con el diagrama
`dropna-modes.svg`, 8 ejercicios, 8 preguntas de quiz y 5 entradas nuevas en la chuleta
(`distinct` pasó al módulo 5).

Conteos medidos con Spark: peso máximo 21.35 (7 filas; con visibilidad ascendente la
primera tiene 0.068765205), peso mínimo 4.555; precios máximos 266.8884 (FDS13 y FDR25) y
266.6884 (FDK51). `dropDuplicates()` y `distinct()` dejan 8523 (sin duplicados exactos);
por `Item_Type` 16, por `Item_Identifier` 1559, por `Outlet_Identifier` 10, por
`Item_Type` + `Item_Fat_Content` 70. `dropna(how="any")` 4650, `how="all"` 8523,
`subset=["Outlet_Size"]` 6113, `subset=["Item_Weight"]` 7060, `thresh=12` 4650; ninguna fila
tiene los dos nulos. Media de `Item_Weight` 12.857645 (12.86). `fillna("texto")` deja
`Item_Weight` con 1463 nulos incluso con `subset=["Item_Weight"]`; `fillna(0)` no toca
`Outlet_Size`. En `orders`: 8 filas, 5 distintas, 3 clientes, 4 parejas cliente+tipo.
Nulos al ordenar: ascendente primero, descendente al final.

## Módulo 6, siguiente

Diseño en [02-curriculum.md](02-curriculum.md#6-strings-y-fechas): `initcap`, `lower`,
`upper`; `current_date`, `date_add`, `date_sub`, `datediff`, `date_format`. Extra: `trim`,
`concat_ws`, `substring`, `to_date`, `year`, `month`. Diagrama previsto: orden de los
argumentos de `datediff` en una línea de tiempo. Lab sobre `drivers.json`: `dob` llega como
`string` y hay que convertirlo con `to_date`; calcular edad y formatear. Los tests deben usar
una fecha fija, no `current_date`, para no depender del día. Errores comunes: `YYYY` en vez
de `yyyy`; `date_format` devuelve texto. Medir todo antes de escribir.

## Datos útiles ya medidos

- Entorno local: Python 3.14, Java 21, PySpark 4.2.0 en `.venv/`. `delta-spark` 4.4.1
  exige PySpark ≤ 4.2.0, por eso está fijada esa versión.
- BigMart: 8523 filas, 12 columnas, 16 tipos de ítem, 1463 pesos nulos, 2410
  `Outlet_Size` nulos, sin filas totalmente duplicadas. `Item_Fat_Content` trae cinco
  variantes: `Low Fat` 5089, `Regular` 2889, `LF` 316, `reg` 117, `low fat` 112.
- Pilotos: 885 registros, 765 sin `code`, 811 sin `number`, 7 sin `dob`.
- Spark optimiza más de lo esperado: ordenar un `spark.range` por `id` o hacerle
  `distinct()` no provoca shuffle. Tenerlo en cuenta al diseñar tests de stages.
