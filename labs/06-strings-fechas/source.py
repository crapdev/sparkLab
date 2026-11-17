# ---
# id: 06-strings-fechas
# title: Strings y fechas
# objective: Limpiar y combinar texto con upper, initcap, substring y concat_ws, y trabajar con fechas de verdad: to_date, year, datediff, months_between, date_add y date_format.
# minutes: 40
# ---

# %% [install]

# %% [helpers]

# %% [session]

# %% [data] bigmart_sales.csv drivers.json

# %%
sales = (
    spark.read.format("csv")
    .option("header", True)
    .option("inferSchema", True)
    .load(dataset_path("bigmart_sales.csv"))
)
drivers = spark.read.format("json").load(dataset_path("drivers.json"))

print("Productos:", sales.count(), "· Pilotos:", drivers.count())

# %% [markdown]
# ## Tarea 1 · Mayúsculas y trozos de texto
#
# Las funciones de texto viven en `F` y devuelven una columna nueva: `F.upper`, `F.lower`,
# `F.initcap` (primera letra de cada palabra en mayúscula) y `F.substring(columna, inicio,
# longitud)`, donde el inicio cuenta **desde 1**.
#
# Los identificadores de BigMart empiezan por dos letras que indican la familia del
# producto: `FD` (comida), `DR` (bebida) y `NC` (no comestible).
#
# Crea `coded` a partir de `sales` con dos cambios:
#
# - una columna nueva `prefix` con las dos primeras letras de `Item_Identifier`
# - `Item_Type` sobrescrita en mayúsculas

# %%
### BEGIN SOLUTION
coded = sales.withColumn("prefix", F.substring("Item_Identifier", 1, 2)).withColumn("Item_Type", F.upper("Item_Type"))
### END SOLUTION
### BEGIN STARTER
coded = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · prefix tiene las dos primeras letras",
    lambda: coded.filter(F.col("prefix") == "FD").count() == 6125 and coded.filter(F.col("prefix") == "DR").count() == 799,
    'Usa F.substring("Item_Identifier", 1, 2): el inicio es 1, no 0. Hay 6125 FD, 1599 NC y 799 DR.',
)
check(
    "Tarea 1 · Item_Type está en mayúsculas",
    lambda: coded.filter(F.col("Item_Type") == "SOFT DRINKS").count() == 445 and "Item_Type" in coded.columns,
    'Sobrescribe la columna: withColumn("Item_Type", F.upper("Item_Type")).',
)
check(
    "Tarea 1 · 13 columnas y 8523 filas",
    lambda: len(coded.columns) == 13 and coded.count() == 8523,
    "prefix se añade e Item_Type se sobrescribe: 12 + 1 columnas, sin perder filas.",
)

# %% [markdown]
# Las tres funciones de mayúsculas, lado a lado. Fíjate en `initcap` con `Item_Fat_Content`:
# convierte `LF` en `Lf` y `reg` en `Reg`, así que no sirve para unificar esas variantes;
# para eso, `lower` y después un `when`, como en el módulo anterior.

# %%
sales.select(F.initcap("Item_Type").alias("initcap"), F.lower("Item_Type").alias("lower"), F.upper("Item_Type").alias("upper")).distinct().show(3, truncate=False)
sales.select(F.initcap("Item_Fat_Content").alias("fat")).groupBy("fat").count().orderBy("fat").show()

# %% [markdown]
# ## Tarea 2 · Unir textos
#
# `F.concat_ws(separador, col1, col2, ...)` une varias columnas con un separador. Si una es
# nula, la salta. `F.concat` hace lo mismo sin separador, pero **si alguna columna es nula,
# el resultado es nulo**.
#
# Los pilotos tienen el nombre partido en `name.forename` y `name.surname`. Crea
# `named` añadiendo a `drivers` la columna `full_name`: nombre y apellido separados por un
# espacio.

# %%
### BEGIN SOLUTION
named = drivers.withColumn("full_name", F.concat_ws(" ", "name.forename", "name.surname"))
### END SOLUTION
### BEGIN STARTER
named = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · Lewis Hamilton existe",
    lambda: named.filter(F.col("full_name") == "Lewis Hamilton").count() == 1,
    'Usa F.concat_ws(" ", "name.forename", "name.surname"). El separador va primero.',
)
check(
    "Tarea 2 · ningún nombre nulo",
    lambda: named.filter(F.col("full_name").isNull()).count() == 0 and named.count() == 885,
    "Con concat_ws no hay nulos. Si usaste concat con una columna nula, el resultado sería nulo.",
)

# %% [markdown]
# La diferencia con los nulos importa: 765 pilotos no tienen `code`. Mira qué pasa al unir
# `driverRef` con `code` de las dos formas:

# %%
print("concat:   ", drivers.select(F.concat("driverRef", F.lit("-"), "code").alias("c")).filter(F.col("c").isNull()).count(), "nulos")
print("concat_ws:", drivers.select(F.concat_ws("-", "driverRef", "code").alias("c")).filter(F.col("c").isNull()).count(), "nulos")
drivers.filter(F.col("code").isNull()).select("driverRef", "code", F.concat_ws("-", "driverRef", "code").alias("concat_ws")).show(2)

# %% [markdown]
# ## Tarea 3 · De texto a fecha
#
# `dob` (fecha de nacimiento) llegó del JSON como `string`. Mientras sea texto, no puedes
# restar fechas ni sacar el año de forma fiable. `F.to_date(columna)` la convierte al tipo
# `date`. Si el texto no está en formato `yyyy-MM-dd`, hay que decirle el patrón:
# `F.to_date(columna, "dd/MM/yyyy")`.
#
# Crea `dated` a partir de `named` **sobrescribiendo** `dob` con su versión de tipo fecha.

# %%
### BEGIN SOLUTION
dated = named.withColumn("dob", F.to_date("dob"))
### END SOLUTION
### BEGIN STARTER
dated = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · dob es de tipo date",
    lambda: dict(dated.dtypes)["dob"] == "date",
    'Usa withColumn("dob", F.to_date("dob")). El texto ya está en yyyy-MM-dd, no hace falta patrón.',
)
check(
    "Tarea 3 · Hamilton nació el 7 de enero de 1985",
    lambda: str(dated.filter(F.col("driverRef") == "hamilton").first()["dob"]) == "1985-01-07",
    "Convierte la columna dob, no otra.",
)
check(
    "Tarea 3 · los 7 nulos siguen siendo nulos",
    lambda: dated.filter(F.col("dob").isNull()).count() == 7,
    "to_date deja los nulos como están. No rellenes ni filtres.",
)

# %% [markdown]
# Un patrón equivocado no devuelve nulos: en Spark 4 **falla al ejecutar**, como el `cast`.
# Esta celda intenta leer `1985-01-07` con el patrón `dd/MM/yyyy`:

# %%
try:
    dated.select(F.to_date(F.lit("1985-01-07"), "dd/MM/yyyy")).show()
except Exception as error:
    print(type(error).__name__)
    print(str(error).split("\n")[0])

# %% [markdown]
# ## Tarea 4 · Partes de una fecha
#
# Con una columna `date`, `F.year`, `F.month` y `F.dayofmonth` sacan cada parte como un
# número entero.
#
# Crea `with_year` añadiendo a `dated` la columna `birth_year` con el año de nacimiento, y
# `young` con los pilotos nacidos en 1990 o después.

# %%
### BEGIN SOLUTION
with_year = dated.withColumn("birth_year", F.year("dob"))
young = with_year.filter(F.col("birth_year") >= 1990)
### END SOLUTION
### BEGIN STARTER
with_year = ...
young = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · birth_year es un entero y vale 1985 para Hamilton",
    lambda: dict(with_year.dtypes)["birth_year"] == "int"
    and with_year.filter(F.col("driverRef") == "hamilton").first()["birth_year"] == 1985,
    'Usa F.year("dob"). Devuelve un int, no un texto.',
)
check(
    "Tarea 4 · 59 pilotos nacidos en 1990 o después",
    lambda: young.count() == 59,
    "Filtra birth_year >= 1990, incluyendo 1990. Los 7 pilotos sin fecha quedan fuera solos.",
)

# %% [markdown]
# ## Tarea 5 · Restar fechas
#
# Dos formas de medir la distancia entre fechas:
#
# - `F.datediff(fin, inicio)` devuelve **días**. El orden importa: si `fin` es anterior a
#   `inicio`, sale negativo.
# - `F.months_between(fin, inicio)` devuelve **meses** con decimales.
#
# Para una edad, lo cómodo es `months_between` dividido entre 12 y redondeado hacia abajo
# con `F.floor`. Para que el resultado no cambie cada día, aquí se calcula a una fecha
# fija: `REFERENCE`, el 1 de enero de 2025.
#
# Crea `aged` añadiendo a `with_year` la columna `age`: la edad en años cumplidos a
# `REFERENCE`, como entero (`.cast("int")` después de `F.floor`).

# %%
REFERENCE = F.to_date(F.lit("2025-01-01"))

### BEGIN SOLUTION
aged = with_year.withColumn("age", F.floor(F.months_between(REFERENCE, F.col("dob")) / 12).cast("int"))
### END SOLUTION
### BEGIN STARTER
aged = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · Hamilton tenía 39 años el 1 de enero de 2025",
    lambda: aged.filter(F.col("driverRef") == "hamilton").first()["age"] == 39,
    "Es F.months_between(REFERENCE, F.col(\"dob\")) / 12, en ese orden, y F.floor para quedarte con los años cumplidos.",
)
check(
    "Tarea 5 · el piloto más joven tenía 16",
    lambda: aged.filter(F.col("age").isNotNull()).agg(F.min("age")).first()[0] == 16,
    "Si te sale negativo, los argumentos de months_between están al revés.",
)
check(
    "Tarea 5 · 39 pilotos con menos de 30 años y age es int",
    lambda: aged.filter(F.col("age") < 30).count() == 39 and dict(aged.dtypes)["age"] == "int",
    'Termina con .cast("int"): floor devuelve un bigint.',
)

# %% [markdown]
# Compara con `datediff` y mira el signo según el orden de los argumentos:

# %%
hamilton = aged.filter(F.col("driverRef") == "hamilton")
hamilton.select(
    "dob",
    F.datediff(REFERENCE, F.col("dob")).alias("days_lived"),
    F.datediff(F.col("dob"), REFERENCE).alias("reversed"),
    F.months_between(REFERENCE, F.col("dob")).alias("months"),
    "age",
).show()

# %% [markdown]
# Sumar y restar días es más directo: `F.date_add(fecha, n)` y `F.date_sub(fecha, n)`.
# Un número negativo en `date_add` también resta. Y `F.current_date()` da la fecha de hoy,
# que es lo que usarías en un proceso real en vez de `REFERENCE`.

# %%
hamilton.select(
    "dob",
    F.date_add("dob", 7).alias("week_after"),
    F.date_sub("dob", 7).alias("week_before"),
    F.date_add("dob", -7).alias("also_before"),
    F.current_date().alias("today"),
).show()

# %% [markdown]
# ## Tarea 6 · De fecha a texto con formato
#
# `F.date_format(fecha, patrón)` convierte una fecha en **texto** con el formato que pidas.
# Las letras del patrón importan, mayúsculas incluidas: `yyyy` año, `MM` mes, `dd` día.
# `mm` son minutos y `YYYY` ni siquiera se acepta.
#
# Crea `formatted` añadiendo a `aged` la columna `dob_text` con la fecha como `dd/MM/yyyy`.

# %%
### BEGIN SOLUTION
formatted = aged.withColumn("dob_text", F.date_format("dob", "dd/MM/yyyy"))
### END SOLUTION
### BEGIN STARTER
formatted = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · Hamilton sale como 07/01/1985",
    lambda: formatted.filter(F.col("driverRef") == "hamilton").first()["dob_text"] == "07/01/1985",
    'El patrón es "dd/MM/yyyy": día, mes en mayúsculas, año en minúsculas.',
)
check(
    "Tarea 6 · dob_text es string y dob sigue siendo date",
    lambda: dict(formatted.dtypes)["dob_text"] == "string" and dict(formatted.dtypes)["dob"] == "date",
    "date_format devuelve texto. Ponlo en una columna nueva y conserva dob como fecha.",
)

# %% [markdown]
# Los dos tropiezos clásicos del patrón. `mm` son minutos, así que el mes sale `00`. Y
# `YYYY` (año por semanas) ya no se acepta: Spark lanza un error que explica el cambio.

# %%
hamilton.select(F.date_format("dob", "dd-MM-yyyy").alias("MM_mes"), F.date_format("dob", "dd-mm-yyyy").alias("mm_minutos")).show()

try:
    hamilton.select(F.date_format("dob", "dd/MM/YYYY")).show()
except Exception as error:
    print(type(error).__name__)
    print(str(error).split("\n")[0][:200])

# %% [markdown]
# ## Para terminar · texto que parece fecha
#
# Como `dob` venía en `yyyy-MM-dd`, muchas cosas funcionan incluso sin `to_date`: Spark
# convierte el texto por debajo cuando una función de fechas lo necesita. Eso engaña. En
# cuanto la fecha llega en otro formato (`07/01/1985`, `Jan 7 1985`), la conversión
# implícita falla, y comparar textos como si fueran fechas da resultados absurdos con
# formatos distintos. Convierte siempre con `to_date` al leer y trabaja con fechas de verdad.

# %%
print("year() sobre el texto:", drivers.filter(F.col("driverRef") == "hamilton").select(F.year("dob")).first()[0])
print("Esquema con to_date:   ", dict(dated.dtypes)["dob"])

# %% [summary]
