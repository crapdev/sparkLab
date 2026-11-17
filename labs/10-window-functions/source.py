# ---
# id: 10-window-functions
# title: Window functions
# objective: Calcular por fila mirando a las filas vecinas: numerar y clasificar con row_number, rank y dense_rank, acumular con un marco de ventana, y partir la ventana por grupo para sacar el top 3, quedarte con una fila por producto y calcular porcentajes sobre el total del grupo.
# minutes: 45
# ---

# %% [install]

# %% [helpers]

# %% [session]

# %% [data] bigmart_sales.csv

# %%
from pyspark.sql.window import Window

sales = (
    spark.read.format("csv")
    .option("header", True)
    .option("inferSchema", True)
    .load(dataset_path("bigmart_sales.csv"))
)

print("Filas:", sales.count(), "· Parejas producto-tienda distintas:", sales.select("Item_Identifier", "Outlet_Identifier").distinct().count())

# %% [markdown]
# La pareja `Item_Identifier` + `Outlet_Identifier` es única en BigMart. Eso importa en este
# laboratorio: una ventana ordenada solo por `Item_Identifier` deja empates (cada producto
# está en varias tiendas), y con empates el resultado de `row_number` cambia de una ejecución
# a otra. **Desempata siempre** añadiendo columnas al `orderBy` hasta que el orden sea único.
#
# ## Tarea 1 · Numerar las filas
#
# Una window function se escribe en dos partes: la función, `F.row_number()`, y la ventana
# sobre la que actúa, `.over(Window.orderBy(...))`. `row_number` da a cada fila un número
# correlativo, 1, 2, 3…, siguiendo el orden de la ventana. Sin `orderBy` no funciona.
#
# Crea `numbered` con una columna `row_num` que numere las filas ordenadas por
# `Item_Identifier` y, dentro de cada producto, por `Outlet_Identifier`.

# %%
### BEGIN SOLUTION
numbered = sales.withColumn("row_num", F.row_number().over(Window.orderBy("Item_Identifier", "Outlet_Identifier")))
### END SOLUTION
### BEGIN STARTER
numbered = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · 8523 números distintos, del 1 al 8523",
    lambda: numbered.agg(F.max("row_num")).first()[0] == 8523 and numbered.select("row_num").distinct().count() == 8523,
    'Usa F.row_number().over(Window.orderBy("Item_Identifier", "Outlet_Identifier")). Si hay repetidos, has usado rank.',
)
check(
    "Tarea 1 · las filas 1 y 2 son DRA12 en OUT010 y OUT013; la 8523, NCZ54 en OUT049",
    lambda: [tuple(r) for r in numbered.filter(F.col("row_num").isin(1, 2, 8523)).orderBy("row_num").select("Item_Identifier", "Outlet_Identifier").collect()]
    == [("DRA12", "OUT010"), ("DRA12", "OUT013"), ("NCZ54", "OUT049")],
    "El orden es ascendente por las dos columnas, primero el producto y después la tienda. Si falta Outlet_Identifier en el orderBy, las tiendas de DRA12 salen en el orden del archivo.",
)

# %%
numbered.select("Item_Identifier", "Outlet_Identifier", "Item_MRP", "row_num").show(5)

# %% [markdown]
# Fíjate en que la ventana no tiene `partitionBy`: Spark avisa en los logs de que mueve
# **todos los datos a una sola partición** para poder numerarlos de seguido. Con 8523 filas
# da igual; con millones es un cuello de botella, y por eso casi siempre querrás partir la
# ventana (tarea 4).
#
# ## Tarea 2 · rank y dense_rank
#
# `rank` y `dense_rank` también numeran, pero a las filas **empatadas** en el orden les dan
# el mismo número. La diferencia está en lo que viene después del empate: `rank` salta los
# números consumidos (1, 1, 1, 4) y `dense_rank` no (1, 1, 1, 2).
#
# Crea `ranked` con dos columnas, `rank` y `dense_rank`, calculadas sobre la ventana ordenada
# por `Item_Identifier` **descendente**. `NCZ54`, el último producto alfabéticamente, está en
# siete tiendas.

# %%
### BEGIN SOLUTION
by_item_desc = Window.orderBy(F.desc("Item_Identifier"))
ranked = sales.withColumn("rank", F.rank().over(by_item_desc)).withColumn("dense_rank", F.dense_rank().over(by_item_desc))
### END SOLUTION
### BEGIN STARTER
ranked = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · las 7 filas de NCZ54 tienen rank 1 y dense_rank 1",
    lambda: ranked.filter(F.col("Item_Identifier") == "NCZ54").select("rank", "dense_rank").distinct().collect() == [(1, 1)],
    'La ventana es Window.orderBy(F.desc("Item_Identifier")): el producto que va último en orden alfabético recibe el 1.',
)
check(
    "Tarea 2 · NCZ53 tiene rank 8 y dense_rank 2",
    lambda: ranked.filter(F.col("Item_Identifier") == "NCZ53").select("rank", "dense_rank").distinct().collect() == [(8, 2)],
    "rank salta los 7 números que consumió NCZ54; dense_rank sigue en 2. Si te sale otra cosa, revisa cuál es cuál.",
)
check(
    "Tarea 2 · el dense_rank más alto es 1559, uno por producto",
    lambda: ranked.agg(F.max("dense_rank")).first()[0] == 1559,
    "dense_rank nunca salta: su máximo es el número de valores distintos. Con rank el máximo es 8518.",
)

# %%
ranked.select("Item_Identifier", "Outlet_Identifier", "rank", "dense_rank").show(9)

# %% [markdown]
# ## Tarea 3 · Suma acumulada con un marco
#
# Una agregación con `over` no colapsa las filas: cada fila recibe el resultado de agregar
# **su ventana**. Y qué filas entran en la ventana lo decide el **marco**. Para una suma
# acumulada, el marco va desde la primera fila hasta la actual:
# `rowsBetween(Window.unboundedPreceding, Window.currentRow)`.
#
# Crea `running` con una columna `cum_mrp`, la suma acumulada de `Item_MRP` ordenando por
# `Item_Type`, `Item_Identifier` y `Outlet_Identifier` (las tres, para que el orden sea
# único).

# %%
### BEGIN SOLUTION
by_type_item = Window.orderBy("Item_Type", "Item_Identifier", "Outlet_Identifier")
running = sales.withColumn("cum_mrp", F.sum("Item_MRP").over(by_type_item.rowsBetween(Window.unboundedPreceding, Window.currentRow)))
### END SOLUTION
### BEGIN STARTER
running = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · FDA11 en OUT018 acumula 187.49 (la segunda fila)",
    lambda: round(running.filter((F.col("Item_Identifier") == "FDA11") & (F.col("Outlet_Identifier") == "OUT018")).first()["cum_mrp"], 2) == 187.49,
    "El marco es rowsBetween(Window.unboundedPreceding, Window.currentRow): desde el principio hasta la fila actual. Si sale 1201681.48, el marco llega hasta el final.",
)
check(
    "Tarea 3 · la última fila acumula el total general, 1201681.48",
    lambda: round(running.agg(F.max("cum_mrp")).first()[0], 2) == 1201681.48 and running.count() == 8523,
    "La suma acumulada no quita filas: la última llega al total de Item_MRP.",
)

# %%
running.select("Item_Type", "Item_Identifier", "Outlet_Identifier", "Item_MRP", "cum_mrp").show(5)

# %% [markdown]
# ¿Y si no pones marco? Con `orderBy`, el marco por defecto va desde el principio hasta la
# fila actual **incluyendo sus empates**: las filas con el mismo valor de orden comparten
# resultado. Ordenando solo por `Item_Type`, todas las filas de `Baking Goods` reciben la
# misma suma, y las de `Breads` reciben `Baking Goods` más `Breads`:

# %%
sales.withColumn("cum_mrp", F.round(F.sum("Item_MRP").over(Window.orderBy("Item_Type")), 2)).select("Item_Type", "Item_MRP", "cum_mrp").distinct().orderBy("Item_Type").show(3)

# %% [markdown]
# ## Tarea 4 · Top 3 por tienda con partitionBy
#
# `Window.partitionBy("columna")` parte la ventana en grupos: la numeración, el ranking o la
# suma **empiezan de cero en cada grupo**. Es el patrón del "top N por grupo": numerar
# dentro de cada grupo en el orden que te interesa y filtrar los primeros.
#
# Crea `top3` con las tres filas más vendidas (`Item_Outlet_Sales` descendente) de cada
# `Outlet_Identifier`, con una columna `rank_in_outlet` que valga 1, 2 o 3. Desempata por
# `Item_Identifier`.

# %%
### BEGIN SOLUTION
by_outlet_sales = Window.partitionBy("Outlet_Identifier").orderBy(F.desc("Item_Outlet_Sales"), "Item_Identifier")
top3 = sales.withColumn("rank_in_outlet", F.row_number().over(by_outlet_sales)).filter(F.col("rank_in_outlet") <= 3)
### END SOLUTION
### BEGIN STARTER
top3 = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · 30 filas: 3 por cada una de las 10 tiendas",
    lambda: top3.count() == 30 and top3.columns == sales.columns + ["rank_in_outlet"],
    'La ventana es Window.partitionBy("Outlet_Identifier").orderBy(F.desc("Item_Outlet_Sales"), "Item_Identifier"), y el filtro rank_in_outlet <= 3.',
)
check(
    "Tarea 4 · en OUT027 ganan NCE42, FDQ19 y FDZ20, en ese orden",
    lambda: [r["Item_Identifier"] for r in top3.filter(F.col("Outlet_Identifier") == "OUT027").orderBy("rank_in_outlet").collect()] == ["NCE42", "FDQ19", "FDZ20"],
    "El orden dentro de cada tienda es por ventas descendente: el 1 es el producto que más vendió.",
)

# %%
top3.select("Outlet_Identifier", "Item_Identifier", "Item_Type", "Item_Outlet_Sales", "rank_in_outlet").orderBy("Outlet_Identifier", "rank_in_outlet").show(6)

# %% [markdown]
# ## Tarea 5 · Una fila por producto
#
# El mismo patrón con N = 1 sirve para **deduplicar eligiendo**: de las varias filas de cada
# producto (una por tienda), quedarte con la que más vendió. A diferencia de
# `dropDuplicates`, tú decides cuál sobrevive.
#
# Crea `best_outlet` con una sola fila por `Item_Identifier`: la de mayor
# `Item_Outlet_Sales`, desempatando por `Outlet_Identifier` ascendente. El resultado tiene
# que tener **las mismas columnas que `sales`**: quita la columna auxiliar al final.

# %%
### BEGIN SOLUTION
by_item_sales = Window.partitionBy("Item_Identifier").orderBy(F.desc("Item_Outlet_Sales"), "Outlet_Identifier")
best_outlet = sales.withColumn("rn", F.row_number().over(by_item_sales)).filter(F.col("rn") == 1).drop("rn")
### END SOLUTION
### BEGIN STARTER
best_outlet = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · 1559 filas, una por producto, con las columnas de sales",
    lambda: best_outlet.count() == 1559 and best_outlet.columns == sales.columns,
    "Numera con row_number dentro de cada Item_Identifier, filtra el 1 y haz drop de la columna auxiliar.",
)
check(
    "Tarea 5 · FDA15 se queda con OUT013 (6474.2392, empatada con OUT027 y OUT035)",
    lambda: best_outlet.filter(F.col("Item_Identifier") == "FDA15").select("Outlet_Identifier", "Item_Outlet_Sales").first() == ("OUT013", 6474.2392),
    'FDA15 vende 6474.2392 en tres tiendas: el desempate por Outlet_Identifier ascendente elige OUT013. Sin desempate, el resultado cambia de una ejecución a otra.',
)
check(
    "Tarea 5 · las mejores ventas suman 5930366.49",
    lambda: round(best_outlet.agg(F.sum("Item_Outlet_Sales")).first()[0], 2) == 5930366.49,
    "Si la suma es menor, te has quedado con una fila cualquiera en vez de la de mayor venta.",
)

# %%
best_outlet.filter(F.col("Item_Identifier").isin("FDA15", "DRC01")).select("Item_Identifier", "Outlet_Identifier", "Item_Outlet_Sales").show()

# %% [markdown]
# ## Tarea 6 · Porcentaje sobre el total de la tienda
#
# Una ventana con `partitionBy` y **sin** `orderBy` agrega el grupo entero y pega el
# resultado en cada fila. Es como un `groupBy` que no colapsa: sirve para comparar cada fila
# con el total de su grupo.
#
# Crea `shares` con dos columnas nuevas: `outlet_total`, la suma de `Item_Outlet_Sales` de
# la tienda de cada fila, y `share_pct`, el porcentaje que esa fila representa sobre ese
# total, redondeado a 2 decimales.

# %%
### BEGIN SOLUTION
by_outlet = Window.partitionBy("Outlet_Identifier")
shares = sales.withColumn("outlet_total", F.sum("Item_Outlet_Sales").over(by_outlet)).withColumn(
    "share_pct", F.round(F.col("Item_Outlet_Sales") / F.col("outlet_total") * 100, 2)
)
### END SOLUTION
### BEGIN STARTER
shares = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · sigue habiendo 8523 filas y 10 totales distintos",
    lambda: shares.count() == 8523 and shares.select("outlet_total").distinct().count() == 10,
    'La ventana es Window.partitionBy("Outlet_Identifier"), sin orderBy. Con groupBy te quedarían 10 filas; con orderBy, un acumulado.',
)
check(
    "Tarea 6 · FDA15 en OUT049 es el 0.17 % de los 2183969.81 de la tienda",
    lambda: shares.filter((F.col("Item_Identifier") == "FDA15") & (F.col("Outlet_Identifier") == "OUT049")).select(F.round("outlet_total", 2), "share_pct").first() == (2183969.81, 0.17),
    "share_pct es F.round(F.col(\"Item_Outlet_Sales\") / F.col(\"outlet_total\") * 100, 2).",
)
check(
    "Tarea 6 · el producto con más peso es NCK30 en OUT010, con el 0.94 %",
    lambda: shares.orderBy(F.desc("share_pct")).select("Item_Identifier", "Outlet_Identifier", "share_pct").first() == ("NCK30", "OUT010", 0.94),
    "El porcentaje más alto está en la tienda que menos vende en total, OUT010.",
)

# %%
shares.select("Item_Identifier", "Outlet_Identifier", "Item_Outlet_Sales", "outlet_total", "share_pct").show(3)

# %% [markdown]
# ## Para terminar · mirar a la fila de al lado, y dos errores
#
# `F.lag` y `F.lead` traen el valor de la fila anterior o siguiente dentro de la ventana. La
# primera fila no tiene anterior: `NULL`, salvo que pases un valor por defecto.

# %%
daily = spark.createDataFrame([(1, 10.0), (2, 20.0), (3, 15.0), (4, 5.0), (5, 30.0)], "day INT, amount DOUBLE")
by_day = Window.orderBy("day")
daily.withColumn("prev", F.lag("amount").over(by_day)).withColumn("next", F.lead("amount").over(by_day)).withColumn("diff", F.col("amount") - F.lag("amount", 1, 0).over(by_day)).show()

# %% [markdown]
# **1. Una ventana sin `orderBy` para una función que necesita orden.** `row_number`, `rank`
# y `lag` no saben qué significa "anterior" si no hay orden:

# %%
try:
    sales.withColumn("rn", F.row_number().over(Window.partitionBy("Outlet_Identifier"))).show(1)
except Exception as error:
    print(type(error).__name__)
    print(str(error).split(". ")[0])

# %% [markdown]
# **2. Filtrar directamente con la window function.** No se puede usar dentro de `filter`:
# primero la calculas en una columna con `withColumn`, y después filtras por la columna. Es
# lo que has hecho en las tareas 4 y 5.

# %%
try:
    sales.filter(F.row_number().over(Window.orderBy("Item_Identifier")) == 1).show(1)
except Exception as error:
    print(type(error).__name__)
    print(str(error).split(";")[0])

# %% [summary]
