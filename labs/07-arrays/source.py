# ---
# id: 07-arrays
# title: Arrays
# objective: Trabajar con columnas que contienen listas: crearlas con split, acceder por índice, medirlas con size, desplegarlas con explode y consultarlas con array_contains.
# minutes: 35
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

sales.groupBy("Outlet_Type").count().orderBy("Outlet_Type").show(truncate=False)

# %% [markdown]
# ## Tarea 1 · De texto a lista con `split`
#
# `F.split(columna, separador)` parte un texto por el separador y devuelve un **array**: una
# columna cuyo valor es una lista. `Outlet_Type` tiene valores como `Supermarket Type1`, dos
# palabras separadas por un espacio.
#
# Crea `parts` añadiendo a `sales` la columna `type_parts` con `Outlet_Type` partido por el
# espacio.

# %%
### BEGIN SOLUTION
parts = sales.withColumn("type_parts", F.split("Outlet_Type", " "))
### END SOLUTION
### BEGIN STARTER
parts = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · type_parts es un array de strings",
    lambda: dict(parts.dtypes).get("type_parts") == "array<string>",
    'Usa F.split("Outlet_Type", " "). El resultado tiene que ser una columna nueva llamada type_parts.',
)
check(
    "Tarea 1 · todas las listas tienen 2 elementos",
    lambda: parts.filter(F.size("type_parts") == 2).count() == 8523,
    'El separador es un espacio, " ". Con otro separador la lista tendría un solo elemento.',
)
check(
    "Tarea 1 · Outlet_Type sigue siendo texto",
    lambda: dict(parts.dtypes)["Outlet_Type"] == "string" and len(parts.columns) == 13,
    "Añade type_parts como columna nueva; no sobrescribas Outlet_Type.",
)

# %% [markdown]
# Mira cómo se ve un array en `show()` y en el esquema:

# %%
parts.select("Outlet_Type", "type_parts").distinct().orderBy("Outlet_Type").show(truncate=False)
parts.select("type_parts").printSchema()

# %% [markdown]
# ## Tarea 2 · Un elemento por su posición
#
# Para sacar un elemento de un array se usa el índice entre corchetes, **empezando en 0**:
# `F.col("type_parts")[0]` es la primera palabra y `[1]` la segunda. El resultado es una
# columna normal del tipo de los elementos.
#
# Crea `coded` añadiendo a `parts` la columna `type_code` con la **segunda** palabra de
# `type_parts` (`Type1`, `Type2`, `Type3` o `Store`).

# %%
### BEGIN SOLUTION
coded = parts.withColumn("type_code", F.col("type_parts")[1])
### END SOLUTION
### BEGIN STARTER
coded = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · type_code es string",
    lambda: dict(coded.dtypes).get("type_code") == "string",
    'Usa F.col("type_parts")[1]. Un elemento de un array<string> es un string.',
)
check(
    "Tarea 2 · 5577 filas con Type1 y 1083 con Store",
    lambda: coded.filter(F.col("type_code") == "Type1").count() == 5577 and coded.filter(F.col("type_code") == "Store").count() == 1083,
    "La segunda palabra es el índice 1, no el 2. El índice 0 daría Supermarket o Grocery.",
)

# %% [markdown]
# Pedir un índice que no existe **no devuelve nulo**: en Spark 4 falla al ejecutar, como
# el `cast` imposible. Esta celda pide el sexto elemento de una lista de dos:

# %%
try:
    parts.select(F.col("type_parts")[5]).show(1)
except Exception as error:
    print(type(error).__name__)
    print(str(error).split("\n")[0])

# %% [markdown]
# Si de verdad quieres `NULL` cuando el índice se pasa, el propio mensaje lo dice: `F.get`.

# %%
parts.select(F.get("type_parts", 5).alias("sixth")).show(1)

# %% [markdown]
# ## Tarea 3 · Cuántos elementos tiene la lista
#
# `F.size(array)` devuelve el número de elementos. Combinada con `split`, cuenta palabras.
#
# `Item_Type` tiene nombres de una, dos y tres palabras (`Dairy`, `Soft Drinks`,
# `Fruits and Vegetables`). Crea `counted` añadiendo a `sales` la columna `word_count` con
# el número de palabras de `Item_Type`.

# %%
### BEGIN SOLUTION
counted = sales.withColumn("word_count", F.size(F.split("Item_Type", " ")))
### END SOLUTION
### BEGIN STARTER
counted = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · word_count es un entero",
    lambda: dict(counted.dtypes).get("word_count") == "int",
    'Usa F.size(F.split("Item_Type", " ")). size devuelve un int.',
)
check(
    "Tarea 3 · 3260 de una palabra, 3511 de dos y 1752 de tres",
    lambda: counted.filter(F.col("word_count") == 1).count() == 3260
    and counted.filter(F.col("word_count") == 2).count() == 3511
    and counted.filter(F.col("word_count") == 3).count() == 1752,
    'Parte Item_Type por el espacio, " ", y mide la lista con F.size.',
)

# %%
counted.select("Item_Type", "word_count").distinct().orderBy(F.desc("word_count"), "Item_Type").show(5, truncate=False)

# %% [markdown]
# ## Tarea 4 · Una fila por elemento con `explode`
#
# `F.explode(array)` genera **una fila por cada elemento** de la lista. Las demás columnas
# se repiten en cada fila nueva. Es la forma de pasar de "una fila con una lista" a "una
# fila por valor", que es lo que necesitas para agrupar o contar por elemento.
#
# Crea `exploded` añadiendo a `parts` la columna `type_word` con cada palabra de
# `type_parts` en su propia fila.

# %%
### BEGIN SOLUTION
exploded = parts.withColumn("type_word", F.explode("type_parts"))
### END SOLUTION
### BEGIN STARTER
exploded = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · 17046 filas: el doble",
    lambda: exploded.count() == 17046,
    'Usa F.explode("type_parts"). Cada fila tiene 2 palabras, así que salen 2 filas por cada una de las 8523.',
)
check(
    "Tarea 4 · type_word es string y las demás columnas siguen ahí",
    lambda: dict(exploded.dtypes).get("type_word") == "string" and len(exploded.columns) == 14,
    "explode no quita columnas: añade type_word a las 13 que tenía parts.",
)
check(
    "Tarea 4 · la palabra Supermarket aparece 7440 veces",
    lambda: exploded.filter(F.col("type_word") == "Supermarket").count() == 7440,
    "Supermarket está en 5577 + 928 + 935 filas de sales; tras explode, en una fila por cada una.",
)

# %%
exploded.select("Item_Identifier", "Outlet_Type", "type_word").show(4, truncate=False)
exploded.groupBy("type_word").count().orderBy("type_word").show()

# %% [markdown]
# `explode` solo acepta arrays (y mapas). Sobre la columna de texto original falla con un
# mensaje que conviene reconocer:

# %%
try:
    sales.withColumn("type_word", F.explode("Outlet_Type")).show(1)
except Exception as error:
    print(type(error).__name__)
    print(str(error).split(";")[0])

# %% [markdown]
# ## Tarea 5 · ¿Está en la lista? `array_contains`
#
# `F.array_contains(array, valor)` devuelve `true` si el valor está en la lista y `false` si
# no. Como todas las comparaciones de texto en Spark, distingue mayúsculas.
#
# Crea `flagged` añadiendo a `parts` la columna `type1_flag`: `true` cuando `type_parts`
# contiene `Type1`.

# %%
### BEGIN SOLUTION
flagged = parts.withColumn("type1_flag", F.array_contains("type_parts", "Type1"))
### END SOLUTION
### BEGIN STARTER
flagged = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · type1_flag es boolean",
    lambda: dict(flagged.dtypes).get("type1_flag") == "boolean",
    'Usa F.array_contains("type_parts", "Type1"). Devuelve una columna boolean.',
)
check(
    "Tarea 5 · 5577 true y 2946 false",
    lambda: flagged.filter(F.col("type1_flag")).count() == 5577 and flagged.filter(~F.col("type1_flag")).count() == 2946,
    'El valor buscado es exactamente "Type1", con mayúscula. Con "type1" todo saldría false.',
)

# %% [markdown]
# Como `explode`, `array_contains` exige un array. Aplicarla a `Outlet_Type`, que es texto,
# da un error de tipos:

# %%
try:
    sales.withColumn("type1_flag", F.array_contains("Outlet_Type", "Type1")).show(1)
except Exception as error:
    print(type(error).__name__)
    print(str(error).split(";")[0])

# %% [markdown]
# ## Tarea 6 · Listas vacías y nulas: `explode_outer`
#
# `explode` tiene una consecuencia que a veces no se quiere: una fila cuya lista está
# **vacía** o es **nula** desaparece, porque no hay elementos que desplegar.
# `F.explode_outer` conserva esas filas con un `NULL` en la columna nueva.
#
# El DataFrame `tagged` tiene tres productos: uno con dos etiquetas, uno sin ninguna y uno
# con la lista nula.

# %%
tagged = spark.createDataFrame(
    [(1, ["bio", "local"]), (2, []), (3, None)],
    "product_id INT, tags ARRAY<STRING>",
)
tagged.show()

# %% [markdown]
# Crea `one_per_tag` con `explode`, y `all_products` con `explode_outer`, las dos con la
# columna nueva `tag`.

# %%
### BEGIN SOLUTION
one_per_tag = tagged.withColumn("tag", F.explode("tags"))
all_products = tagged.withColumn("tag", F.explode_outer("tags"))
### END SOLUTION
### BEGIN STARTER
one_per_tag = ...
all_products = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · explode deja 2 filas, solo del producto 1",
    lambda: one_per_tag.count() == 2 and one_per_tag.filter(F.col("product_id") != 1).count() == 0,
    'Usa F.explode("tags"): los productos sin etiquetas desaparecen.',
)
check(
    "Tarea 6 · explode_outer deja 4 filas y conserva los productos 2 y 3",
    lambda: all_products.count() == 4 and all_products.filter(F.col("tag").isNull()).count() == 2,
    'Usa F.explode_outer("tags"): los productos 2 y 3 quedan con tag en NULL.',
)

# %%
one_per_tag.show()
all_products.show()

# %% [markdown]
# ## Para terminar · el separador de `split` es una expresión regular
#
# El segundo argumento de `split` no es un texto literal sino una **regex**, igual que en
# `regexp_replace`. Con un espacio no se nota, pero con un punto o una barra vertical sí:
# `.` significa "cualquier carácter" y `|` significa "o". Hay que escaparlos con `\\`.

# %%
versions = spark.createDataFrame([("4.2.0",), ("3.5.1",)], "version STRING")
versions.select(
    "version",
    F.split("version", ".").alias("wrong"),
    F.split("version", "\\.").alias("right"),
    F.split("version", "\\.")[0].alias("major"),
).show(truncate=False)

# %% [summary]
