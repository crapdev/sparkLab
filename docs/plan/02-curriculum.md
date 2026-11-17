# 02 · Temario

15 módulos en 5 bloques. Los 13 primeros cubren todo el video; los 2 últimos son
extra. El orden busca que cada módulo use solo lo que ya se vio antes, así que
no siempre coincide con el orden del video.

Las cifras de los labs marcadas con ✔ están comprobadas contra el CSV real. El
resto se confirma al ejecutar PySpark en la fase de construcción.

## Mapa general

| #   | Módulo                      | Bloque                   | Video                                 | Min. aprox. |
| --- | --------------------------- | ------------------------ | ------------------------------------- | ----------- |
| 1   | Fundamentos de Spark        | A · Fundamentos          | 0:00:00 – 0:23:40                     | 35          |
| 2   | Lectura de datos y esquemas | A · Fundamentos          | 0:23:40 – 0:56:55                     | 45          |
| 3   | Seleccionar y filtrar       | B · Transformaciones     | 0:56:55 – 1:20:01                     | 40          |
| 4   | Crear y modificar columnas  | B · Transformaciones     | 1:20:01 – 1:37:05 y 3:32:27 – 3:47:15 | 50          |
| 5   | Ordenar y limpiar           | B · Transformaciones     | 1:37:05 – 2:00:49 y 2:31:01 – 2:45:10 | 50          |
| 6   | Strings y fechas            | B · Transformaciones     | 2:08:56 – 2:31:01                     | 45          |
| 7   | Arrays                      | B · Transformaciones     | 2:45:10 – 3:05:07                     | 35          |
| 8   | Agregaciones                | C · Resumir y combinar   | 3:05:07 – 3:32:27                     | 50          |
| 9   | Union y joins               | C · Resumir y combinar   | 2:00:49 – 2:08:56 y 3:47:15 – 4:13:37 | 60          |
| 10  | Window functions            | C · Resumir y combinar   | 4:13:37 – 4:52:15                     | 60          |
| 11  | UDFs                        | D · Extender y persistir | 4:52:15 – 5:02:13                     | 30          |
| 12  | Escritura y formatos        | D · Extender y persistir | 5:02:13 – 5:33:50                     | 50          |
| 13  | Tablas y Spark SQL          | D · Extender y persistir | 5:33:50 – 5:52:43                     | 45          |
| 14  | Rendimiento por dentro      | E · Rumbo a pro          | Extra                                 | 60          |
| 15  | Proyecto integrador         | E · Rumbo a pro          | Extra                                 | 90          |

## Qué cambió respecto a tu lista de 12

| Cambio                                            | Motivo                                                                                                |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Tu módulo 3 se parte en dos (3 y 4)               | Cubría 40 minutos de video y ocho funciones; era el más cargado                                       |
| `when/otherwise` pasa de agregaciones al módulo 4 | Es una forma de crear una columna, no una agregación. En el 8 reaparece como agregación condicional   |
| `dropna`/`fillna` pasan al módulo 5               | Limpiar nulos va con limpiar duplicados; "nulos y arrays" mezclaba dos temas sin relación             |
| `union`/`unionByName` pasan al módulo 9           | Son la otra forma de combinar DataFrames: apilar frente a cruzar                                      |
| Módulo 14 nuevo                                   | El video no explica particiones, shuffle, planes ni caché, y es lo que más se pregunta en entrevistas |
| Módulo 15 nuevo                                   | Un pipeline completo de principio a fin, para juntar todo                                             |

Lo que **no** entra: Structured Streaming, MLlib, despliegue de clústeres y
Databricks avanzado (Unity Catalog, workflows). Cada uno daría para otro curso.

## Cómo se ve cada módulo

1. **Teoría:** 5 a 10 minutos de lectura, con diagramas y el enlace al minuto
   del video.
2. **Ejercicios:** 5 a 8, mezclando predecir salida y completar código.
3. **Quiz:** 5 a 8 preguntas; se aprueba con 70 %.
4. **Laboratorio:** notebook de Colab con 4 a 6 tareas y tests automáticos.
5. **Errores comunes:** los fallos típicos del tema, incluidos los que el
   instructor comete en vivo.

---

## Bloque A · Fundamentos

### 1. Fundamentos de Spark

- **Objetivo:** entender qué hace Spark por debajo antes de escribir código.
- **Teoría:** motor distribuido y escalado horizontal; driver, executors y
  cluster manager; transformaciones frente a acciones; lazy evaluation y plan
  lógico; Job, Stage y Task; tolerancia a fallos por linaje.
- **Corrección a las notas:** un Job lo dispara cada acción, no cada celda.
- **Sección propia:** "Colab frente a Databricks": crear la `SparkSession`,
  `show()` en vez de `display()`, rutas locales en vez de DBFS.
- **Extra:** transformaciones narrow y wide, y por qué las wide crean un Stage nuevo.
- **Diagramas:** arquitectura del clúster; línea de tiempo de lazy evaluation;
  jerarquía Job → Stage → Task.
- **Ejercicios:** clasificar operaciones en transformación o acción; predecir
  cuántos jobs dispara un fragmento; ordenar los pasos de una ejecución.
- **Lab:** crear la sesión, encadenar transformaciones y comprobar que no se
  ejecuta nada hasta la acción; leer un plan con `explain()`; contar particiones.
  Los tests miden los jobs disparados con el `statusTracker` de Spark.

### 2. Lectura de datos y esquemas

- **Objetivo:** leer CSV y JSON controlando los tipos.
- **Teoría:** `spark.read.format().option().load()`; `header` e `inferSchema` y
  su coste (obliga a leer el archivo dos veces); JSON de una línea frente a
  multilínea; `printSchema()`; esquema con string DDL y con `StructType`.
- **Corrección a las notas:** los esquemas completos con las 12 columnas;
  `header` e `inferSchema` no aplican a JSON.
- **Extra:** leer campos anidados (`name.forename` en los pilotos); qué pasa
  cuando un valor no encaja en el tipo declarado.
- **Diagramas:** con y sin `inferSchema`; anatomía de un `StructField`.
- **Ejercicios:** completar un esquema DDL; predecir el `printSchema()`;
  detectar por qué un JSON multilínea se lee como una sola columna corrupta.
- **Lab:** leer BigMart con esquema inferido y con esquema explícito; leer
  `drivers.json` y `drivers_multiline.json`. Tests: 8523 filas ✔, 12 columnas ✔,
  tipos correctos, 885 pilotos ✔.

---

## Bloque B · Transformaciones

### 3. Seleccionar y filtrar

- **Objetivo:** quedarse con las columnas y filas que interesan.
- **Teoría:** `select` con strings y con `col()`; `alias`; `filter`/`where`;
  operadores `&`, `|`, `~` y por qué necesitan paréntesis; `isNull`, `isin`.
- **Extra:** `between`, `like`, `contains`; `selectExpr`.
- **Diagramas:** recorte por columnas frente a recorte por filas.
- **Errores comunes:** `&&` o `and` en vez de `&`; olvidar paréntesis; comparar
  con un valor mal escrito y obtener cero filas sin error.
- **Lab:** los tres escenarios del video sobre BigMart. Tests: bebidas de menos
  de 10 kg = 166 filas ✔; `Outlet_Size` nulo en Tier 1 o 2 = 1855 filas ✔.

### 4. Crear y modificar columnas

- **Objetivo:** añadir, renombrar, transformar y convertir columnas.
- **Teoría:** `withColumn` para crear y para sobrescribir; `lit`; operaciones
  entre columnas; `withColumnRenamed` frente a `alias`; `regexp_replace`;
  `cast`; `when/otherwise` como `CASE WHEN`.
- **Extra:** `withColumns` para varias a la vez; qué devuelve `cast` cuando no
  puede convertir.
- **Diagramas:** flujo de decisión de un `when` encadenado.
- **Errores comunes:** pasar un string donde hace falta `lit`; condiciones que
  dejan huecos (en el video, un precio de exactamente 100 cae en la rama equivocada).
- **Lab:** normalizar `Item_Fat_Content`, que trae cinco variantes para dos
  valores. Tests: `Low Fat` = 5517 ✔ y `Regular` = 3006 ✔; columna calculada;
  bandera con `when`.

### 5. Ordenar y limpiar

- **Objetivo:** dejar un DataFrame ordenado y sin basura.
- **Teoría:** `sort`/`orderBy`, `asc`/`desc`, varias columnas; `limit`; `drop`;
  `dropDuplicates` y `distinct`; `dropna` con `how` y `subset`; `fillna`.
- **Corrección a las notas:** BigMart no tiene filas totalmente duplicadas, así
  que `dropDuplicates()` sin argumentos no cambia nada; `fillna` con un texto
  solo rellena columnas de texto.
- **Extra:** dónde quedan los nulos al ordenar; `fillna` con un diccionario por columna.
- **Diagramas:** `how="any"` frente a `how="all"` frente a `subset`.
- **Lab:** tests: quitar nulos de `Outlet_Size` deja 6113 filas ✔; `how="any"`
  deja 4650 ✔; 16 tipos de ítem distintos ✔; un DataFrame pequeño con
  duplicados reales para practicar la deduplicación.

### 6. Strings y fechas

- **Objetivo:** limpiar texto y calcular con fechas.
- **Teoría:** `initcap`, `lower`, `upper`; `current_date`, `date_add`,
  `date_sub`, `datediff`, `date_format`.
- **Extra:** `trim`, `concat_ws`, `substring`; `to_date` para convertir texto en
  fecha (lo más usado en datos reales); `year`, `month`.
- **Errores comunes:** `YYYY` en vez de `yyyy`; olvidar que `date_format`
  devuelve texto, no fecha.
- **Diagramas:** el orden de los argumentos de `datediff` sobre una línea de tiempo.
- **Lab:** fechas de nacimiento de los pilotos: convertir `dob` a fecha, calcular
  edad, formatear. Los tests usan una fecha fija, no `current_date`, para que el
  resultado no dependa del día.

### 7. Arrays

- **Objetivo:** trabajar con columnas que contienen listas.
- **Teoría:** `split`, acceso por índice, `explode`, `array_contains`.
- **Extra:** `size`, `explode_outer`; que el segundo argumento de `split` es una
  expresión regular.
- **Diagramas:** una fila con un array que se convierte en varias filas.
- **Errores comunes:** usar `array_contains` sobre una columna de texto.
- **Lab:** partir `Outlet_Type` ("Supermarket Type1") y contar filas antes y
  después del `explode`. Tests sobre conteos y tipos de columna.

---

## Bloque C · Resumir y combinar

### 8. Agregaciones

- **Objetivo:** resumir datos por grupos.
- **Teoría:** `groupBy` + `agg`; `sum`, `avg`, `count`, `min`, `max`; alias;
  varias agregaciones y varias claves; `collect_list`; `pivot`.
- **Extra:** `countDistinct`, `collect_set`; agregación condicional con `when`;
  por qué conviene pasarle a `pivot` la lista de valores.
- **Diagramas:** filas que colapsan en un grupo; forma de una tabla pivotada.
- **Lab:** ventas por tipo de ítem y por tienda. Tests: 16 grupos ✔, total de
  `Item_MRP` ≈ 1 201 681 ✔, columnas del pivot.

### 9. Union y joins

- **Objetivo:** combinar DataFrames sin perder ni duplicar filas por accidente.
- **Teoría:** `union` (por posición, no quita duplicados) y `unionByName`;
  clave de unión; inner, left, right y anti; ambigüedad de columnas.
- **Extra:** full outer y semi; unir por nombre de columna para no duplicarla;
  claves nulas que nunca cruzan; filas que se multiplican con claves repetidas.
- **Diagramas:** uno por tipo de join, con las mismas dos tablas del video
  (`d01`…`d06`) para comparar resultados: inner 5 filas, left 6, right 6, anti 1.
- **Lab:** los DataFrames de ejemplo se crean en el notebook. Tests por número
  de filas y por contenido de cada join.

### 10. Window functions

- **Objetivo:** calcular por fila mirando a las filas vecinas.
- **Teoría:** `Window.orderBy`, `over`; `row_number`, `rank`, `dense_rank`;
  marco de la ventana y suma acumulada con `rowsBetween`.
- **Corrección a las notas:** qué hace realmente una suma con ventana sin marco;
  ejemplos de filas con datos reales (NCZ54 aparece 7 veces ✔).
- **Extra:** `partitionBy` (el índice lo nombra pero las notas no traen código);
  top N por grupo; patrón de deduplicación con `row_number`; `lag` y `lead`.
- **Diagramas:** `row_number` frente a `rank` frente a `dense_rank` con empates;
  marco que crece fila a fila.
- **Lab:** ranking de productos por tienda, top 3 por categoría, ventas
  acumuladas. Tests con orden determinista (se desempata siempre).

---

## Bloque D · Extender y persistir

### 11. UDFs

- **Objetivo:** saber escribir una UDF y, sobre todo, cuándo no hacerlo.
- **Teoría:** función Python → `udf()` → `withColumn`; por qué es lenta (los
  datos viajan entre la JVM y Python).
- **Corrección a las notas:** sin tipo de retorno, una UDF devuelve texto.
- **Extra:** `pandas_udf` vectorizada; reescribir una UDF con funciones nativas.
- **Diagramas:** viaje de los datos JVM ↔ Python.
- **Lab:** escribir una UDF con tipo de retorno, luego la versión nativa
  equivalente y comprobar que dan lo mismo.

### 12. Escritura y formatos

- **Objetivo:** guardar resultados sin destruir datos.
- **Teoría:** `df.write`; modos `append`, `overwrite`, `error`, `ignore`;
  formatos por filas frente a columnares; Parquet; Delta Lake y su log.
- **Corrección a las notas:** `save("data.csv")` crea una carpeta, no un
  archivo; en Delta los archivos siguen siendo Parquet con su metadata.
- **Extra:** por qué salen varios archivos `part-`; `partitionBy` al escribir;
  `header` al escribir CSV.
- **Diagramas:** los cuatro modos de escritura; filas frente a columnas en disco;
  Parquet frente a Delta con `_delta_log`.
- **Lab:** escribir en los cuatro modos y comprobar el resultado en disco; leer
  Parquet de vuelta. Sección opcional de Delta si `delta-spark` resulta estable
  en Colab (ver [03-labs.md](03-labs.md#versiones)).

### 13. Tablas y Spark SQL

- **Objetivo:** usar SQL sobre DataFrames y entender quién es dueño de los datos.
- **Teoría:** `saveAsTable`; tabla managed frente a external y qué borra
  `DROP TABLE`; vistas temporales; `spark.sql()`; mismo rendimiento que la API
  de DataFrames.
- **Extra:** `createOrReplaceTempView` (el `createTempView` del video falla si
  se ejecuta dos veces); comprobar con `explain()` que SQL y DataFrame producen
  el mismo plan.
- **Diagramas:** managed frente a external; SQL y DataFrame confluyendo en el
  mismo plan.
- **Lab:** crear una tabla de cada tipo, borrarlas y comprobar en disco qué
  sobrevive; resolver la misma consulta con SQL y con la API. Test: filtrar
  `Item_Fat_Content = 'LF'` devuelve 316 filas ✔.

---

## Bloque E · Rumbo a pro (extra, no está en el video)

### 14. Rendimiento por dentro

- **Objetivo:** leer un plan de ejecución y saber por qué un job va lento.
- **Teoría:** particiones y shuffle; `repartition` frente a `coalesce`; leer
  `explain()`; Catalyst y AQE en dos párrafos; `cache`/`persist`; broadcast join;
  qué es el skew.
- **Diagramas:** shuffle entre particiones; broadcast join frente a sort-merge join.
- **Lab:** medir particiones, forzar y evitar un shuffle, comprobar en el plan
  que un join pasa a ser broadcast.

### 15. Proyecto integrador

- **Objetivo:** construir un pipeline completo sin guía paso a paso.
- **Contenido:** leer BigMart con esquema explícito → limpiar nulos y
  categorías → enriquecer con columnas calculadas → agregar por tienda y
  categoría → ranking con ventanas → escribir Parquet particionado → consultar
  con SQL.
- **Lab:** un solo notebook largo, con tests por etapa. Sin quiz; se completa al
  pasar todos los tests.
