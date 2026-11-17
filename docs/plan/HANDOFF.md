# Punto de retoma

Actualizado el 2026-11-17. Leer esto primero al retomar el proyecto.

## Dónde estamos

| Módulo                         | Estado                                                                                                                                                                                                   |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Fundamentos de Spark        | Hecho y verificado. Subido a GitHub por el usuario; **modificado después en disco** (refuerzo de acciones y SparkSession explicada, ver abajo): hay que volver a subirlo y **resubir el lab 1 a Colab**. |
| 2. Lectura de datos y esquemas | Hecho y verificado. En disco; falta que el usuario lo suba.                                                                                                                                              |
| 3. Seleccionar y filtrar       | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                                                                         |
| 4. Crear y modificar columnas  | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                                                                         |
| 5. Ordenar y limpiar           | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                                                                         |
| 6. Strings y fechas            | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                                                                         |
| 7. Arrays                      | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                                                                         |
| 8. Agregaciones                | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                                                                         |
| 9. Union y joins               | Hecho y verificado. En disco; pendiente de revisión del usuario. Trae el dataset nuevo `outlets.csv`.                                                                                                    |
| 10. Window functions           | Hecho y verificado. En disco; pendiente de revisión del usuario.                                                                                                                                         |
| 11. UDFs                       | Hecho y verificado (labs:check, 18 mutaciones). En disco; pendiente de revisión del usuario.                                                                                                             |
| 12. Escritura y formatos       | **Siguiente.** Diseñado en [02-curriculum.md](02-curriculum.md), sin empezar.                                                                                                                            |
| 13 a 15                        | Pendientes. Existen como `"status": "planned"` en `src/content/modules/`.                                                                                                                                |

Última comprobación: lint, formato, tests, build y `npm run labs:check` (labs 1 a 11) pasan. El entorno local necesita `pandas` (por el `toPandas()` del lab 1) y `pyarrow` (por las UDF del lab 11; en Spark 4.2 **cualquier** `F.udf` necesita pyarrow en el worker), los dos en `requirements-labs.txt`.

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

- `siteUrl` en `site.config.json` sigue con el marcador. Tras publicar en Vercel:
  `.venv/bin/python scripts/set-data-url.py https://<sitio>.vercel.app`

**Confirmado el 2026-11-17:** los labs abren y funcionan en Google Colab (instalación de
PySpark y Java incluida). El repositorio `crapdev/sparkLab` sirve los notebooks y los datos.

## Decisiones sobre datos (2026-11-17)

- Se sigue con `bigmart_sales.csv` (8523 filas) y `drivers.json` en los módulos 9 a 13:
  pequeño a propósito, para que los tests comprueben valores exactos y todo corra rápido.
- Módulo 9 (hecho): `public/data/outlets.csv`, una tabla de tiendas para los joins (ver el
  diseño en la sección del módulo 9).
- Módulo 14: los datos grandes se generan dentro del notebook (`spark.range` o BigMart
  replicado ×100), no se descargan.
- Módulo 15: BigMart ampliado a millones de filas más `outlets.csv`, de principio a fin.

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

## Módulo 1, SparkSession explicada (petición del usuario, 2026-11-17)

Plan en [fix-m1-sparksession.md](fix-m1-sparksession.md), aplicado entero:

- Teoría: sección nueva "La SparkSession: tu puerta de entrada" entre "Las piezas de un
  clúster" y "Transformaciones y acciones", con el diagrama `spark-session.svg` (tu código →
  `spark` en el driver con `read`, `createDataFrame`, `sql`, `conf` y `sparkContext` → executors),
  la receta pieza a pieza, el experimento de `getOrCreate`, configuración y `stop()`. Dos
  errores comunes nuevos (Builder sin `getOrCreate`; segundo builder con otro nombre).
- `module.json`: el objetivo 6 se partió en dos (7 objetivos). Ejercicios: siguen siendo 10;
  entraron `ex-builder-only` (choice) y `ex-getorcreate-name` (predict-output) y salieron
  `ex-show-output` y `ex-pipeline`; `ex-session` con explicación ampliada. Quiz: 12 preguntas
  con `q-session-where` y `q-local-star` nuevas. `lab.tasks[0]` actualizada.
- Lab 1: markdown de la Tarea 1 remite a la sección nueva y explica `local[*]`; test nuevo
  "Tarea 1 · el nombre de la aplicación es lab-01-fundamentos" (4 tests en la tarea); celda de
  demostración con `version`, `master`, `appName`, `defaultParallelism` y el experimento de
  `getOrCreate` con otro nombre. `mutations.json`: 8 mutaciones (2 nuevas: sin `getOrCreate`,
  otro `appName`). **El lab 1 ya estaba publicado: hay que resubirlo a Colab.**
- Chuleta, categoría Sesión: `SparkSession.builder` y `spark.conf.set` ampliadas; nuevas
  `builder.config`, `spark.sparkContext`, `spark.version` y `spark.stop` (sin etiqueta T/A).

Medido con Spark 4.2.0 en local: `spark.version` `4.2.0`; `master` `local[*]`;
`defaultParallelism` 8 (con `local[2]`, 2; con `local[1]`, 1) y `spark.range` nace con ese
número de particiones; `spark.sql.shuffle.partitions` por defecto `'200'`. Segundo
`SparkSession.builder.master("local[2]").appName("otra-app").getOrCreate()` devuelve la misma
sesión (`spark2 is spark` → `True`, nombre y master originales). `builder.config("spark.sql.
shuffle.partitions", "4").getOrCreate()` sobre una sesión existente **sí** aplica la opción SQL
(documentado en la chuleta). `spark.conf.set("spark.driver.memory", "2g")` →
`AnalysisException [CANNOT_MODIFY_CONFIG] Cannot modify the value of the Spark config:
"spark.driver.memory"`; `spark.conf.set("spark.master", "local[2]")` **no falla** pero no cambia
nada (`sparkContext.master` sigue `local[*]`, aunque `conf.get("spark.master")` devuelva el valor
nuevo): no se menciona en la página. Builder sin `getOrCreate`: `AttributeError: 'Builder'
object has no attribute 'read'` (y `'range'`). Tras `spark.stop()`: `df.count()` →
`Py4JJavaError`; `spark.range(3)` → `AttributeError: 'NoneType' object has no attribute 'sc'`;
un `getOrCreate()` nuevo crea otra sesión con el nombre y master nuevos.

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

## Módulo 6, hecho

Lab de 6 tareas (`labs/06-strings-fechas/`) sobre BigMart (texto) y `drivers.json`
(fechas), 15 tests y 14 mutaciones. Teoría con el diagrama `datediff-order.svg`, 8
ejercicios, 8 preguntas de quiz y 9 entradas nuevas en la chuleta (categoría Columnas).

Medido con Spark: prefijos de `Item_Identifier` FD 6125, NC 1599, DR 799; `SOFT DRINKS` 445;
`initcap` sobre `Item_Fat_Content` da `Lf` 316, `Low Fat` 5201, `Reg` 117, `Regular` 2889;
`initcap("alain de changy")` → `Alain De Changy`. Pilotos: 885, 7 sin `dob`, 765 sin `code`
(`concat` con `code` da 765 nulos, `concat_ws` ninguno). Hamilton: `dob` 1985-01-07, a
2025-01-01 lleva 14604 días y 479.806 meses → 39 años; `date_add(dob, 7)` 1985-01-14,
`date_sub(dob, 7)` 1984-12-31, `add_months(dob, 1)` 1985-02-07. Nacidos en 1990 o después:
59; en los 80: 39; menores de 30 a 2025-01-01: 39, menores de 25: 23; el más joven tiene
16 (`freddie_slater`, 2008-08-09); el más viejo `etancelin` 1896-12-28. `year("dob")`
funciona sobre el texto ISO (conversión implícita). `to_date` con patrón que no encaja
lanza `CANNOT_PARSE_TIMESTAMP`; sin patrón y texto no ISO, `CAST_INVALID_INPUT`;
`F.try_to_date` devuelve nulo. `date_format` con `YYYY` lanza
`INCONSISTENT_BEHAVIOR_CROSS_VERSION.DATETIME_PATTERN_RECOGNITION`; `mm` da `00`; `DD` es
el día del año (1985-02-10 → `41`). Nombres de mes y día salen en inglés (`January`,
`Monday`). `floor` devuelve `bigint`. `substring` empieza en 1 (con 0 da lo mismo que 1).

## Módulo 7, hecho

Lab de 6 tareas (`labs/07-arrays/`) sobre BigMart más un DataFrame `tagged` de 3 filas con
una lista vacía y otra nula, 14 tests y 12 mutaciones. Teoría con el diagrama
`explode-rows.svg`, 8 ejercicios, 8 preguntas de quiz y 5 entradas nuevas en la chuleta.

Medido con Spark: `split("Outlet_Type", " ")` da 2 elementos en las 8523 filas;
`[1]` → `Type1` 5577, `Type2` 928, `Type3` 935, `Store` 1083; `explode` → 17046 filas
(`Supermarket` 7440, `Grocery` y `Store` 1083); `array_contains(..., "Type1")` 5577 true y
2946 false. Palabras de `Item_Type`: 1 → 3260, 2 → 3511, 3 → 1752 (`Fruits and Vegetables`,
`Health and Hygiene`); `explode` sobre ellas → 15538 filas. `tagged`: `explode` 2 filas,
`explode_outer` 4. ANSI: `col[5]` sobre una lista de 2 lanza
`ArrayIndexOutOfBoundsException [INVALID_ARRAY_INDEX]`; `F.get(col, 5)` y
`F.try_element_at(col, F.lit(6))` devuelven `NULL`; `element_at(col, 0)` lanza
`INVALID_INDEX_OF_ZERO`. `explode`/`array_contains` sobre texto:
`AnalysisException [DATATYPE_MISMATCH.UNEXPECTED_INPUT_TYPE]`. `split(v, ".")` sobre
`4.2.0` da `[, , , , , ]`; `split(v, "\\.")` da `[4, 2, 0]`; `split(v, "\\.", 2)` da
`[4, 2.0]`. `size(NULL)` es `NULL`. `array_contains` sobre lista nula da `NULL`.

## Módulo 8, hecho

Lab de 6 tareas (`labs/08-agregaciones/`) sobre BigMart más un DataFrame `books` de 6 filas,
15 tests y 15 mutaciones. Teoría con dos diagramas, `groupby-collapse.svg` y
`pivot-shape.svg`, 8 ejercicios, 8 preguntas de quiz y 6 entradas nuevas en la chuleta.

Medido con Spark: total de `Item_MRP` 1201681.4808 (las notas decían ≈ 1 201 681: correcto);
por `Item_Type` 16 grupos, `Fruits and Vegetables` 178124.081, `Snack Foods` 175433.92,
`Household` 135976.53; media de `Item_MRP` más alta `Household` 149.42. Por
`Outlet_Identifier` 10 grupos: `OUT027` 935 filas, media 139.8, ventas 3453926.05 (la mayor);
`OUT019` 528 filas y 179694.09. `Item_Type` × `Outlet_Size` 64 grupos (48 sin el nulo, 16
con nulo). `count(*)` 8523, `count(Item_Weight)` 7060, `count(Outlet_Size)` 6113,
`countDistinct(Item_Identifier)` 1559; `avg(Item_Weight)` 12.86 frente a `sum/count(*)`
10.65. `collect_set(Outlet_Size)` por `Outlet_Type`: `Supermarket Type1` [High, Medium,
Small] (3722 elementos con `collect_list` porque salta nulos), los otros tres un solo
tamaño; `countDistinct(Outlet_Identifier)` por tipo: 2, 6, 1, 1. Pivot `Item_Type` ×
`Outlet_Size` sin lista: columnas `['Item_Type', 'null', 'High', 'Medium', 'Small']`, 7
jobs; con lista `["Small", "Medium", "High"]`: 3 jobs; `Baking Goods` Small 125.21, Medium
126.18, High 129.2; ninguna celda nula con esos tres valores. Pivot
`Outlet_Type` × `Outlet_Location_Type` sobre ventas sí tiene celdas nulas. Condicional:
`Regular` por tipo suma 2889 (`Dairy` 258 de 682, `Fruits and Vegetables` 577 de 1232);
`Item_MRP > 200` suma 1440. Errores capturados: `agg(F.col("Item_MRP"))` →
`AnalysisException [MISSING_AGGREGATION]` (sugiere `any_value`); `sum("Item_MRP")` de Python
→ `TypeError: unsupported operand type(s) for +: 'int' and 'str'`; `F.count("*")` dentro
de `pivot` → `[INVALID_USAGE_OF_STAR_OR_REGEX] Invalid usage of '*' in Pivot`;
`groupBy(...).show()` → `AttributeError: 'GroupedData' object has no attribute 'show'`;
`F.sum` sobre texto → `CAST_INVALID_INPUT` (ANSI). `groupBy().agg` con AQE: 2 jobs, 3 stages.
Pivot con varias agregaciones nombra `Tier 1_s`, `Tier 1_n`.

## Módulo 9, hecho

Lab de 6 tareas (`labs/09-union-joins/`): tablas de juguete `emp` (6 empleados, `d01, d02, d03,
d03, d05, d06`) y `dept` (5 departamentos, `d01`…`d05`) para `unionByName`, inner, left y anti,
y después BigMart × `outlets.csv`. 17 tests y 21 mutaciones. Teoría con siete diagramas:
`union-by-position.svg` y `join-inner`, `join-left`, `join-right`, `join-anti`, `join-full` y
`join-semi` (los seis generados con un script temporal a partir de las mismas dos tablas; si
hay que retocarlos, es más fácil regenerarlos que editarlos a mano). 8 ejercicios, 8
preguntas de quiz y 6 entradas nuevas en la chuleta (`union / unionAll`, `unionByName`,
`join`, `anti / semi join`, `eqNullSafe`, `broadcast`).

**Dataset nuevo `public/data/outlets.csv`**, generado por `scripts/build-outlets.py` y
documentado en el README: una fila por tienda, las cuatro columnas de tienda copiadas de
BigMart (`Outlet_Size` nulo en OUT010, OUT017 y OUT045) más tres inventadas, `City`,
`Manager` y `Staff` (ciudades indias acordes al Tier; nombres y plantillas ficticios).
**OUT019 no está** (528 ventas) y **OUT099 está pero no vende**. La página dice que las tres
columnas son inventadas. Se reutiliza en los módulos 13 y 15.

Medido con Spark, tablas de juguete: inner 5 filas, left 6, right 6, anti 1 (Jorge, `d06`),
full 7, semi 5; `dept.join(emp, "dept_id", "anti")` → Legal. Con la condición explícita
`emp["dept_id"] == dept["dept_id"]` salen 5 columnas (`dept_id` dos veces, columnas de `emp`
primero) y `select("dept_id")` o `filter` sobre ella dan `AnalysisException
[AMBIGUOUS_REFERENCE]`; `drop("dept_id")` tira las dos, `drop(dept["dept_id"])` una. Por
nombre de columna la clave sale una vez y la primera: `['dept_id', 'emp_id', 'name',
'dept_name']`. `union(emp, emp)` 12 filas, `distinct` 6; `emp.union(dept)` →
`NUM_COLUMNS_MISMATCH`; `unionByName` con columna que falta →
`UNRESOLVED_COLUMN_AMONG_FIELD_NAMES`, con `allowMissingColumns=True` rellena nulos. **ANSI:**
`union` por posición con texto bajo un entero no falla al construirse sino al ejecutar
(`CAST_INVALID_INPUT`, intenta convertir `'d01'` a `BIGINT`); con dos columnas de texto
intercambiadas no hay error y los datos quedan mezclados (así está hecho `new_hires`).
Tipo de join inválido → `UNSUPPORTED_JOIN_TYPE` con la lista completa. `emp.join(dept)` sin
condición no falla: producto cartesiano, 30 filas. Claves repetidas: con `d03` dos veces en
`dept`, inner 7 y left 8. Claves nulas: inner 5, left 7, anti devuelve Jorge y la fila nula;
`eqNullSafe` inner 6.

BigMart × `outlets` por `Outlet_Identifier`: con la tabla entera 19 columnas y `Outlet_Type`
ambigua; con `outlet_info = outlets.select("Outlet_Identifier", "City", "Manager", "Staff")`
15 columnas. inner 7995, left 8523 (528 con `City` nulo, todas OUT019), right 7996, full 8524,
semi 7995, anti desde `sales` 528 (solo OUT019), anti desde `outlets` 1 (OUT099), semi desde
`outlets` 9. Con OUT049 duplicada en `outlet_info`: inner 8925, left 9453. Ventas por ciudad:
Bhopal 3453926.05, Pune 2268122.94, Delhi 2183969.81; 9 ciudades. Unir por las 5 columnas
compartidas da 5585 filas (las 2410 de las tiendas con `Outlet_Size` nulo no cruzan). Jobs:
inner BigMart con broadcast 3 jobs / 4 stages / 4 tasks (`BroadcastHashJoin`); sin broadcast
(`autoBroadcastJoinThreshold = -1`) 4 jobs / 9 stages (`SortMergeJoin`); el inner de las
tablas de juguete sale en 4 jobs / 9 stages. `union` de dos mitades de BigMart: 2 jobs.

## Módulo 10, hecho

Lab de 6 tareas (`labs/10-window-functions/`) sobre BigMart más el DataFrame `daily` de 5
filas para `lag`/`lead`, 15 tests y 21 mutaciones. Teoría con tres diagramas,
`rank-vs-dense.svg` (jugadores `scores` con empates), `window-vs-groupby.svg` y
`window-frame.svg` (marco que crece), 8 ejercicios, 8 preguntas de quiz y 5 entradas nuevas en
la chuleta (`Window + over`, `row_number / rank / dense_rank`, `rowsBetween`, `Agregación con
ventana`, `lag / lead`). La corrección a las notas sobre la suma sin marco está en la teoría
(sección "Qué pasa sin marco").

Medido con Spark: la pareja `Item_Identifier` + `Outlet_Identifier` es única (8523 parejas), y
por eso los tests ordenan siempre por las dos. `row_number` por (`Item_Identifier`,
`Outlet_Identifier`): fila 1 `DRA12`/`OUT010`, fila 8523 `NCZ54`/`OUT049`; ordenando solo por
`Item_Identifier`, la primera es `DRA12`/`OUT017` (orden de llegada). `DRA12` está en 6
tiendas, `NCZ54` en 7, `NCZ53` en 5. `rank`/`dense_rank` por `Item_Identifier` desc: `NCZ54`
1/1, `NCZ53` 8/2, máximos 8518/1559. Por `Item_MRP` desc: `FDS13` y `FDR25` empatan a
266.8884 (rank 1, 1; siguiente rank 3, dense 2); 5938 precios distintos. Suma sin marco con
`orderBy("Item_Type")`: todas las filas de un tipo comparten valor y es acumulado: `Baking
Goods` 81894.74, `Breads` 117273.86 (no 35379.12), `Breakfast` 132870.55, `Canned`
223577.28. Con `rowsBetween(unboundedPreceding, currentRow)` y orden (`Item_Type`,
`Item_Identifier`, `Outlet_Identifier`): `FDA11`/`OUT017` 94.34, `/OUT018` 187.49,
`/OUT027` 282.23, última 1201681.48; con `unboundedFollowing`, 1201681.48 en todas. Top 3 por
tienda por `Item_Outlet_Sales` desc: 30 filas; `OUT027`: `NCE42` 13086.9648, `FDQ19`
12117.56, `FDZ20` 11445.102 (también las 3 ventas máximas globales); `OUT019`: `NCX41`,
`FDY39`, `FDS13`. Hay 1184 empates de ventas dentro de tienda pero ninguno en el top 3
(`rank <= 3` también da 30). Top 3 por `Item_Type` por `Item_MRP`: `row_number` 48, `rank`
48, `dense_rank` 50. Una fila por producto con la venta máxima: 1559; `FDA15` empata a
6474.2392 en `OUT013`, `OUT027` y `OUT035` (578 productos tienen empate en su máximo), con
desempate por `Outlet_Identifier` asc se queda `OUT013`; suma de las mejores ventas
5930366.49. Porcentaje sobre la tienda: 10 totales distintos, `FDA15`/`OUT049` 0.17 % de
2183969.81; máximo `NCK30`/`OUT010` 0.94 %; `OUT027` 3453926.05. `avg(Item_MRP)` por
`Item_Type` con ventana: `Baking Goods` 126.38. `lag` por producto ordenado por tienda: 1559
nulos (uno por producto). `daily` (10, 20, 15, 5, 30): acumulado 10, 30, 45, 50, 80;
`rowsBetween(-2, 0)` 10, 30, 45, 40, 50; `lag` con empates en el orden (`ties`): el marco por
defecto suma 30 en las dos filas del día 1 y `rowsBetween` da 10 y 30.

Errores capturados: `row_number`/`rank`/`lag` sin `orderBy` →
`AnalysisException [WINDOW_FUNCTION_FRAME_NOT_ORDERED]`; `.over("texto")` →
`PySparkTypeError [NOT_EXPECTED_TYPE]`; `F.row_number()` sin `over` →
`[WINDOW_FUNCTION_WITHOUT_OVER_CLAUSE]`; window function dentro de `filter` →
`[WINDOW_FUNCTION_NOT_ALLOWED_IN_CLAUSE]`; `rangeBetween` con orden de texto →
`[DATATYPE_MISMATCH.SPECIFIED_WINDOW_FRAME_UNACCEPTED_TYPE]`. `sum(...).over(partitionBy(...)
.rowsBetween(...))` sin `orderBy` **no** falla (devuelve el valor de la fila). Una window
function dentro de `groupBy().agg()` tampoco falla. Jobs: `row_number` con o sin `partitionBy`,
2 jobs / 3 stages / 3 tasks; sin `partitionBy` el plan trae `Exchange SinglePartition`, con
él `Exchange hashpartitioning(Outlet_Identifier, 200)`. `Window.unboundedPreceding` es
`-9223372036854775808`, `currentRow` 0.

## Módulo 11, hecho

Lab de 6 tareas (`labs/11-udfs/`) sobre BigMart más `spark.range(2_000_000)` para medir
tiempos, 11 tests y 18 mutaciones. Teoría con el diagrama `udf-roundtrip.svg` (JVM frente a
proceso de Python), 8 ejercicios, 8 preguntas de quiz y 2 entradas nuevas en la chuleta
(`udf`, `pandas_udf`). La corrección a las notas (sin tipo de retorno, la UDF devuelve texto)
está en la teoría.

Medido con Spark: `F.udf(square)` sin tipo → columna `string`; ordenada descendente el
"máximo" es `99.9384` → `9987.68379456` (alfabético) en vez de `266.8884` → `71229.41805456`;
`F.sum` sobre ese texto funciona (202478298.30) pero `col + 1` falla con `CAST_INVALID_INPUT`
a `BIGINT`. Con tipo `"double"`, `DoubleType()` o el decorador `@F.udf("double")`, todo bien.
Tipo declarado que no coincide: `"int"` con un `float` **trunca** (62404), `"string"` con un
`int` lo convierte (`'2000'`): no da nulos ni error (Spark 4.2, ruta Arrow). Nulos: `lambda w:
w * 2` sobre `Item_Weight` → `PythonException` con `TypeError: unsupported operand type(s) for
*: 'NoneType' and 'int'`; con `if w is None: return None` quedan 1463 nulos y 7060 valores.
`grams = int(round(w * 1000))` con tipo `"int"`: FDA15 9300, suma 90774975, máximo 21350,
mínimo 4555; coincide en las 8523 filas con `F.round(F.col("Item_Weight") * 1000).cast("int")`
(ningún peso cae en `.5` exacto). Bandas de precio con UDF y con `when`: 2439 / 4644 / 1440,
0 diferencias. `price_band(F.col(...))` sin envolver → `PySparkValueError
[CANNOT_CONVERT_COLUMN_INTO_BOOL]`; `square(F.col(...))` sin envolver **funciona** (es
`Column * Column`, la versión nativa); `square("Item_MRP")` → `TypeError: can't multiply
sequence by non-int of type 'str'`. UDF con dos columnas y con `F.lit` funciona; con un número
suelto → `PySparkTypeError [NOT_EXPECTED_TYPE] Argument col should be Column or str, got
float`. UDF en `filter` funciona (1440) pero el plan pone el `Filter` detrás de
`ArrowEvalPython` y sin `PushedFilters`; el filtro nativo sale como `PushedFilters:
[IsNotNull(Item_MRP), GreaterThanOrEqual(Item_MRP,200.0)]`. Plan de la UDF:
`ArrowEvalPython [price_band(Item_MRP)], ..., 101`; `pandas_udf`: `ArrowEvalPython ..., 200`
(ese 200 es el `evalType` que comprueba el test de la tarea 6); nativa: `CASE WHEN` dentro
del `Project`. Tiempos con 2 M filas (mejor de 3): nativa 0.15 s, `F.udf` 0.80 s, `pandas_udf`
0.54 s. `pandas_udf` deja pasar los nulos (1463). `spark.udf.register("price_band_sql",
price_band, "string")` funciona desde SQL. Una UDF que lanza excepción (`1 / 0`) →
`PythonException` con `ZeroDivisionError`.

**Cuelgue conocido (entorno local, Python 3.14, PySpark 4.2.0, pyarrow 26):** aplicar una
UDF o una `pandas_udf` sobre un DataFrame en `cache()` ya materializado se queda colgado
para siempre: la JVM entra por `ColumnarArrowEvalPython` y espera al worker, y el worker
espera datos (comprobado con `jstack`; workers en `wait_woken`, 0 % CPU). Lo mismo con
`spark.range` y con el CSV. No lo arregla ni pandas 2.3 ni
`spark.sql.execution.arrow.pythonUDF.columnarInput.enabled=false`; sí lo evita
`spark.sql.execution.pythonUDF.arrow.enabled=false` o no cachear antes de la UDF. No se ha
podido comprobar en Colab (Python 3.12). Por eso el lab 11 no usa `cache()`, y el módulo 14
(rendimiento) tiene que tenerlo en cuenta si combina `cache` con UDF. El script de medición
original se quedó 10 minutos colgado en la celda de tiempos por este motivo.

**Entorno:** el worker de Python de Spark arranca con `PYSPARK_PYTHON`; `check-labs.py` y
`mutate-lab.py` ya lo fijan al Python de `.venv`. Para scripts sueltos hay que exportarlo
(`PYSPARK_PYTHON=$PWD/.venv/bin/python`), si no el worker usa el `python3` del sistema y falla
con `ModuleNotFoundError: No module named 'pyarrow'` en cuanto aparece una UDF.

## Módulo 12, siguiente

Diseño en [02-curriculum.md](02-curriculum.md#12-escritura-y-formatos). Las notas
(`material/parte5.md` y `parte6.md`) traen `df.write.format("csv").save(...)`, los modos de
escritura (`append`, `overwrite`, `error`, `ignore`), Parquet y Delta. Errores conocidos de
las notas en [04-source-review.md](04-source-review.md): `save("…/data.csv")` crea una
**carpeta** con archivos `part-`, y en Delta los archivos siguen siendo Parquet. `delta-spark`
4.4.1 está instalado en `.venv` (exige PySpark ≤ 4.2.0). Medir con Spark cuántos archivos
escribe cada formato, qué hace cada modo y el error de `error`/`errorifexists`.

## Datos útiles ya medidos

- Entorno local: Python 3.14, Java 21, PySpark 4.2.0 en `.venv/`. `delta-spark` 4.4.1
  exige PySpark ≤ 4.2.0, por eso está fijada esa versión.
- BigMart: 8523 filas, 12 columnas, 16 tipos de ítem, 1463 pesos nulos, 2410
  `Outlet_Size` nulos, sin filas totalmente duplicadas. `Item_Fat_Content` trae cinco
  variantes: `Low Fat` 5089, `Regular` 2889, `LF` 316, `reg` 117, `low fat` 112.
- Pilotos: 885 registros, 765 sin `code`, 811 sin `number`, 7 sin `dob`.
- Spark optimiza más de lo esperado: ordenar un `spark.range` por `id` o hacerle
  `distinct()` no provoca shuffle. Tenerlo en cuenta al diseñar tests de stages.
