# ---
# id: 03-seleccionar-filtrar
# title: Seleccionar y filtrar
# objective: Quedarte con las columnas y las filas que te interesan de un DataFrame: select, col, alias, filter y las condiciones combinadas con &, | y ~.
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

print("Filas:", sales.count(), "· Columnas:", len(sales.columns))
print(sales.columns)

# %% [markdown]
# ## Tarea 1 · Selecciona tres columnas
#
# `select` devuelve un DataFrame nuevo solo con las columnas que le pides. La forma más
# corta es pasar los nombres como strings.
#
# Crea `item_basics` con exactamente estas tres columnas, en este orden:
# `Item_Identifier`, `Item_Weight` e `Item_Fat_Content`.

# %%
### BEGIN SOLUTION
item_basics = sales.select("Item_Identifier", "Item_Weight", "Item_Fat_Content")
### END SOLUTION
### BEGIN STARTER
item_basics = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · tres columnas en orden",
    lambda: item_basics.columns == ["Item_Identifier", "Item_Weight", "Item_Fat_Content"],
    'Usa sales.select("Item_Identifier", "Item_Weight", "Item_Fat_Content").',
)
check(
    "Tarea 1 · siguen las 8523 filas",
    lambda: item_basics.count() == 8523,
    "select recorta columnas, no filas: tienen que quedar todas.",
)

# %% [markdown]
# Mira el resultado. Fíjate en que `select` no toca las filas: hay las mismas que antes,
# pero más estrechas.

# %%
item_basics.show(3)

# %% [markdown]
# ## Tarea 2 · Renombra con alias
#
# Un string solo puede nombrar una columna. Para hacer algo más con ella, como
# renombrarla, hace falta un objeto columna: `F.col("nombre")`. A ese objeto se le puede
# pedir `.alias("otro_nombre")`.
#
# Crea `prices` con dos columnas: `Item_Identifier` renombrada a `Item_ID` e `Item_MRP`
# renombrada a `Price`.

# %%
### BEGIN SOLUTION
prices = sales.select(F.col("Item_Identifier").alias("Item_ID"), F.col("Item_MRP").alias("Price"))
### END SOLUTION
### BEGIN STARTER
prices = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · columnas Item_ID y Price",
    lambda: prices.columns == ["Item_ID", "Price"],
    'Cada columna va como F.col("nombre_original").alias("nombre_nuevo").',
)
check(
    "Tarea 2 · Price contiene el precio",
    lambda: prices.first()["Price"] == 249.8092,
    "Price tiene que salir de Item_MRP, no de otra columna.",
)
check(
    "Tarea 2 · siguen las 8523 filas",
    lambda: prices.count() == 8523,
    "Solo hay que seleccionar y renombrar, sin filtrar filas.",
)

# %% [markdown]
# Un detalle importante: el alias cambia el nombre **en el DataFrame nuevo**. En `sales`
# la columna sigue llamándose `Item_MRP`, y en `prices` ya no existe con ese nombre:

# %%
prices.show(3)
print("Columnas de sales:  ", sales.columns[:2], "...")
print("Columnas de prices: ", prices.columns)

# %% [markdown]
# ## Tarea 3 · Un filtro sencillo
#
# `filter` devuelve las filas que cumplen una condición. La condición se escribe comparando
# una columna con un valor: `F.col("columna") == valor`. `where` hace exactamente lo mismo.
#
# Crea `regular` con los productos cuyo `Item_Fat_Content` es exactamente `"Regular"`.

# %%
### BEGIN SOLUTION
regular = sales.filter(F.col("Item_Fat_Content") == "Regular")
### END SOLUTION
### BEGIN STARTER
regular = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · 2889 filas",
    lambda: regular.count() == 2889,
    'La condición es F.col("Item_Fat_Content") == "Regular", respetando mayúsculas.',
)
check(
    "Tarea 3 · todas las filas son Regular",
    lambda: regular.filter(F.col("Item_Fat_Content") != "Regular").count() == 0,
    "Se han colado filas con otro valor. Revisa la comparación.",
)
check(
    "Tarea 3 · conserva las 12 columnas",
    lambda: len(regular.columns) == 12,
    "filter recorta filas, no columnas: tienen que quedar las 12.",
)

# %% [markdown]
# Si escribes mal el valor, Spark no avisa: simplemente no encuentra ninguna fila.
# Compara `"Regular"` con `"regular"`:

# %%
print('"Regular":', sales.filter(F.col("Item_Fat_Content") == "Regular").count())
print('"regular":', sales.filter(F.col("Item_Fat_Content") == "regular").count())

# %% [markdown]
# Antes de filtrar por un valor de texto, conviene mirar qué valores hay de verdad:

# %%
sales.select("Item_Fat_Content").distinct().show()

# %% [markdown]
# ## Tarea 4 · Dos condiciones con `&`
#
# Para exigir dos condiciones a la vez se usa `&`, y **cada condición va entre
# paréntesis**: `(cond1) & (cond2)`. En PySpark no sirven `and`, `or` ni `not`: se usan
# `&`, `|` y `~`.
#
# Crea `light_drinks` con los productos de tipo `"Soft Drinks"` que pesan menos de 10
# (columna `Item_Weight`).

# %%
### BEGIN SOLUTION
light_drinks = sales.filter((F.col("Item_Type") == "Soft Drinks") & (F.col("Item_Weight") < 10))
### END SOLUTION
### BEGIN STARTER
light_drinks = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · 166 filas",
    lambda: light_drinks.count() == 166,
    "Las dos condiciones van entre paréntesis y unidas con &.",
)
check(
    "Tarea 4 · todas son Soft Drinks",
    lambda: light_drinks.filter(F.col("Item_Type") != "Soft Drinks").count() == 0,
    'La primera condición es F.col("Item_Type") == "Soft Drinks".',
)
check(
    "Tarea 4 · todas pesan menos de 10",
    lambda: light_drinks.filter(~(F.col("Item_Weight") < 10)).count() == 0,
    'La segunda condición es F.col("Item_Weight") < 10.',
)

# %% [markdown]
# ¿Qué pasa si usas `and` en vez de `&`? Python intenta convertir la primera condición en
# `True` o `False`, y una columna de Spark no es ni lo uno ni lo otro. Esta celda provoca
# el error a propósito y muestra el mensaje:

# %%
try:
    sales.filter((F.col("Item_Type") == "Soft Drinks") and (F.col("Item_Weight") < 10))
except Exception as error:
    print(type(error).__name__)
    print(error)

# %% [markdown]
# Olvidar los paréntesis produce **el mismo error**, porque `&` se evalúa antes que `==` y
# `<`. Spark acaba viendo `"Soft Drinks" & F.col("Item_Weight")`, que no tiene sentido:

# %%
try:
    sales.filter(F.col("Item_Type") == "Soft Drinks" & F.col("Item_Weight") < 10)
except Exception as error:
    print(type(error).__name__)
    print(error)

# %% [markdown]
# ## Tarea 5 · Nulos y listas de valores
#
# Dos condiciones nuevas:
#
# - `F.col("columna").isNull()` es verdadera cuando el valor falta. Comparar con `== None`
#   **no funciona**: siempre devuelve cero filas.
# - `F.col("columna").isin("a", "b", "c")` es verdadera cuando el valor es uno de la lista.
#
# Crea `unknown_size` con las filas que no tienen `Outlet_Size` **y** cuyo
# `Outlet_Location_Type` es `"Tier 1"` o `"Tier 2"`.

# %%
### BEGIN SOLUTION
unknown_size = sales.filter(F.col("Outlet_Size").isNull() & F.col("Outlet_Location_Type").isin("Tier 1", "Tier 2"))
### END SOLUTION
### BEGIN STARTER
unknown_size = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · 1855 filas",
    lambda: unknown_size.count() == 1855,
    'Combina F.col("Outlet_Size").isNull() y F.col("Outlet_Location_Type").isin("Tier 1", "Tier 2") con &.',
)
check(
    "Tarea 5 · Outlet_Size es nulo en todas",
    lambda: unknown_size.filter(F.col("Outlet_Size").isNotNull()).count() == 0,
    "Para detectar nulos usa .isNull(), no == None.",
)
check(
    "Tarea 5 · no hay tiendas de Tier 3",
    lambda: unknown_size.filter(F.col("Outlet_Location_Type") == "Tier 3").count() == 0,
    'Revisa la lista de isin: solo "Tier 1" y "Tier 2".',
)

# %% [markdown]
# Comprueba por qué `== None` no sirve. Las dos expresiones parecen pedir lo mismo, pero
# solo una funciona:

# %%
print("isNull(): ", sales.filter(F.col("Outlet_Size").isNull()).count())
print("== None:  ", sales.filter(F.col("Outlet_Size") == None).count())  # Wrong on purpose.

# %% [markdown]
# ## Tarea 6 · Combina `|` y `~`
#
# `|` es el OR y `~` es el NOT. Se combinan con `&` siguiendo la misma regla: cada
# condición entre paréntesis.
#
# Crea `fresh_outside_tier3` con los productos de tipo `"Dairy"` **o** `"Meat"` cuyo
# `Outlet_Location_Type` **no** es `"Tier 3"`. Usa `|` para el "o" y `~` para el "no".

# %%
### BEGIN SOLUTION
fresh_outside_tier3 = sales.filter(
    ((F.col("Item_Type") == "Dairy") | (F.col("Item_Type") == "Meat"))
    & ~(F.col("Outlet_Location_Type") == "Tier 3")
)
### END SOLUTION
### BEGIN STARTER
fresh_outside_tier3 = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · 667 filas",
    lambda: fresh_outside_tier3.count() == 667,
    "El OR de los dos tipos va entre paréntesis, y después el & con la negación.",
)
check(
    "Tarea 6 · solo Dairy y Meat",
    lambda: fresh_outside_tier3.filter(~F.col("Item_Type").isin("Dairy", "Meat")).count() == 0,
    'Las dos condiciones del OR son F.col("Item_Type") == "Dairy" y F.col("Item_Type") == "Meat".',
)
check(
    "Tarea 6 · ninguna tienda es de Tier 3",
    lambda: fresh_outside_tier3.filter(F.col("Outlet_Location_Type") == "Tier 3").count() == 0,
    'La negación es ~(F.col("Outlet_Location_Type") == "Tier 3"), con sus paréntesis.',
)

# %% [markdown]
# Si te ha salido, prueba a escribir lo mismo con `isin` en lugar del OR y con `!=` en
# lugar del NOT. El resultado tiene que ser idéntico: hay varias formas de decir lo mismo.

# %%
same_thing = sales.filter(F.col("Item_Type").isin("Dairy", "Meat") & (F.col("Outlet_Location_Type") != "Tier 3"))
print("Con | y ~:     ", fresh_outside_tier3.count())
print("Con isin y !=: ", same_thing.count())

# %% [markdown]
# ## Para terminar · los nulos no se dejan comparar
#
# `Item_Weight` tiene 1463 valores nulos. Si separas las filas en "pesan menos de 10" y
# "no pesan menos de 10", esperarías que las dos partes sumen 8523. No lo hacen:

# %%
light = sales.filter(F.col("Item_Weight") < 10).count()
not_light = sales.filter(~(F.col("Item_Weight") < 10)).count()
missing = sales.filter(F.col("Item_Weight").isNull()).count()

print("Item_Weight < 10:    ", light)
print("~(Item_Weight < 10): ", not_light)
print("Suma:                ", light + not_light, "de", sales.count())
print("Item_Weight nulo:    ", missing)

# %% [markdown]
# Una comparación con un nulo no es ni verdadera ni falsa, así que `filter` descarta esas
# filas en los dos casos. Si quieres conservarlas, tienes que pedirlo: `(F.col("Item_Weight") < 10) | F.col("Item_Weight").isNull()`.

# %% [summary]
