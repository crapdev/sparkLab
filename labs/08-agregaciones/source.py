# ---
# id: 08-agregaciones
# title: Agregaciones
# objective: Resumir datos por grupos con groupBy y agg: sumas, medias, conteos, varias claves, listas con collect_list, tablas pivotadas y agregaciones condicionales.
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

print("Filas:", sales.count(), "· Tipos de producto:", sales.select("Item_Type").distinct().count())

# %% [markdown]
# ## Tarea 1 · Una suma por grupo
#
# `groupBy("columna")` junta las filas que comparten un valor, y `agg(...)` calcula algo
# sobre cada grupo. Las funciones de agregación viven en `F`: `F.sum`, `F.avg`, `F.count`,
# `F.min`, `F.max`. Sin alias, la columna resultante se llama como la fórmula:
# `sum(Item_MRP)`.
#
# Crea `mrp_by_type` con el total de `Item_MRP` por `Item_Type`, en una columna llamada
# `total_mrp`.

# %%
### BEGIN SOLUTION
mrp_by_type = sales.groupBy("Item_Type").agg(F.sum("Item_MRP").alias("total_mrp"))
### END SOLUTION
### BEGIN STARTER
mrp_by_type = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · 16 grupos con las columnas Item_Type y total_mrp",
    lambda: mrp_by_type.count() == 16 and mrp_by_type.columns == ["Item_Type", "total_mrp"],
    'Usa sales.groupBy("Item_Type").agg(F.sum("Item_MRP").alias("total_mrp")).',
)
check(
    "Tarea 1 · Fruits and Vegetables suma 178124.08",
    lambda: round(mrp_by_type.filter(F.col("Item_Type") == "Fruits and Vegetables").first()["total_mrp"], 2) == 178124.08,
    "La agregación es F.sum sobre Item_MRP, no sobre otra columna.",
)
check(
    "Tarea 1 · los 16 totales suman 1201681.48",
    lambda: round(mrp_by_type.agg(F.sum("total_mrp")).first()[0], 2) == 1201681.48,
    "Agrupar no pierde filas: la suma de los grupos tiene que ser el total general.",
)

# %% [markdown]
# Mira el resultado ordenado. El orden en que salen los grupos **no está garantizado**: si
# lo quieres ordenado, pídelo.

# %%
mrp_by_type.orderBy(F.desc("total_mrp")).show(5, truncate=False)
print("Total general:", round(sales.agg(F.sum("Item_MRP")).first()[0], 2))

# %% [markdown]
# ## Tarea 2 · Varias agregaciones a la vez
#
# `agg` acepta tantas agregaciones como quieras, separadas por comas, cada una con su alias.
# `F.count("*")` cuenta filas; `F.round(F.avg(...), 2)` redondea una media.
#
# Crea `by_outlet` con una fila por `Outlet_Identifier` y tres columnas calculadas, en este
# orden:
#
# - `items`: número de filas
# - `avg_mrp`: media de `Item_MRP` redondeada a 2 decimales
# - `total_sales`: suma de `Item_Outlet_Sales` redondeada a 2 decimales

# %%
### BEGIN SOLUTION
by_outlet = sales.groupBy("Outlet_Identifier").agg(
    F.count("*").alias("items"),
    F.round(F.avg("Item_MRP"), 2).alias("avg_mrp"),
    F.round(F.sum("Item_Outlet_Sales"), 2).alias("total_sales"),
)
### END SOLUTION
### BEGIN STARTER
by_outlet = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · 10 tiendas y 4 columnas en orden",
    lambda: by_outlet.count() == 10 and by_outlet.columns == ["Outlet_Identifier", "items", "avg_mrp", "total_sales"],
    "Las tres agregaciones van dentro del mismo agg, cada una con su .alias().",
)
check(
    "Tarea 2 · OUT027 tiene 935 filas y vende 3453926.05",
    lambda: by_outlet.filter(F.col("Outlet_Identifier") == "OUT027").first().asDict()
    == {"Outlet_Identifier": "OUT027", "items": 935, "avg_mrp": 139.8, "total_sales": 3453926.05},
    'items es F.count("*"), avg_mrp es F.round(F.avg("Item_MRP"), 2) y total_sales es F.round(F.sum("Item_Outlet_Sales"), 2).',
)

# %%
by_outlet.orderBy(F.desc("total_sales")).show()

# %% [markdown]
# Dos matices de `count`. `F.count("*")` cuenta todas las filas; `F.count("columna")`
# cuenta solo las filas donde esa columna **no es nula**. Y `F.countDistinct("columna")`
# cuenta valores distintos:

# %%
sales.agg(
    F.count("*").alias("rows"),
    F.count("Item_Weight").alias("rows_with_weight"),
    F.countDistinct("Item_Identifier").alias("distinct_items"),
).show()

# %% [markdown]
# ## Tarea 3 · Agrupar por dos columnas
#
# `groupBy` acepta varias columnas: hay un grupo por cada combinación de valores que
# exista en los datos. Los nulos también forman grupo.
#
# Crea `by_type_size` con la suma de `Item_MRP` por `Item_Type` **y** `Outlet_Size`, en una
# columna `total_mrp`.

# %%
### BEGIN SOLUTION
by_type_size = sales.groupBy("Item_Type", "Outlet_Size").agg(F.sum("Item_MRP").alias("total_mrp"))
### END SOLUTION
### BEGIN STARTER
by_type_size = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · 64 combinaciones y 3 columnas",
    lambda: by_type_size.count() == 64 and by_type_size.columns == ["Item_Type", "Outlet_Size", "total_mrp"],
    'Usa groupBy("Item_Type", "Outlet_Size"): 16 tipos × 4 tamaños (contando el NULL) = 64 grupos.',
)
check(
    "Tarea 3 · los grupos con Outlet_Size nulo están",
    lambda: by_type_size.filter(F.col("Outlet_Size").isNull()).count() == 16,
    "No filtres los nulos: groupBy los trata como un valor más.",
)

# %%
by_type_size.orderBy("Item_Type", "Outlet_Size").show(8, truncate=False)

# %% [markdown]
# ## Tarea 4 · Juntar valores en una lista
#
# `F.collect_list("columna")` junta en un array todos los valores del grupo, repetidos
# incluidos. `F.collect_set` hace lo mismo pero sin repetidos. Las dos ignoran los nulos.
#
# Sobre `sales`, crea `sizes_by_type` con una fila por `Outlet_Type` y una columna `sizes`
# con los valores **distintos** de `Outlet_Size` de cada grupo, ordenados con `F.array_sort`
# para que el resultado sea predecible.

# %%
### BEGIN SOLUTION
sizes_by_type = sales.groupBy("Outlet_Type").agg(F.array_sort(F.collect_set("Outlet_Size")).alias("sizes"))
### END SOLUTION
### BEGIN STARTER
sizes_by_type = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · sizes es un array de strings",
    lambda: dict(sizes_by_type.dtypes).get("sizes") == "array<string>" and sizes_by_type.count() == 4,
    'Usa F.collect_set("Outlet_Size") dentro de agg, y F.array_sort alrededor.',
)
check(
    "Tarea 4 · Supermarket Type1 tiene tres tamaños, ordenados",
    lambda: sizes_by_type.filter(F.col("Outlet_Type") == "Supermarket Type1").first()["sizes"] == ["High", "Medium", "Small"],
    "Con collect_list saldrían 3722 elementos repetidos. Hace falta collect_set y array_sort.",
)

# %%
sizes_by_type.orderBy("Outlet_Type").show(truncate=False)

# %% [markdown]
# La diferencia entre las dos se ve mejor con pocos datos. Un lector que repite un libro:

# %%
books = spark.createDataFrame(
    [("user1", "book1"), ("user1", "book2"), ("user2", "book2"), ("user3", "book1"), ("user3", "book3"), ("user3", "book1")],
    "user STRING, book STRING",
)
books.groupBy("user").agg(F.collect_list("book").alias("all_books"), F.collect_set("book").alias("distinct_books")).orderBy("user").show(truncate=False)

# %% [markdown]
# ## Tarea 5 · Una tabla pivotada
#
# `groupBy(filas).pivot(columnas).agg(valor)` convierte los valores de una columna en
# **columnas nuevas**, como una tabla dinámica. Si le pasas la lista de valores,
# `pivot("Outlet_Size", ["Small", "Medium", "High"])`, eliges cuáles salen y en qué orden, y
# además Spark se ahorra una pasada por los datos para descubrirlos.
#
# Crea `pivoted` con una fila por `Item_Type`, una columna por cada tamaño `Small`,
# `Medium` y `High` (en ese orden) y, en cada celda, la media de `Item_MRP` redondeada a 2
# decimales.

# %%
### BEGIN SOLUTION
pivoted = sales.groupBy("Item_Type").pivot("Outlet_Size", ["Small", "Medium", "High"]).agg(F.round(F.avg("Item_MRP"), 2))
### END SOLUTION
### BEGIN STARTER
pivoted = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · columnas Item_Type, Small, Medium y High",
    lambda: pivoted.columns == ["Item_Type", "Small", "Medium", "High"],
    'Pasa la lista de valores a pivot: pivot("Outlet_Size", ["Small", "Medium", "High"]). Sin ella aparece también una columna null.',
)
check(
    "Tarea 5 · 16 filas y Baking Goods en Small vale 125.21",
    lambda: pivoted.count() == 16 and pivoted.filter(F.col("Item_Type") == "Baking Goods").first()["Small"] == 125.21,
    'La agregación es F.round(F.avg("Item_MRP"), 2).',
)

# %%
pivoted.orderBy("Item_Type").show(5)

# %% [markdown]
# Sin la lista de valores, Spark tiene que recorrer los datos para descubrirlos, y mete los
# nulos como una columna más llamada `null`:

# %%
print(sales.groupBy("Item_Type").pivot("Outlet_Size").agg(F.avg("Item_MRP")).columns)

# %% [markdown]
# ## Tarea 6 · Contar solo lo que cumple una condición
#
# A veces quieres, dentro de cada grupo, contar o sumar solo algunas filas. El truco es
# combinar la agregación con un `when`: `F.count(F.when(condición, 1))` cuenta las filas
# que cumplen la condición, porque `count` ignora los nulos que deja el `when` sin
# `otherwise`. `F.sum(F.when(condición, 1).otherwise(0))` hace lo mismo.
#
# Crea `regular_by_type` con una fila por `Item_Type` y dos columnas: `items`, el total de
# filas del grupo, y `regular_items`, cuántas de ellas tienen `Item_Fat_Content` igual a
# `"Regular"`.

# %%
### BEGIN SOLUTION
regular_by_type = sales.groupBy("Item_Type").agg(
    F.count("*").alias("items"),
    F.count(F.when(F.col("Item_Fat_Content") == "Regular", 1)).alias("regular_items"),
)
### END SOLUTION
### BEGIN STARTER
regular_by_type = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · columnas Item_Type, items y regular_items",
    lambda: regular_by_type.columns == ["Item_Type", "items", "regular_items"] and regular_by_type.count() == 16,
    "Las dos agregaciones van en el mismo agg, con esos alias y en ese orden.",
)
check(
    "Tarea 6 · Dairy tiene 682 filas y 258 Regular",
    lambda: regular_by_type.filter(F.col("Item_Type") == "Dairy").first().asDict() == {"Item_Type": "Dairy", "items": 682, "regular_items": 258},
    'regular_items es F.count(F.when(F.col("Item_Fat_Content") == "Regular", 1)). Si te sale igual que items, falta el when.',
)
check(
    "Tarea 6 · en total hay 2889 Regular",
    lambda: regular_by_type.agg(F.sum("regular_items")).first()[0] == 2889,
    'La condición es exactamente == "Regular". Las variantes reg y low fat no cuentan.',
)

# %%
regular_by_type.orderBy(F.desc("regular_items")).show(5, truncate=False)

# %% [markdown]
# ## Para terminar · dos errores que verás seguro
#
# **1. Pedir una columna que no está en el `groupBy` ni agregada.** Spark no sabe qué valor
# del grupo darte, y lo dice:

# %%
try:
    sales.groupBy("Item_Type").agg(F.col("Item_MRP")).show()
except Exception as error:
    print(type(error).__name__)
    print(str(error).split(";")[0])

# %% [markdown]
# **2. Usar el `sum` de Python en vez de `F.sum`.** Pasa cuando se importa con
# `from pyspark.sql.functions import *` y luego algo vuelve a definir `sum`, o simplemente
# cuando se olvida la `F.`. El error no habla de Spark, y por eso despista:

# %%
try:
    sales.groupBy("Item_Type").agg(sum("Item_MRP"))
except Exception as error:
    print(type(error).__name__)
    print(error)

# %% [summary]
