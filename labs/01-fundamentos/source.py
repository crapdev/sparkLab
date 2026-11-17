# ---
# id: 01-fundamentos
# title: Fundamentos de Spark
# objective: Crear una SparkSession y comprobar con mediciones reales cómo funcionan la evaluación perezosa, los jobs, los stages y las tasks.
# minutes: 35
# ---

# %% [install]

# %% [helpers]

# %% [markdown]
# ## Tarea 1 · Crea tu SparkSession
#
# La `SparkSession` es la puerta de entrada a Spark: con ella lees datos, creas DataFrames
# y lanzas consultas. En Databricks ya viene creada con el nombre `spark`; aquí la creas tú.
#
# Crea una sesión que:
#
# - se ejecute en modo local usando todos los núcleos disponibles: `local[*]`
# - tenga como nombre de aplicación `lab-01-fundamentos`
#
# La receta es `SparkSession.builder.master(...).appName(...).getOrCreate()`.

# %%
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

### BEGIN SOLUTION
spark = SparkSession.builder.master("local[*]").appName("lab-01-fundamentos").getOrCreate()
### END SOLUTION
### BEGIN STARTER
spark = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · spark es una SparkSession",
    lambda: isinstance(spark, SparkSession),
    "Termina la cadena con .getOrCreate(); sin eso solo tienes el builder.",
)
check(
    "Tarea 1 · se ejecuta en modo local",
    lambda: spark.sparkContext.master.startswith("local"),
    'Usa .master("local[*]") antes de .getOrCreate().',
)
check(
    "Tarea 1 · la sesión funciona",
    lambda: spark.range(5).count() == 5,
    "La sesión no pudo ejecutar un job sencillo. Vuelve a ejecutar la celda de preparación.",
)

# %% [markdown]
# ### Una herramienta para mirar dentro de Spark
#
# Las dos celdas siguientes ya están escritas:
#
# 1. La primera ajusta la sesión para este laboratorio. Desactiva temporalmente **AQE** (Adaptive Query
#    Execution), una optimización que puede repartir una acción en varios jobs. Al final del
#    laboratorio la vuelves a activar para ver la diferencia.
# 2. La segunda define `measure(action)`, que ejecuta una función y te dice cuántos **jobs**, **stages**
#    y **tasks** lanzó Spark. Es el equivalente a mirar la pestaña "Spark Jobs" de Databricks.

# %%
spark.sparkContext.setLogLevel("ERROR")
spark.conf.set("spark.sql.adaptive.enabled", "false")
spark.conf.set("spark.sql.shuffle.partitions", "4")

# %% [measure]

# %% [markdown]
# ## Tarea 2 · Un pipeline perezoso
#
# Las **transformaciones** (`filter`, `withColumn`, `select`...) no ejecutan nada: solo
# añaden pasos a un plan. Spark no toca los datos hasta que llega una **acción**.
#
# Completa `build_pipeline` para que, partiendo de los números del 1 al 1000, devuelva un
# DataFrame con:
#
# - solo los múltiplos de 7
# - una columna nueva `squared` con el cuadrado de `id`
#
# La función **no debe ejecutar ninguna acción**: nada de `show()`, `count()` ni `collect()`
# dentro. El test mide cuántos jobs dispara, y tienen que ser cero.

# %%
def build_pipeline():
    """Return the multiples of 7 between 1 and 1000 with their square. No actions."""
    numbers = spark.range(1, 1001)  # One column named "id".
    ### BEGIN SOLUTION
    return numbers.filter(F.col("id") % 7 == 0).withColumn("squared", F.col("id") * F.col("id"))
    ### END SOLUTION
    ### BEGIN STARTER
    return ...
    ### END STARTER


# %% [test]
check(
    "Tarea 2 · devuelve un DataFrame",
    lambda: isinstance(build_pipeline(), DataFrame),
    "La función tiene que devolver el DataFrame transformado, no el resultado de una acción.",
)
check(
    "Tarea 2 · no dispara ningún job",
    lambda: measure(build_pipeline)["jobs"] == 0,
    "Dentro de la función hay una acción (show, count, collect...). Quítala.",
)
check(
    "Tarea 2 · columnas id y squared",
    lambda: build_pipeline().columns == ["id", "squared"],
    'Añade la columna con .withColumn("squared", ...) y no elimines "id".',
)
check(
    "Tarea 2 · quedan los múltiplos de 7",
    lambda: build_pipeline().count() == 142,
    'Filtra con F.col("id") % 7 == 0. Entre 1 y 1000 hay 142 múltiplos de 7.',
)
check(
    "Tarea 2 · squared es el cuadrado de id",
    lambda: build_pipeline().filter(F.col("id") == 7).first()["squared"] == 49,
    'El cuadrado es F.col("id") * F.col("id").',
)

# %% [markdown]
# Fíjate en lo que acaba de pasar: construir el pipeline dispara **0 jobs**. El plan existe,
# pero Spark todavía no ha calculado nada. Puedes ver ese plan sin ejecutarlo:

# %%
build_pipeline().explain()

# %% [markdown]
# ## Tarea 3 · ¿Transformación o acción?
#
# Una **transformación** devuelve otro DataFrame y no ejecuta nada.
# Una **acción** obliga a Spark a calcular: devuelve un resultado a Python o lo muestra.
#
# De la lista `OPERATIONS`, escribe en `actions` solo las que son acciones.

# %%
OPERATIONS = ["select", "filter", "count", "withColumn", "show", "collect", "groupBy", "take", "orderBy", "first"]

### BEGIN SOLUTION
actions = ["count", "show", "collect", "take", "first"]
### END SOLUTION
### BEGIN STARTER
actions = []  # For example: ["count", ...]
### END STARTER

# %% [test]
EXPECTED_ACTIONS = {"count", "show", "collect", "take", "first"}

check(
    "Tarea 3 · están todas las acciones",
    lambda: EXPECTED_ACTIONS <= set(actions),
    "Faltan acciones. Hay 5: son las que devuelven un número, filas de Python o imprimen algo.",
)
check(
    "Tarea 3 · no hay transformaciones en la lista",
    lambda: set(actions) <= EXPECTED_ACTIONS,
    "Sobra alguna. Si la operación devuelve otro DataFrame, es una transformación.",
)

# %% [markdown]
# No hace falta creerlo: se puede medir. La siguiente celda aplica cada operación al
# pipeline y cuenta los jobs. Las transformaciones dan 0; las acciones, al menos 1.

# %%
pipeline = build_pipeline()

demo_operations = {
    "select": lambda: pipeline.select("id"),
    "filter": lambda: pipeline.filter(F.col("id") > 500),
    "withColumn": lambda: pipeline.withColumn("double", F.col("id") * 2),
    "groupBy + count()": lambda: pipeline.groupBy("id").count(),
    "orderBy": lambda: pipeline.orderBy("squared"),
    "count": lambda: pipeline.count(),
    "collect": lambda: pipeline.collect(),
    "take(3)": lambda: pipeline.take(3),
    "first": lambda: pipeline.first(),
}
for label, operation in demo_operations.items():
    report(label, measure(operation))

# %% [markdown]
# ## Tarea 4 · Acciones que devuelven resultados
#
# Usa acciones sobre `pipeline` para obtener:
#
# - `total`: cuántas filas tiene
# - `first_three`: una lista con 3 filas cualesquiera
# - `biggest`: el valor más grande de la columna `squared`
#
# Para `biggest` puedes agregar con `pipeline.agg(F.max("squared"))`. Eso devuelve un
# DataFrame de una fila y una columna: necesitas una acción para sacar el número.

# %%
### BEGIN SOLUTION
total = pipeline.count()
first_three = pipeline.take(3)
biggest = pipeline.agg(F.max("squared")).first()[0]
### END SOLUTION
### BEGIN STARTER
total = ...
first_three = ...
biggest = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · total de filas",
    lambda: total == 142,
    "Usa .count(). Tiene que dar 142.",
)
check(
    "Tarea 4 · first_three tiene 3 filas",
    lambda: isinstance(first_three, list) and len(first_three) == 3 and all(row["id"] % 7 == 0 for row in first_three),
    "Usa .take(3): devuelve una lista de Python con 3 filas.",
)
check(
    "Tarea 4 · el cuadrado más grande",
    lambda: biggest == 988036,
    "Tras .agg(...) usa .first()[0] para sacar el valor. El mayor múltiplo de 7 es 994.",
)

# %% [markdown]
# ## Tarea 5 · `limit` no es `take`, y otras formas de traer filas
#
# Hay varias acciones para sacar filas de Spark, y una transformación que se les parece:
#
# - `limit(n)` es una **transformación**: devuelve otro DataFrame de como mucho `n` filas.
# - `head(n)` es una **acción**: devuelve una lista de `n` filas, igual que `take(n)`.
# - `toPandas()` es una **acción**: devuelve un DataFrame de **pandas** con todas las filas.
#
# Sobre `pipeline`, crea:
#
# - `top_five`: un DataFrame de Spark con las 5 primeras filas, usando `limit`
# - `five_rows`: una lista de Python con 5 filas, usando `head`
# - `as_pandas`: el pipeline completo convertido a pandas

# %%
### BEGIN SOLUTION
top_five = pipeline.limit(5)
five_rows = pipeline.head(5)
as_pandas = pipeline.toPandas()
### END SOLUTION
### BEGIN STARTER
top_five = ...
five_rows = ...
as_pandas = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · top_five sigue siendo un DataFrame de Spark",
    lambda: isinstance(top_five, DataFrame) and top_five.count() == 5,
    "Usa pipeline.limit(5): devuelve un DataFrame, no una lista.",
)
check(
    "Tarea 5 · limit no lanza ningún job",
    lambda: measure(lambda: pipeline.limit(5))["jobs"] == 0,
    "limit es una transformación. Si mides jobs, es que has usado una acción.",
)
check(
    "Tarea 5 · five_rows es una lista de 5 Row",
    lambda: isinstance(five_rows, list) and len(five_rows) == 5 and five_rows[0]["id"] == 7,
    "Usa pipeline.head(5). Devuelve una lista de Python, como take(5).",
)
check(
    "Tarea 5 · as_pandas tiene 142 filas y 2 columnas",
    lambda: type(as_pandas).__module__.startswith("pandas") and as_pandas.shape == (142, 2),
    "Usa pipeline.toPandas(), sin filtrar ni limitar antes.",
)

# %% [markdown]
# Mide la diferencia. `limit(5)` no lanza nada; `limit(5).show()` lanza el job de `show`.
# Y fíjate en las tasks: las acciones que traen pocas filas leen una sola partición,
# mientras que `collect()` y `toPandas()` tienen que tocar las 8.

# %%
report("limit(5)", measure(lambda: pipeline.limit(5)))
report("limit(5).show()", measure(lambda: pipeline.limit(5).show()))
report("take(5)", measure(lambda: pipeline.take(5)))
report("head(5)", measure(lambda: pipeline.head(5)))
report("collect()", measure(pipeline.collect))
report("toPandas()", measure(pipeline.toPandas))

# %% [markdown]
# `collect()` y `toPandas()` traen **todas** las filas al driver, que es un solo proceso con
# una memoria limitada. Con 142 filas da igual; con cientos de millones, el driver se queda
# sin memoria y la sesión muere. Antes de llamarlas, reduce con `filter`, una agregación o
# `limit`. Para mirar, `show()` o `take(n)` bastan.
#
# Escribir en disco también es una acción, aunque no devuelva nada a Python. Esta celda
# guarda el pipeline como CSV en una carpeta temporal y mide lo que cuesta:

# %%
import os
import tempfile

output_dir = os.path.join(tempfile.mkdtemp(), "multiples")
report("write.csv()", measure(lambda: pipeline.write.mode("overwrite").csv(output_dir)))
print("Archivos escritos:", len([name for name in os.listdir(output_dir) if name.startswith("part-")]))

# %% [markdown]
# Un archivo por partición: 8. Spark escribe en paralelo, igual que lee. Lo verás a fondo
# en el módulo de escritura y formatos.

# %% [markdown]
# ## Tarea 6 · Narrow, wide, stages y tasks
#
# - Una transformación **narrow** (`filter`, `withColumn`, `select`) procesa cada partición
#   por separado. No hay que mover datos entre particiones.
# - Una transformación **wide** (`groupBy`, `orderBy`, `join`) necesita juntar filas que
#   están en particiones distintas. Ese movimiento se llama **shuffle** y parte el job en
#   un **stage** más.
# - Cada stage lanza una **task** por partición.
#
# Partiendo de `numbers`, que tiene **4 particiones**, crea:
#
# - `narrow_df`: `numbers` con una columna nueva `is_even`, que es `True` cuando `id` es par
# - `wide_df`: cuántas filas hay de cada valor de `is_even`, con `groupBy` y `count()`

# %%
numbers = spark.range(0, 1000, numPartitions=4)

### BEGIN SOLUTION
narrow_df = numbers.withColumn("is_even", F.col("id") % 2 == 0)
wide_df = narrow_df.groupBy("is_even").count()
### END SOLUTION
### BEGIN STARTER
narrow_df = ...
wide_df = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · narrow_df tiene id e is_even",
    lambda: narrow_df.columns == ["id", "is_even"],
    'Usa .withColumn("is_even", F.col("id") % 2 == 0).',
)
check(
    "Tarea 6 · narrow_df se resuelve en 1 stage",
    lambda: measure(narrow_df.collect)["stages"] == 1,
    "narrow_df solo debe usar transformaciones narrow; nada de groupBy u orderBy.",
)
check(
    "Tarea 6 · una task por partición",
    lambda: measure(narrow_df.collect)["tasks"] == 4,
    "Parte de `numbers` sin cambiar su número de particiones.",
)
check(
    "Tarea 6 · wide_df cuenta pares e impares",
    lambda: {row["is_even"]: row["count"] for row in wide_df.collect()} == {True: 500, False: 500},
    'Agrupa con .groupBy("is_even") y cuenta con .count().',
)
check(
    "Tarea 6 · el shuffle añade un stage",
    lambda: measure(wide_df.collect)["stages"] == 2,
    "wide_df necesita un groupBy: es lo que provoca el shuffle y el segundo stage.",
)

# %%
report("narrow_df.collect()", measure(narrow_df.collect))
report("wide_df.collect()", measure(wide_df.collect))

# %% [markdown]
# Lee las dos líneas: la versión narrow usa 1 stage con 4 tasks, una por partición. La
# versión wide usa 2 stages: el primero lee las 4 particiones y el segundo procesa las 4
# particiones que salen del shuffle (las fijamos en 4 al configurar la sesión).

# %% [data] bigmart_sales.csv

# %% [markdown]
# ## Tarea 7 · Leer un archivo también lanza jobs
#
# Justo después de `spark.read...load()` suele aparecer un job aunque no hayas llamado
# a ninguna acción. No es una contradicción: para conocer los **nombres** de las columnas
# (`header`) y sus **tipos** (`inferSchema`), Spark tiene que abrir el archivo.
#
# Lee `bigmart_sales.csv` en un DataFrame llamado `sales`:
#
# - la primera fila contiene los nombres de las columnas
# - Spark debe deducir el tipo de cada columna
#
# La receta es `spark.read.format("csv").option(...).option(...).load(csv_path)`.

# %%
csv_path = dataset_path("bigmart_sales.csv")

### BEGIN SOLUTION
sales = spark.read.format("csv").option("header", True).option("inferSchema", True).load(csv_path)
### END SOLUTION
### BEGIN STARTER
sales = ...
### END STARTER

# %% [test]
check(
    "Tarea 7 · 8523 filas",
    lambda: sales.count() == 8523,
    'Si te sale 8524, falta .option("header", True): la cabecera se contó como dato.',
)
check(
    "Tarea 7 · 12 columnas con su nombre",
    lambda: len(sales.columns) == 12 and sales.columns[0] == "Item_Identifier",
    'Sin .option("header", True) las columnas se llaman _c0, _c1...',
)
check(
    "Tarea 7 · Item_Weight es numérica",
    lambda: dict(sales.dtypes)["Item_Weight"] == "double",
    'Sin .option("inferSchema", True) todas las columnas son string.',
)

# %% [markdown]
# Ahora mide cuánto cuesta cada forma de leer. Cuantas más cosas tiene que averiguar Spark
# por su cuenta, más veces abre el archivo. Si tú le das el esquema, no necesita abrirlo
# hasta que haya una acción. Eso es el módulo 2.

# %%
reader = spark.read.format("csv")

report("solo header", measure(lambda: reader.option("header", True).load(csv_path)))
report(
    "header + inferSchema",
    measure(lambda: reader.option("header", True).option("inferSchema", True).load(csv_path)),
)
report(
    "con esquema explícito",
    measure(lambda: reader.option("header", True).schema(sales.schema).load(csv_path)),
)

# %% [markdown]
# ## Para terminar · una acción puede ser más de un job
#
# Se suele decir "una acción, un job". Es una buena primera aproximación, pero no es exacta.
# Vuelve a activar AQE, que es como viene Spark por defecto, y mide el mismo `count()`:

# %%
spark.conf.set("spark.sql.adaptive.enabled", "false")
report("count() sin AQE", measure(pipeline.count))

spark.conf.set("spark.sql.adaptive.enabled", "true")
report("count() con AQE", measure(pipeline.count))

# %% [markdown]
# Con AQE, Spark ejecuta la consulta por partes y decide el siguiente paso con lo que ha
# aprendido del anterior; cada parte puede aparecer como un job distinto. La idea correcta
# es: **cada acción dispara al menos un job**. Por eso una sola celda de un notebook puede
# generar varios.

# %% [summary]
