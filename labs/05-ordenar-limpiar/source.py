# ---
# id: 05-ordenar-limpiar
# title: Ordenar y limpiar
# objective: Dejar un DataFrame ordenado y sin basura: sort, limit, drop, duplicados con dropDuplicates y distinct, y nulos con dropna y fillna.
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
# ## Tarea 1 · Ordenar
#
# `sort` y `orderBy` son la misma función. Reciben una o varias columnas y, para cada una,
# el sentido: `F.col("x").asc()` (el de por defecto) o `F.col("x").desc()`.
#
# Crea dos DataFrames a partir de `sales`:
#
# - `heaviest`: ordenado por `Item_Weight` de mayor a menor
# - `by_two`: ordenado por `Item_Weight` de mayor a menor y, a igual peso, por
#   `Item_Visibility` de menor a mayor

# %%
### BEGIN SOLUTION
heaviest = sales.sort(F.col("Item_Weight").desc())
by_two = sales.sort(F.col("Item_Weight").desc(), F.col("Item_Visibility").asc())
### END SOLUTION
### BEGIN STARTER
heaviest = ...
by_two = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · heaviest empieza por el peso máximo, 21.35",
    lambda: heaviest.first()["Item_Weight"] == 21.35,
    'Usa sales.sort(F.col("Item_Weight").desc()). Si la primera fila tiene el peso en NULL, has ordenado ascendente.',
)
check(
    "Tarea 1 · heaviest conserva las 8523 filas y 12 columnas",
    lambda: heaviest.count() == 8523 and len(heaviest.columns) == 12,
    "Ordenar no quita filas ni columnas.",
)
check(
    "Tarea 1 · by_two desempata por visibilidad ascendente",
    lambda: by_two.first()["Item_Weight"] == 21.35 and by_two.first()["Item_Visibility"] == 0.068765205,
    'La segunda clave es F.col("Item_Visibility").asc(). Entre los 7 productos de 21.35, el de menor visibilidad tiene 0.068765205.',
)

# %% [markdown]
# Mira dónde quedan los nulos. `Item_Weight` tiene 1463 valores nulos: en orden ascendente
# salen **primero** y en descendente salen **al final**. Si no es lo que quieres, hay
# variantes explícitas: `asc_nulls_last()` y `desc_nulls_first()`.

# %%
sales.sort(F.col("Item_Weight").asc()).select("Item_Identifier", "Item_Weight").show(3)
sales.sort(F.col("Item_Weight").asc_nulls_last()).select("Item_Identifier", "Item_Weight").show(3)

# %% [markdown]
# ## Tarea 2 · Los N primeros
#
# `limit(n)` recorta un DataFrame a `n` filas. Combinado con `sort`, da "los N mayores" o
# "los N menores". Sin `sort`, las filas que devuelve son las que primero encuentra, sin
# ninguna garantía.
#
# Crea `top_prices` con los **3 productos más caros** según `Item_MRP`.

# %%
### BEGIN SOLUTION
top_prices = sales.sort(F.col("Item_MRP").desc()).limit(3)
### END SOLUTION
### BEGIN STARTER
top_prices = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · exactamente 3 filas",
    lambda: top_prices.count() == 3,
    "Termina con .limit(3).",
)
check(
    "Tarea 2 · son los precios más altos",
    lambda: [row["Item_MRP"] for row in top_prices.collect()] == [266.8884, 266.8884, 266.6884],
    'Ordena antes de recortar: sales.sort(F.col("Item_MRP").desc()).limit(3). El precio máximo es 266.8884.',
)

# %%
top_prices.select("Item_Identifier", "Item_Type", "Item_MRP").show()

# %% [markdown]
# ## Tarea 3 · Quitar columnas
#
# `drop` elimina una o varias columnas, separadas por comas. Es el contrario de `select`:
# en vez de decir cuáles quieres, dices cuáles sobran.
#
# Crea `slim` a partir de `sales` sin las columnas `Item_Visibility` e `Item_Type`.

# %%
### BEGIN SOLUTION
slim = sales.drop("Item_Visibility", "Item_Type")
### END SOLUTION
### BEGIN STARTER
slim = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · quedan 10 columnas, sin las dos indicadas",
    lambda: len(slim.columns) == 10 and "Item_Visibility" not in slim.columns and "Item_Type" not in slim.columns,
    'Usa sales.drop("Item_Visibility", "Item_Type"), las dos en la misma llamada.',
)
check(
    "Tarea 3 · el resto sigue en su orden",
    lambda: slim.columns == [column for column in sales.columns if column not in ("Item_Visibility", "Item_Type")],
    "drop no reordena las columnas que quedan. Si usaste select, revisa el orden.",
)

# %% [markdown]
# Como `withColumnRenamed`, `drop` **no avisa** si la columna no existe: devuelve el
# DataFrame tal cual. Comprueba `df.columns` después de un `drop` importante.

# %%
print(len(sales.drop("Item_Visibilty").columns))  # Typo on purpose.

# %% [markdown]
# ## Tarea 4 · Duplicados
#
# BigMart no tiene filas totalmente repetidas, así que para practicar hay un DataFrame
# pequeño de pedidos con duplicados de verdad:

# %%
orders = spark.createDataFrame(
    [
        (1, "ana", "Dairy", 12.5),
        (2, "luis", "Meat", 30.0),
        (2, "luis", "Meat", 30.0),
        (3, "ana", "Dairy", 8.0),
        (4, "marta", "Snack Foods", 5.5),
        (4, "marta", "Snack Foods", 5.5),
        (4, "marta", "Snack Foods", 5.5),
        (5, "luis", "Dairy", 12.5),
    ],
    "order_id INT, customer STRING, item_type STRING, amount DOUBLE",
)
orders.show()

# %% [markdown]
# - `dropDuplicates()` sin argumentos quita las filas en las que **todas** las columnas
#   coinciden. `distinct()` hace exactamente lo mismo.
# - `dropDuplicates(["col1", "col2"])` compara solo esas columnas y se queda con **una**
#   fila por combinación, con el resto de columnas de alguna de las repetidas.
#
# Crea:
#
# - `unique_orders`: `orders` sin filas repetidas
# - `one_per_customer`: una sola fila por `customer`
# - `item_types`: un DataFrame con una sola columna, `Item_Type`, y los valores distintos
#   que hay en `sales`

# %%
### BEGIN SOLUTION
unique_orders = orders.dropDuplicates()
one_per_customer = orders.dropDuplicates(["customer"])
item_types = sales.select("Item_Type").distinct()
### END SOLUTION
### BEGIN STARTER
unique_orders = ...
one_per_customer = ...
item_types = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · unique_orders tiene 5 pedidos",
    lambda: unique_orders.count() == 5 and unique_orders.columns == orders.columns,
    "Usa orders.dropDuplicates() o orders.distinct(), sin argumentos. Hay 3 filas repetidas.",
)
check(
    "Tarea 4 · one_per_customer tiene 3 filas, una por cliente",
    lambda: one_per_customer.count() == 3
    and sorted(row["customer"] for row in one_per_customer.collect()) == ["ana", "luis", "marta"],
    'Usa orders.dropDuplicates(["customer"]). Hay 3 clientes.',
)
check(
    "Tarea 4 · item_types tiene 16 tipos en una columna",
    lambda: item_types.columns == ["Item_Type"] and item_types.count() == 16,
    'Selecciona primero la columna y luego quita repetidos: sales.select("Item_Type").distinct().',
)

# %% [markdown]
# Un aviso sobre `dropDuplicates` con subset: Spark se queda con **una** de las filas
# repetidas, pero **no garantiza cuál**. Si necesitas la más reciente o la más cara,
# el módulo de window functions enseña cómo elegirla. Mira cuál ha sobrevivido aquí:

# %%
one_per_customer.sort("customer").show()

# %% [markdown]
# ## Tarea 5 · Quitar filas con nulos
#
# `dropna` elimina filas con nulos. Tiene dos mandos:
#
# - `how`: `"any"` (por defecto) quita la fila si **alguna** columna es nula; `"all"` solo
#   si **todas** lo son.
# - `subset`: la lista de columnas que se miran. Sin él, se miran todas.
#
# En `sales` hay nulos en dos columnas: `Item_Weight` (1463) y `Outlet_Size` (2410), y
# ninguna fila los tiene en las dos a la vez.
#
# Crea:
#
# - `with_size`: `sales` sin las filas que no tienen `Outlet_Size`
# - `complete`: `sales` solo con las filas que no tienen **ningún** nulo

# %%
### BEGIN SOLUTION
with_size = sales.dropna(subset=["Outlet_Size"])
complete = sales.dropna(how="any")
### END SOLUTION
### BEGIN STARTER
with_size = ...
complete = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · with_size tiene 6113 filas",
    lambda: with_size.count() == 6113,
    'Usa sales.dropna(subset=["Outlet_Size"]). 8523 − 2410 = 6113.',
)
check(
    "Tarea 5 · with_size conserva los pesos nulos",
    lambda: with_size.filter(F.col("Item_Weight").isNull()).count() == 1463,
    "Con subset solo se mira Outlet_Size: los pesos nulos tienen que seguir ahí.",
)
check(
    "Tarea 5 · complete tiene 4650 filas sin ningún nulo",
    lambda: complete.count() == 4650,
    'Usa sales.dropna() o sales.dropna(how="any"). 8523 − 1463 − 2410 = 4650.',
)

# %% [markdown]
# `how="all"` es mucho menos agresivo: solo quita filas totalmente vacías, y en BigMart no
# hay ninguna.

# %%
print('how="any":', sales.dropna(how="any").count())
print('how="all":', sales.dropna(how="all").count())
print("subset=['Outlet_Size']:", sales.dropna(subset=["Outlet_Size"]).count())

# %% [markdown]
# ## Tarea 6 · Rellenar nulos
#
# `fillna(valor)` sustituye los nulos por un valor. Tiene una regla que sorprende: **solo
# rellena las columnas cuyo tipo encaja con el valor**. Un texto rellena las columnas de
# texto; un número, las numéricas. Las demás se quedan como estaban, sin aviso.
#
# Con un diccionario se da un valor distinto a cada columna, y eso evita el problema.
#
# Crea `filled` a partir de `sales` con `Outlet_Size` rellenado con `"Unknown"` e
# `Item_Weight` rellenado con `12.86`, la media de los pesos conocidos.

# %%
### BEGIN SOLUTION
filled = sales.fillna({"Outlet_Size": "Unknown", "Item_Weight": 12.86})
### END SOLUTION
### BEGIN STARTER
filled = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · no quedan nulos en Outlet_Size ni en Item_Weight",
    lambda: filled.filter(F.col("Outlet_Size").isNull() | F.col("Item_Weight").isNull()).count() == 0,
    'Pasa un diccionario: sales.fillna({"Outlet_Size": "Unknown", "Item_Weight": 12.86}).',
)
check(
    "Tarea 6 · 2410 tiendas marcadas como Unknown",
    lambda: filled.filter(F.col("Outlet_Size") == "Unknown").count() == 2410,
    'El valor para Outlet_Size es exactamente "Unknown".',
)
check(
    "Tarea 6 · 1463 pesos valen 12.86 y la columna sigue siendo double",
    lambda: filled.filter(F.col("Item_Weight") == 12.86).count() == 1463 and dict(filled.dtypes)["Item_Weight"] == "double",
    "El valor para Item_Weight es 12.86. fillna no cambia el tipo de la columna.",
)
check(
    "Tarea 6 · siguen las 8523 filas",
    lambda: filled.count() == 8523,
    "fillna rellena, no borra filas.",
)

# %% [markdown]
# Comprueba la regla del tipo. Un solo valor de texto rellena `Outlet_Size`, pero deja
# `Item_Weight` con sus 1463 nulos; y pedir explícitamente que rellene `Item_Weight` con un
# texto tampoco hace nada:

# %%
text_fill = sales.fillna("Not Available")
print("fillna('Not Available') · Outlet_Size nulos:", text_fill.filter(F.col("Outlet_Size").isNull()).count())
print("fillna('Not Available') · Item_Weight nulos:", text_fill.filter(F.col("Item_Weight").isNull()).count())

forced = sales.fillna("Not Available", subset=["Item_Weight"])
print("fillna('Not Available', subset=['Item_Weight']) · Item_Weight nulos:", forced.filter(F.col("Item_Weight").isNull()).count())

# %% [markdown]
# ## Para terminar · dropna frente a fillna
#
# Las dos opciones quitan los nulos de en medio, pero no son intercambiables. `dropna`
# pierde filas: aquí, el 45 % de los datos si quitas cualquier nulo. `fillna` las conserva,
# pero inventa un valor, y ese valor contamina las medias y los conteos que hagas después.
# Antes de elegir, mira cuántos nulos hay y en qué columnas:

# %%
null_counts = sales.select([F.count(F.when(F.col(column).isNull(), 1)).alias(column) for column in sales.columns])
null_counts.show(vertical=True)

# %% [summary]
