# ---
# id: 11-udfs
# title: UDFs
# objective: Escribir funciones propias en Python y aplicarlas a un DataFrame con udf y pandas_udf, declarar el tipo de retorno, proteger la función de los nulos y comprobar que la versión nativa de Spark da lo mismo y corre más rápido.
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

print("Filas:", sales.count())

# %% [markdown]
# ## Tarea 1 · Una función de Python aplicada a una columna
#
# Una UDF (*user defined function*) son tres pasos: escribir una función de Python normal,
# envolverla con `F.udf(función, tipo_de_retorno)` y aplicarla con `withColumn`. El tipo
# de retorno se puede dar como texto: `"string"`, `"double"`, `"int"`.
#
# Escribe `price_band(mrp)`, que devuelva `"cheap"` si el precio es menor de 100, `"mid"` si
# es menor de 200 y `"premium"` en el resto. Envuélvela en `band_udf` con tipo `"string"` y
# crea `banded` con la columna `band`.

# %%
### BEGIN SOLUTION
def price_band(mrp):
    if mrp < 100:
        return "cheap"
    if mrp < 200:
        return "mid"
    return "premium"


band_udf = F.udf(price_band, "string")
banded = sales.withColumn("band", band_udf("Item_MRP"))
### END SOLUTION
### BEGIN STARTER
def price_band(mrp):
    ...


band_udf = ...
banded = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · price_band funciona como función de Python",
    lambda: [price_band(v) for v in (31.29, 99.99, 100.0, 199.99, 266.89)] == ["cheap", "cheap", "mid", "mid", "premium"],
    "Es una función normal: price_band(50) tiene que devolver 'cheap'. Los límites son < 100 y < 200.",
)
check(
    "Tarea 1 · band es string y reparte 2439 / 4644 / 1440",
    lambda: dict(banded.dtypes)["band"] == "string"
    and {r["band"]: r["count"] for r in banded.groupBy("band").count().collect()} == {"cheap": 2439, "mid": 4644, "premium": 1440},
    'Envuelve con F.udf(price_band, "string") y aplica band_udf("Item_MRP") en withColumn.',
)

# %%
banded.select("Item_Identifier", "Item_MRP", "band").show(5)

# %% [markdown]
# ¿Y si aplicas la función de Python **sin** envolverla? `price_band(F.col("Item_MRP"))` no
# recibe un número sino una columna, y `if columna < 100` no tiene sentido para Python:

# %%
try:
    sales.withColumn("band", price_band(F.col("Item_MRP"))).show(1)
except Exception as error:
    print(type(error).__name__)
    print(str(error).split("\n")[0])

# %% [markdown]
# ## Tarea 2 · El tipo de retorno importa
#
# Si no declaras el tipo, Spark asume `string` y convierte a texto lo que devuelva la
# función. Mira lo que pasa con un cuadrado sin tipo: la columna es texto, y el "máximo" es
# el mayor alfabéticamente, no el mayor número.

# %%
def square(x):
    return x * x


untyped = sales.withColumn("mrp_sq", F.udf(square)("Item_MRP"))
print(untyped.select("mrp_sq").dtypes)
untyped.orderBy(F.desc("mrp_sq")).select("Item_MRP", "mrp_sq").show(3)

# %% [markdown]
# Crea `square_udf` envolviendo `square` con tipo `"double"`, y `squared` con la columna
# `mrp_sq`, el cuadrado de `Item_MRP`.

# %%
### BEGIN SOLUTION
square_udf = F.udf(square, "double")
squared = sales.withColumn("mrp_sq", square_udf("Item_MRP"))
### END SOLUTION
### BEGIN STARTER
square_udf = ...
squared = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · mrp_sq es double",
    lambda: dict(squared.dtypes)["mrp_sq"] == "double",
    'El segundo argumento de F.udf es el tipo de retorno: F.udf(square, "double").',
)
check(
    "Tarea 2 · el cuadrado de 249.8092 es 62404.64 y el máximo 71229.42",
    lambda: round(squared.filter((F.col("Item_Identifier") == "FDA15") & (F.col("Outlet_Identifier") == "OUT049")).first()["mrp_sq"], 2) == 62404.64
    and round(squared.agg(F.max("mrp_sq")).first()[0], 2) == 71229.42,
    "La función es x * x. Con el tipo correcto, el máximo es numérico (266.8884²), no alfabético.",
)

# %%
squared.orderBy(F.desc("mrp_sq")).select("Item_MRP", "mrp_sq").show(3)

# %% [markdown]
# ## Tarea 3 · Proteger la UDF de los nulos
#
# Spark pasa los nulos a la función como `None`. Si la función no lo espera, revienta el
# worker de Python entero, con un error largo que termina en el `TypeError` de siempre.
# `Item_Weight` tiene 1463 nulos:

# %%
try:
    sales.withColumn("grams", F.udf(lambda w: int(round(w * 1000)), "int")("Item_Weight")).filter(F.col("grams").isNull()).count()
except Exception as error:
    print(type(error).__name__)
    print([line for line in str(error).splitlines() if "TypeError" in line][0].strip())

# %% [markdown]
# Escribe `grams(weight)`, que devuelva `None` si el peso es `None` y, si no, el peso en
# gramos como entero: `int(round(weight * 1000))`. Envuélvela en `grams_udf` con tipo
# `"int"` y crea `weighed` con la columna `grams`.

# %%
### BEGIN SOLUTION
def grams(weight):
    if weight is None:
        return None
    return int(round(weight * 1000))


grams_udf = F.udf(grams, "int")
weighed = sales.withColumn("grams", grams_udf("Item_Weight"))
### END SOLUTION
### BEGIN STARTER
def grams(weight):
    ...


grams_udf = ...
weighed = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · grams es int, con 1463 nulos conservados",
    lambda: dict(weighed.dtypes)["grams"] == "int" and weighed.filter(F.col("grams").isNull()).count() == 1463,
    'Devuelve None cuando weight es None, y declara el tipo "int". Los nulos tienen que seguir siendo nulos.',
)
check(
    "Tarea 3 · FDA15 pesa 9300 gramos y el total es 90774975",
    lambda: weighed.filter((F.col("Item_Identifier") == "FDA15") & (F.col("Outlet_Identifier") == "OUT049")).first()["grams"] == 9300
    and weighed.agg(F.sum("grams")).first()[0] == 90774975,
    "Son gramos: int(round(weight * 1000)). Sin round, algunos pesos se truncan y la suma no cuadra.",
)

# %%
weighed.select("Item_Identifier", "Item_Weight", "grams").show(5)

# %% [markdown]
# ## Tarea 4 · La misma lógica, sin UDF
#
# Casi todo lo que se escribe como UDF se puede escribir con funciones nativas, y la versión
# nativa corre dentro de la JVM, sin mandar los datos a Python. Las bandas de precio son un
# `when` encadenado.
#
# Crea `compared` a partir de `banded` con una columna `band_native` calculada con `F.when`,
# sin UDF, que dé exactamente lo mismo que `band`.

# %%
### BEGIN SOLUTION
compared = banded.withColumn(
    "band_native", F.when(F.col("Item_MRP") < 100, "cheap").when(F.col("Item_MRP") < 200, "mid").otherwise("premium")
)
### END SOLUTION
### BEGIN STARTER
compared = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · band_native existe y no hay ninguna fila distinta de band",
    lambda: "band_native" in compared.columns and compared.filter(~F.col("band").eqNullSafe(F.col("band_native"))).count() == 0,
    'F.when(F.col("Item_MRP") < 100, "cheap").when(F.col("Item_MRP") < 200, "mid").otherwise("premium"). Sin otherwise quedan nulos.',
)
check(
    "Tarea 4 · band_native no usa una UDF",
    lambda: "pythonUDF" not in compared.select("band_native")._jdf.queryExecution().executedPlan().toString(),
    "La versión nativa se escribe con F.when y F.col, sin F.udf: en el plan no aparece ningún paso de Python.",
)

# %%
compared.select("Item_MRP", "band", "band_native").show(3)

# %% [markdown]
# La diferencia se ve en el plan de ejecución: la UDF aparece como un paso `ArrowEvalPython`
# (los datos salen de la JVM, pasan por Python y vuelven); la versión nativa es un
# `CASE WHEN` dentro del mismo `Project`.

# %%
compared.select("band").explain()
compared.select("band_native").explain()

# %% [markdown]
# ## Tarea 5 · Los gramos, sin UDF
#
# Crea `weighed_native` a partir de `weighed` con una columna `grams_native` de tipo `int`
# calculada con funciones nativas: `F.round` del peso por 1000 y un `cast`. Los nulos salen
# solos: ninguna función nativa revienta con un `NULL`.

# %%
### BEGIN SOLUTION
weighed_native = weighed.withColumn("grams_native", F.round(F.col("Item_Weight") * 1000).cast("int"))
### END SOLUTION
### BEGIN STARTER
weighed_native = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · grams_native es int y coincide con grams en las 8523 filas",
    lambda: dict(weighed_native.dtypes)["grams_native"] == "int"
    and weighed_native.filter(~F.col("grams").eqNullSafe(F.col("grams_native"))).count() == 0,
    'F.round(F.col("Item_Weight") * 1000).cast("int"). Sin round, el cast trunca y algunos pesos no coinciden.',
)

# %%
weighed_native.select("Item_Weight", "grams", "grams_native").show(3)

# %% [markdown]
# ## Tarea 6 · pandas_udf: Python, pero por lotes
#
# Cuando de verdad hace falta Python, `pandas_udf` es la alternativa rápida: en vez de
# llamar a la función una vez por fila, Spark le pasa **lotes** enteros como `pandas.Series`,
# y la función devuelve otra `Series`. Se escribe como decorador, con el tipo de retorno y
# las anotaciones de tipo.
#
# Escribe `square_pd` con `@pandas_udf("double")`, que reciba una `pd.Series` y devuelva su
# cuadrado, y crea `squared_pd` con la columna `mrp_sq`.

# %%
import pandas as pd
from pyspark.sql.functions import pandas_udf

# %%
### BEGIN SOLUTION
@pandas_udf("double")
def square_pd(s: pd.Series) -> pd.Series:
    return s * s


squared_pd = sales.withColumn("mrp_sq", square_pd("Item_MRP"))
### END SOLUTION
### BEGIN STARTER
@pandas_udf("double")
def square_pd(s: pd.Series) -> pd.Series:
    ...


squared_pd = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · square_pd es una pandas_udf escalar",
    lambda: getattr(square_pd, "evalType", None) == 200,
    "Decora la función con @pandas_udf(\"double\"), no con F.udf, y anota los tipos: (s: pd.Series) -> pd.Series.",
)
check(
    "Tarea 6 · mrp_sq es double y vale 62404.64 para FDA15 en OUT049",
    lambda: dict(squared_pd.dtypes)["mrp_sq"] == "double"
    and round(squared_pd.filter((F.col("Item_Identifier") == "FDA15") & (F.col("Outlet_Identifier") == "OUT049")).first()["mrp_sq"], 2) == 62404.64
    and squared_pd.count() == 8523,
    "La función recibe una Series entera: devuelve s * s.",
)

# %%
squared_pd.select("Item_MRP", "mrp_sq").show(3)

# %% [markdown]
# ## Para terminar · cuánto cuesta cada camino
#
# Con 2 millones de filas, las tres formas de elevar al cuadrado. Los tiempos cambian de una
# máquina a otra, pero el orden no: la nativa gana, la `pandas_udf` queda en medio y la UDF
# fila a fila es la más lenta. Con funciones más pesadas y más datos, la distancia crece.

# %%
import time

big = spark.range(2_000_000).withColumn("x", (F.col("id") % 1000).cast("double"))


def timed(label, column):
    started = time.perf_counter()
    total = big.select(column.alias("y")).agg(F.sum("y")).first()[0]
    print(f"{label:<12} {time.perf_counter() - started:5.2f} s   suma = {total:.0f}")


timed("nativa", F.col("x") * F.col("x"))
timed("udf", square_udf("x"))
timed("pandas_udf", square_pd("x"))

# %% [summary]
