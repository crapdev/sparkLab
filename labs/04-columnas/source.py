# ---
# id: 04-columnas
# title: Crear y modificar columnas
# objective: Añadir, calcular, renombrar, limpiar y convertir columnas con withColumn, lit, withColumnRenamed, regexp_replace, cast y when/otherwise.
# minutes: 40
# ---

# %% [install]

# %% [helpers]

# %% [session]

# %% [data] bigmart_sales.csv

# %%
sales = (
    spark.read.format("csv")
    .option("header", True)
    .option("inferSchema", True)
    .load(dataset_path("bigmart_sales.csv"))
)

print("Filas:", sales.count(), "· Columnas:", len(sales.columns))

# %% [markdown]
# ## Tarea 1 · Una columna constante con `lit`
#
# `withColumn(nombre, expresión)` devuelve un DataFrame nuevo con una columna más. La
# expresión tiene que ser una **columna de Spark**: un valor suelto de Python, como
# `"new"`, no vale. Para convertirlo en columna se usa `F.lit()` (de *literal*).
#
# Crea `flagged` añadiendo a `sales` una columna `flag` que valga `"new"` en todas las filas.

# %%
### BEGIN SOLUTION
flagged = sales.withColumn("flag", F.lit("new"))
### END SOLUTION
### BEGIN STARTER
flagged = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · existe la columna flag",
    lambda: "flag" in flagged.columns and len(flagged.columns) == 13,
    'Usa sales.withColumn("flag", ...). Tiene que añadir una columna, no sustituir ninguna.',
)
check(
    "Tarea 1 · todas las filas valen new",
    lambda: flagged.filter(F.col("flag") == "new").count() == 8523,
    'El valor constante va envuelto en F.lit("new").',
)

# %% [markdown]
# Mira qué pasa si olvidas `lit`. Esta celda provoca el error a propósito:

# %%
try:
    sales.withColumn("flag", "new")
except Exception as error:
    print(type(error).__name__)
    print(error)

# %% [markdown]
# ## Tarea 2 · Una columna calculada
#
# Las columnas se pueden combinar con los operadores de siempre: `+`, `-`, `*`, `/`. Un
# número suelto sí se acepta en una operación (`F.col("x") * 2`), porque Spark lo convierte
# solo; lo que no acepta es una expresión que sea **únicamente** un valor de Python.
#
# Crea `priced` añadiendo a `sales` la columna `weight_price`, el producto de `Item_Weight`
# por `Item_MRP`.

# %%
### BEGIN SOLUTION
priced = sales.withColumn("weight_price", F.col("Item_Weight") * F.col("Item_MRP"))
### END SOLUTION
### BEGIN STARTER
priced = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · existe weight_price y es double",
    lambda: dict(priced.dtypes).get("weight_price") == "double",
    'Añade la columna con withColumn("weight_price", F.col("Item_Weight") * F.col("Item_MRP")).',
)
check(
    "Tarea 2 · el primer producto es 9.3 × 249.8092",
    lambda: abs(priced.first()["weight_price"] - 2323.22556) < 0.001,
    "Multiplica Item_Weight por Item_MRP, en ese orden o en el otro: el resultado es el mismo.",
)
check(
    "Tarea 2 · hay 1463 resultados nulos",
    lambda: priced.filter(F.col("weight_price").isNull()).count() == 1463,
    "No rellenes ni filtres nada: donde Item_Weight es nulo, el producto también lo es.",
)

# %% [markdown]
# Fíjate en la última comprobación: `Item_Weight` tiene 1463 nulos y `weight_price` también.
# Cualquier operación con un nulo da nulo. No es un fallo, es la regla, y conviene saberla
# antes de sumar o promediar una columna calculada.

# %%
priced.select("Item_Weight", "Item_MRP", "weight_price").show(4)
priced.filter(F.col("Item_Weight").isNull()).select("Item_Weight", "Item_MRP", "weight_price").show(2)

# %% [markdown]
# ## Tarea 3 · Renombrar sin tocar el resto
#
# `alias` renombra dentro de un `select`, así que obliga a enumerar las columnas que quieres
# conservar. Cuando solo quieres cambiar un nombre y dejar todo lo demás igual, es más corto
# `withColumnRenamed(nombre_actual, nombre_nuevo)`.
#
# Crea `renamed` a partir de `sales`, con `Item_Weight` renombrada a `Item_WT` y las demás
# columnas intactas.

# %%
### BEGIN SOLUTION
renamed = sales.withColumnRenamed("Item_Weight", "Item_WT")
### END SOLUTION
### BEGIN STARTER
renamed = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · Item_WT sustituye a Item_Weight",
    lambda: "Item_WT" in renamed.columns and "Item_Weight" not in renamed.columns,
    'Usa sales.withColumnRenamed("Item_Weight", "Item_WT").',
)
check(
    "Tarea 3 · las otras 11 columnas siguen ahí, en su sitio",
    lambda: renamed.columns == ["Item_Identifier", "Item_WT"] + sales.columns[2:],
    "withColumnRenamed no cambia el orden ni quita columnas. Si usaste select, te faltan columnas.",
)

# %% [markdown]
# Un detalle que puede despistar: si el nombre que quieres cambiar **no existe**, Spark no
# da error. Devuelve el DataFrame tal cual, en silencio:

# %%
print(sales.withColumnRenamed("Item_Wieght", "Item_WT").columns == sales.columns)

# %% [markdown]
# ## Tarea 4 · Limpiar una columna con `when` / `otherwise`
#
# `Item_Fat_Content` trae cinco variantes para dos valores:

# %%
sales.groupBy("Item_Fat_Content").count().orderBy("Item_Fat_Content").show()

# %% [markdown]
# `F.when(condición, valor).when(...).otherwise(valor)` es el `CASE WHEN` de SQL: evalúa las
# condiciones en orden y devuelve el valor de la primera que se cumple. Si ninguna se cumple,
# devuelve el `otherwise`.
#
# Crea `clean` a partir de `sales`, **sobrescribiendo** `Item_Fat_Content` (mismo nombre en
# `withColumn`) de forma que:
#
# - `LF` y `low fat` pasen a `Low Fat`
# - `reg` pase a `Regular`
# - el resto se quede como está: `F.col("Item_Fat_Content")` en el `otherwise`
#
# Si prefieres `regexp_replace`, también vale: el test solo mira el resultado.

# %%
### BEGIN SOLUTION
clean = sales.withColumn(
    "Item_Fat_Content",
    F.when(F.col("Item_Fat_Content").isin("LF", "low fat"), "Low Fat")
    .when(F.col("Item_Fat_Content") == "reg", "Regular")
    .otherwise(F.col("Item_Fat_Content")),
)
### END SOLUTION
### BEGIN STARTER
clean = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · solo quedan Low Fat y Regular",
    lambda: sorted(str(row[0]) for row in clean.select("Item_Fat_Content").distinct().collect()) == ["Low Fat", "Regular"],
    "Tienen que desaparecer LF, low fat y reg. Si ves NULL, te falta el otherwise.",
)
check(
    "Tarea 4 · 5517 Low Fat y 3006 Regular",
    lambda: clean.filter(F.col("Item_Fat_Content") == "Low Fat").count() == 5517
    and clean.filter(F.col("Item_Fat_Content") == "Regular").count() == 3006,
    "Low Fat = 5089 + 316 + 112 y Regular = 2889 + 117. Revisa qué variante va a cada valor.",
)
check(
    "Tarea 4 · la columna se sobrescribió, no se añadió",
    lambda: clean.columns == sales.columns,
    'Usa el mismo nombre en withColumn: withColumn("Item_Fat_Content", ...).',
)

# %% [markdown]
# El `otherwise` no es opcional en la práctica. Sin él, las filas que no cumplen ninguna
# condición quedan en `NULL`:

# %%
no_otherwise = sales.withColumn(
    "fat",
    F.when(F.col("Item_Fat_Content").isin("LF", "low fat"), "Low Fat").when(F.col("Item_Fat_Content") == "reg", "Regular"),
)
no_otherwise.groupBy("fat").count().show()

# %% [markdown]
# ## Tarea 5 · Cambiar el tipo con `cast`
#
# `F.col("x").cast("tipo")` convierte una columna a otro tipo. El tipo se puede dar como
# texto (`"string"`, `"int"`, `"double"`) o como objeto (`StringType()`).
#
# Crea `typed` a partir de `sales` con dos cambios:
#
# 1. `Outlet_Establishment_Year` convertida a `string`, sobrescribiendo la columna.
# 2. Una columna nueva, `mrp_int`, con `Item_MRP` convertida a `int`.

# %%
### BEGIN SOLUTION
typed = sales.withColumn("Outlet_Establishment_Year", F.col("Outlet_Establishment_Year").cast("string")).withColumn(
    "mrp_int", F.col("Item_MRP").cast("int")
)
### END SOLUTION
### BEGIN STARTER
typed = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · el año es string",
    lambda: dict(typed.dtypes)["Outlet_Establishment_Year"] == "string",
    'Sobrescribe la columna: withColumn("Outlet_Establishment_Year", F.col("Outlet_Establishment_Year").cast("string")).',
)
check(
    "Tarea 5 · mrp_int es int y trunca los decimales",
    lambda: dict(typed.dtypes).get("mrp_int") == "int" and typed.first()["mrp_int"] == 249,
    'Añade mrp_int con F.col("Item_MRP").cast("int"). 249.8092 pasa a 249: cast trunca, no redondea.',
)
check(
    "Tarea 5 · 13 columnas",
    lambda: len(typed.columns) == 13,
    "El año se sobrescribe (misma columna) y mrp_int se añade (columna nueva).",
)

# %% [markdown]
# ¿Y si el valor no se puede convertir? En Spark 4 el **modo ANSI** viene activado, y un
# `cast` imposible no devuelve nulo: **falla cuando se ejecuta**. Esta celda intenta convertir
# `Item_Identifier` (valores como `FDA15`) a entero:

# %%
try:
    sales.withColumn("id_num", F.col("Item_Identifier").cast("int")).show(3)
except Exception as error:
    print(type(error).__name__)
    print(str(error).split("\n")[0])

# %% [markdown]
# Cuando sabes que puede haber valores malos y prefieres un `NULL` a un error, el propio
# mensaje te da la salida: `try_cast`.

# %%
sales.withColumn("id_num", F.col("Item_Identifier").try_cast("int")).select("Item_Identifier", "id_num").show(3)

# %% [markdown]
# ## Tarea 6 · Un `when` encadenado sin huecos
#
# Crea `banded` añadiendo a `sales` la columna `price_band` según `Item_MRP`:
#
# | Condición | Valor |
# |---|---|
# | menor que 100 | `cheap` |
# | de 100 a menos de 200 | `mid` |
# | 200 o más | `expensive` |
#
# Recuerda que `when` evalúa las condiciones **en orden**: cuando llega a la segunda, las
# filas con menos de 100 ya han salido por la primera, así que basta con `< 200`.

# %%
### BEGIN SOLUTION
banded = sales.withColumn(
    "price_band",
    F.when(F.col("Item_MRP") < 100, "cheap").when(F.col("Item_MRP") < 200, "mid").otherwise("expensive"),
)
### END SOLUTION
### BEGIN STARTER
banded = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · 2439 cheap, 4644 mid y 1440 expensive",
    lambda: banded.filter(F.col("price_band") == "cheap").count() == 2439
    and banded.filter(F.col("price_band") == "mid").count() == 4644
    and banded.filter(F.col("price_band") == "expensive").count() == 1440,
    "Revisa los límites: cheap es < 100, mid es < 200 (el 100 incluido), expensive el resto.",
)
check(
    "Tarea 6 · ninguna fila sin banda",
    lambda: banded.filter(F.col("price_band").isNull()).count() == 0,
    "Hace falta un otherwise para que ninguna fila quede en NULL.",
)
check(
    "Tarea 6 · el precio más alto es expensive",
    lambda: banded.orderBy(F.col("Item_MRP").desc()).first()["price_band"] == "expensive",
    "La última rama, otherwise, tiene que ser expensive.",
)

# %% [markdown]
# ## Para terminar · los huecos entre condiciones
#
# Es fácil escribir dos condiciones que parecen cubrir todo y no lo hacen. `Item_Weight`
# tiene 43 filas que pesan **exactamente** 10, y 1463 nulos. Con `< 10` y `> 10`, ninguna de
# esas filas entra en una rama:

# %%
gaps = sales.withColumn("size", F.when(F.col("Item_Weight") < 10, "light").when(F.col("Item_Weight") > 10, "heavy"))
gaps.groupBy("size").count().show()
print("Exactamente 10:", sales.filter(F.col("Item_Weight") == 10).count())
print("Nulos:         ", sales.filter(F.col("Item_Weight").isNull()).count())

# %% [markdown]
# Los 1506 nulos de `size` son los 43 pesos de exactamente 10 más los 1463 pesos nulos. Dos
# costumbres evitan el problema: usar `<` y `>=` (o `<=` y `>`) para que los límites caigan
# en una rama, y terminar siempre con un `otherwise`, aunque sea para etiquetar lo que no
# encaja con un valor que luego puedas buscar.

# %% [summary]
