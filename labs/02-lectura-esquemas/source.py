# ---
# id: 02-lectura-esquemas
# title: Lectura de datos y esquemas
# objective: Leer archivos CSV y JSON controlando los tipos de las columnas, con esquemas inferidos y con esquemas escritos a mano.
# minutes: 35
# ---

# %% [install]

# %% [helpers]

# %% [session]

# %% [measure]

# %% [data] bigmart_sales.csv drivers.json drivers_multiline.json

# %%
from pyspark.sql.types import DateType, IntegerType, StringType, StructField, StructType

csv_path = dataset_path("bigmart_sales.csv")
drivers_path = dataset_path("drivers.json")
drivers_multiline_path = dataset_path("drivers_multiline.json")

# %% [markdown]
# ## Antes de empezar · qué pasa si no le dices nada a Spark
#
# Lee el CSV sin ninguna opción y mira el resultado. Spark no sabe que la primera fila son
# los nombres de las columnas, así que las llama `_c0`, `_c1`... y trata la cabecera como
# un dato más. Además, todas las columnas son texto.

# %%
raw = spark.read.format("csv").load(csv_path)

print("Filas:", raw.count())
print("Tipos distintos:", {column_type for _, column_type in raw.dtypes})
raw.select("_c0", "_c1", "_c2").show(3)

# %% [markdown]
# ## Tarea 1 · Deja que Spark deduzca el esquema
#
# Lee `csv_path` en `sales_inferred` de forma que:
#
# - la primera fila se use como nombres de columna
# - Spark deduzca el tipo de cada columna

# %%
### BEGIN SOLUTION
sales_inferred = (
    spark.read.format("csv").option("header", True).option("inferSchema", True).load(csv_path)
)
### END SOLUTION
### BEGIN STARTER
sales_inferred = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · 8523 filas y 12 columnas",
    lambda: sales_inferred.count() == 8523 and len(sales_inferred.columns) == 12,
    'Falta .option("header", True): sin ella la cabecera cuenta como una fila más.',
)
check(
    "Tarea 1 · las columnas tienen su nombre",
    lambda: sales_inferred.columns[0] == "Item_Identifier",
    'Con .option("header", True) la primera fila pasa a ser los nombres.',
)
check(
    "Tarea 1 · los tipos se han deducido",
    lambda: dict(sales_inferred.dtypes)["Item_Weight"] == "double"
    and dict(sales_inferred.dtypes)["Outlet_Establishment_Year"] == "int",
    'Falta .option("inferSchema", True): sin ella todas las columnas son string.',
)

# %% [markdown]
# `printSchema()` es la forma más cómoda de ver el esquema. Fíjate en los tipos: te harán
# falta en la tarea siguiente.

# %%
sales_inferred.printSchema()

# %% [markdown]
# ## Tarea 2 · Escribe el esquema como texto DDL
#
# `inferSchema` es cómodo, pero obliga a Spark a recorrer el archivo entero solo para
# adivinar los tipos. Si ya los conoces, es mejor dárselos.
#
# La forma más corta es un **string DDL**: `"nombre TIPO, nombre TIPO, ..."`, igual que en
# un `CREATE TABLE` de SQL.
#
# 1. Completa `SALES_DDL` con las 12 columnas, en el mismo orden que el archivo y con los
#    mismos tipos que dedujo Spark. Los tipos que necesitas son `STRING`, `DOUBLE` e `INT`.
# 2. Lee el CSV en `sales_ddl` usando `.schema(SALES_DDL)` en lugar de `inferSchema`.
#    La opción `header` sigue haciendo falta: sin ella la cabecera se leería como datos.

# %%
### BEGIN SOLUTION
SALES_DDL = """
    Item_Identifier STRING,
    Item_Weight DOUBLE,
    Item_Fat_Content STRING,
    Item_Visibility DOUBLE,
    Item_Type STRING,
    Item_MRP DOUBLE,
    Outlet_Identifier STRING,
    Outlet_Establishment_Year INT,
    Outlet_Size STRING,
    Outlet_Location_Type STRING,
    Outlet_Type STRING,
    Item_Outlet_Sales DOUBLE
"""

sales_ddl = spark.read.format("csv").option("header", True).schema(SALES_DDL).load(csv_path)
### END SOLUTION
### BEGIN STARTER
SALES_DDL = """
    Item_Identifier STRING,
    Item_Weight DOUBLE
"""  # Add the other 10 columns.

sales_ddl = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · el esquema tiene las 12 columnas en orden",
    lambda: sales_ddl.columns == sales_inferred.columns,
    "Revisa SALES_DDL: tienen que estar las 12 columnas, con el mismo nombre y orden que el archivo.",
)
check(
    "Tarea 2 · los tipos coinciden con los deducidos",
    lambda: sales_ddl.dtypes == sales_inferred.dtypes,
    "Algún tipo no coincide. Compara con el printSchema() de la tarea 1: STRING, DOUBLE o INT.",
)
check(
    "Tarea 2 · se leen las 8523 filas",
    lambda: sales_ddl.count() == 8523,
    'Mantén .option("header", True) aunque des el esquema.',
)
check(
    "Tarea 2 · los datos son los mismos",
    lambda: sales_ddl.exceptAll(sales_inferred).count() == 0,
    "Con un tipo equivocado Spark rellena con NULL. Revisa los tipos de SALES_DDL.",
)

# %% [markdown]
# Ahora mide la diferencia. Con el esquema escrito, leer no lanza ningún job: Spark no
# abre el archivo hasta que una acción lo necesita.

# %%
report(
    "header + inferSchema",
    measure(lambda: spark.read.format("csv").option("header", True).option("inferSchema", True).load(csv_path)),
)
report(
    "esquema DDL",
    measure(lambda: spark.read.format("csv").option("header", True).schema(SALES_DDL).load(csv_path)),
)

# %% [markdown]
# ### Dos trampas de los esquemas en CSV
#
# **1. El esquema se aplica por posición, no por nombre.** Spark no comprueba que tus
# nombres coincidan con la cabecera. Si cambias el orden, los datos acaban bajo el nombre
# equivocado y nadie avisa:

# %%
swapped = spark.read.format("csv").option("header", True).schema("Item_Weight STRING, Item_Identifier STRING").load(csv_path)
swapped.show(3)

# %% [markdown]
# **2. Un tipo que no encaja se convierte en `NULL`.** Por defecto Spark no falla: deja
# vacío lo que no puede convertir. Aquí se declara el identificador como número:

# %%
wrong_type = spark.read.format("csv").option("header", True).schema("Item_Identifier INT, Item_Weight DOUBLE").load(csv_path)
wrong_type.show(3)
print("Identificadores nulos:", wrong_type.filter(F.col("Item_Identifier").isNull()).count(), "de", wrong_type.count())

# %% [markdown]
# ## Tarea 3 · Lee un JSON
#
# `drivers.json` tiene un piloto de Fórmula 1 por línea. Ese formato se llama **JSON Lines**
# y es el que Spark espera por defecto.
#
# Lee `drivers_path` en `drivers`. En JSON no hacen falta `header` ni `inferSchema`: los
# nombres van dentro de cada registro y Spark siempre deduce los tipos.

# %%
### BEGIN SOLUTION
drivers = spark.read.format("json").load(drivers_path)
### END SOLUTION
### BEGIN STARTER
drivers = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · 885 pilotos",
    lambda: drivers.count() == 885,
    'Usa spark.read.format("json").load(drivers_path), sin más opciones.',
)
check(
    "Tarea 3 · 8 columnas",
    lambda: len(drivers.columns) == 8 and "driverRef" in drivers.columns,
    "Si solo ves la columna _corrupt_record, quita la opción multiLine: este archivo tiene un registro por línea.",
)
check(
    "Tarea 3 · name es un struct",
    lambda: dict(drivers.dtypes)["name"] == "struct<forename:string,surname:string>",
    "Deja que Spark deduzca el esquema: no le pases uno propio en esta tarea.",
)

# %% [markdown]
# Mira el esquema. Hay tres cosas que conviene notar:
#
# - Las columnas salen en **orden alfabético**, no en el orden del archivo.
# - `name` es un **struct**: una columna que contiene otras dos, `forename` y `surname`.
# - `dob` (fecha de nacimiento) es `string`: Spark no deduce fechas en JSON.

# %%
drivers.printSchema()
drivers.show(3, truncate=False)

# %% [markdown]
# ## Tarea 4 · Saca los campos anidados
#
# Para llegar a un campo dentro de un struct se usa un punto: `"name.forename"`.
#
# Crea `driver_names` con exactamente estas tres columnas, en este orden:
# `driverRef`, `forename` y `surname`.

# %%
### BEGIN SOLUTION
driver_names = drivers.select("driverRef", "name.forename", "name.surname")
### END SOLUTION
### BEGIN STARTER
driver_names = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · columnas driverRef, forename y surname",
    lambda: driver_names.columns == ["driverRef", "forename", "surname"],
    'Usa .select("driverRef", "name.forename", "name.surname").',
)
check(
    "Tarea 4 · siguen los 885 pilotos",
    lambda: driver_names.count() == 885,
    "Solo hay que seleccionar columnas, sin filtrar filas.",
)
check(
    "Tarea 4 · los nombres son correctos",
    lambda: driver_names.filter(F.col("driverRef") == "hamilton").first()["forename"] == "Lewis",
    "forename tiene que salir de name.forename.",
)

# %% [markdown]
# ## Tarea 5 · Un JSON de varias líneas
#
# `drivers_multiline.json` contiene 20 pilotos, pero escritos como un único array con
# sangría, que ocupa muchas líneas. Si lo lees como en la tarea 3, Spark intenta
# interpretar cada línea como un registro completo y no entiende ninguna:

# %%
broken = spark.read.format("json").load(drivers_multiline_path)
print("Columnas:", broken.columns)

# %% [markdown]
# Esa columna `_corrupt_record` es la señal de que Spark no pudo interpretar el archivo.
#
# Lee `drivers_multiline_path` en `drivers_multi` indicándole a Spark que cada registro
# puede ocupar varias líneas, con la opción `multiLine`.

# %%
### BEGIN SOLUTION
drivers_multi = spark.read.format("json").option("multiLine", True).load(drivers_multiline_path)
### END SOLUTION
### BEGIN STARTER
drivers_multi = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · sin registros corruptos",
    lambda: "_corrupt_record" not in drivers_multi.columns,
    'Añade .option("multiLine", True).',
)
check(
    "Tarea 5 · 20 pilotos",
    lambda: drivers_multi.count() == 20,
    "Lee drivers_multiline_path, no drivers_path.",
)
check(
    "Tarea 5 · mismo esquema que el JSON de una línea",
    lambda: drivers_multi.dtypes == drivers.dtypes,
    "Deja que Spark deduzca el esquema.",
)

# %% [markdown]
# ## Tarea 6 · Un esquema con StructType
#
# El string DDL es corto, pero el esquema también se puede construir con objetos:
# `StructType` es la tabla y cada `StructField(nombre, tipo)` es una columna. Es más largo
# de escribir, y a cambio se puede generar y modificar con código.
#
# Completa `DRIVERS_SCHEMA` con estas 8 columnas, en este orden:
#
# | Columna | Tipo |
# |---|---|
# | `driverId` | `IntegerType()` |
# | `driverRef` | `StringType()` |
# | `number` | `IntegerType()` |
# | `code` | `StringType()` |
# | `name` | un `StructType` con `forename` y `surname`, los dos `StringType()` |
# | `dob` | `DateType()` |
# | `nationality` | `StringType()` |
# | `url` | `StringType()` |
#
# Después lee `drivers_path` en `drivers_typed` usando `.schema(DRIVERS_SCHEMA)`.

# %%
### BEGIN SOLUTION
DRIVERS_SCHEMA = StructType(
    [
        StructField("driverId", IntegerType()),
        StructField("driverRef", StringType()),
        StructField("number", IntegerType()),
        StructField("code", StringType()),
        StructField(
            "name",
            StructType(
                [
                    StructField("forename", StringType()),
                    StructField("surname", StringType()),
                ]
            ),
        ),
        StructField("dob", DateType()),
        StructField("nationality", StringType()),
        StructField("url", StringType()),
    ]
)

drivers_typed = spark.read.format("json").schema(DRIVERS_SCHEMA).load(drivers_path)
### END SOLUTION
### BEGIN STARTER
DRIVERS_SCHEMA = StructType(
    [
        StructField("driverId", IntegerType()),
        StructField("driverRef", StringType()),
        # Add number, code, name (a nested StructType), dob, nationality and url.
    ]
)

drivers_typed = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · las 8 columnas en orden",
    lambda: DRIVERS_SCHEMA.fieldNames()
    == ["driverId", "driverRef", "number", "code", "name", "dob", "nationality", "url"],
    "Revisa los nombres y el orden de los StructField.",
)
check(
    "Tarea 6 · driverId y number son enteros",
    lambda: dict(drivers_typed.dtypes)["driverId"] == "int" and dict(drivers_typed.dtypes)["number"] == "int",
    "Usa IntegerType() para driverId y number.",
)
check(
    "Tarea 6 · dob es una fecha",
    lambda: dict(drivers_typed.dtypes)["dob"] == "date",
    "Usa DateType() para dob.",
)
check(
    "Tarea 6 · name sigue siendo un struct",
    lambda: dict(drivers_typed.dtypes)["name"] == "struct<forename:string,surname:string>",
    "name es un StructType con dos StructField: forename y surname.",
)
check(
    "Tarea 6 · se leen los 885 pilotos con sus datos",
    lambda: drivers_typed.count() == 885
    and str(drivers_typed.filter(F.col("driverRef") == "hamilton").first()["dob"]) == "1985-01-07",
    "Lee drivers_path con .schema(DRIVERS_SCHEMA). Si dob sale NULL, revisa el nombre de la columna.",
)

# %% [markdown]
# Compara con el esquema que dedujo Spark en la tarea 3: ahora las columnas están en el
# orden que tú elegiste, los identificadores son `integer` y `dob` es una fecha de verdad.
# Y, como en el CSV, leer con esquema no lanza ningún job.

# %%
drivers_typed.printSchema()

report("JSON con esquema deducido", measure(lambda: spark.read.format("json").load(drivers_path)))
report("JSON con StructType", measure(lambda: spark.read.format("json").schema(DRIVERS_SCHEMA).load(drivers_path)))

# %% [markdown]
# Una diferencia importante con el CSV: en JSON las columnas se emparejan **por nombre**.
# Si en el esquema pides un campo que no existe en el archivo, la columna sale entera
# en `NULL`, sin ningún error:

# %%
spark.read.format("json").schema("driverRef STRING, nickname STRING").load(drivers_path).show(3)

# %% [summary]
