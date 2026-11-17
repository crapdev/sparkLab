# ---
# id: 09-union-joins
# title: Union y joins
# objective: Apilar DataFrames con unionByName y cruzarlos con inner, left y anti join, primero con dos tablas pequeñas y después con las ventas de BigMart y su tabla de tiendas.
# minutes: 40
# ---

# %% [install]

# %% [helpers]

# %% [session]

# %% [data] bigmart_sales.csv outlets.csv

# %% [markdown]
# ## Dos tablas de juguete
#
# Antes de tocar BigMart, dos DataFrames tan pequeños que se ven enteros en pantalla:
# `emp`, con seis empleados y el departamento de cada uno, y `dept`, con cinco
# departamentos. Fíjate en que `d03` tiene dos empleados, que Jorge está en `d06` (que no
# existe en `dept`) y que `Legal` (`d04`) no tiene a nadie.

# %%
emp = spark.createDataFrame(
    [(1, "Ana", "d01"), (2, "Luis", "d02"), (3, "Marta", "d03"), (4, "Pedro", "d03"), (5, "Sofía", "d05"), (6, "Jorge", "d06")],
    "emp_id INT, name STRING, dept_id STRING",
)
dept = spark.createDataFrame(
    [("d01", "Ventas"), ("d02", "Marketing"), ("d03", "Datos"), ("d04", "Legal"), ("d05", "Soporte")],
    "dept_id STRING, dept_name STRING",
)
emp.show()
dept.show()

# %% [markdown]
# ## Tarea 1 · Apilar dos DataFrames
#
# `union` pone las filas de un DataFrame debajo de las de otro **por posición**: la primera
# columna bajo la primera, la segunda bajo la segunda, sin mirar los nombres.
# `unionByName` las empareja **por nombre**, y es la forma segura.
#
# `new_hires` trae dos empleados nuevos con las columnas en otro orden. Crea `staff` con
# todos los empleados, los seis de `emp` y los dos nuevos, con las columnas de `emp`.

# %%
new_hires = spark.createDataFrame([(7, "d02", "Elena"), (8, "d04", "Hugo")], "emp_id INT, dept_id STRING, name STRING")
new_hires.show()

# %%
### BEGIN SOLUTION
staff = emp.unionByName(new_hires)
### END SOLUTION
### BEGIN STARTER
staff = ...
### END STARTER

# %% [test]
check(
    "Tarea 1 · 8 empleados con las columnas emp_id, name y dept_id",
    lambda: staff.count() == 8 and staff.columns == ["emp_id", "name", "dept_id"],
    "Usa emp.unionByName(new_hires): el DataFrame de la izquierda manda en el orden de las columnas.",
)
check(
    "Tarea 1 · Elena sigue siendo Elena y está en d02",
    lambda: staff.filter(F.col("emp_id") == 7).first().asDict() == {"emp_id": 7, "name": "Elena", "dept_id": "d02"},
    "Con union, el nombre acaba en dept_id y el departamento en name. unionByName empareja por nombre de columna.",
)

# %%
staff.show()

# %% [markdown]
# Mira lo que hace `union` con las mismas dos tablas: no falla, pero mezcla las columnas
# sin avisar, porque `name` y `dept_id` son las dos de texto:

# %%
emp.union(new_hires).show()

# %% [markdown]
# Otras dos cosas que conviene saber de `union`: **no quita duplicados** (para eso está
# `distinct`), y si el número de columnas no coincide, falla:

# %%
print("emp.union(emp):", emp.union(emp).count(), "filas ·", emp.union(emp).distinct().count(), "distintas")
try:
    emp.union(dept).show()
except Exception as error:
    print(type(error).__name__)
    print(str(error).split(";")[0])

# %% [markdown]
# ## Tarea 2 · Inner join
#
# `join` cruza dos DataFrames por una **clave**. Con `inner`, solo salen las filas cuya
# clave está en los dos lados. La forma más explícita de escribir la condición es
# `emp["dept_id"] == dept["dept_id"]`.
#
# Crea `emp_dept` con el inner join de `emp` y `dept` escrito con esa condición explícita.
# Verás que la clave aparece **dos veces** en el resultado, una por cada tabla.

# %%
### BEGIN SOLUTION
emp_dept = emp.join(dept, emp["dept_id"] == dept["dept_id"], "inner")
### END SOLUTION
### BEGIN STARTER
emp_dept = ...
### END STARTER

# %% [test]
check(
    "Tarea 2 · 5 filas: d03 sale dos veces, d04 y d06 no salen",
    lambda: emp_dept.count() == 5,
    'Usa emp.join(dept, emp["dept_id"] == dept["dept_id"], "inner"). Un inner join solo conserva las claves que están en los dos lados.',
)
check(
    "Tarea 2 · las columnas de emp y luego las de dept, con dept_id repetida",
    lambda: emp_dept.columns == ["emp_id", "name", "dept_id", "dept_id", "dept_name"],
    "Con la condición explícita, el resultado trae todas las columnas de los dos DataFrames, emp primero.",
)
check(
    "Tarea 2 · Marta está en Datos y Jorge no está",
    lambda: emp_dept.filter(F.col("name") == "Marta").first()["dept_name"] == "Datos" and emp_dept.filter(F.col("name") == "Jorge").count() == 0,
    "Jorge está en d06, que no existe en dept: un inner join lo descarta.",
)

# %%
emp_dept.show()

# %% [markdown]
# Esa `dept_id` repetida da problemas en cuanto la pides por nombre: Spark no sabe a cuál
# te refieres.

# %%
try:
    emp_dept.select("dept_id").show()
except Exception as error:
    print(type(error).__name__)
    print(str(error).split(";")[0])

# %% [markdown]
# Dos salidas: decir de qué tabla viene la columna, `emp_dept.select(emp["dept_id"])`, o
# hacer el join **por nombre de columna**, `emp.join(dept, "dept_id", "inner")`, que deja
# la clave una sola vez y la pone la primera. Es la forma que usarás a partir de ahora.

# %%
emp.join(dept, "dept_id", "inner").show()

# %% [markdown]
# ## Tarea 3 · Left join
#
# `left` conserva **todas** las filas del DataFrame de la izquierda. Las que no cruzan con
# nada salen igualmente, con `NULL` en las columnas que venían de la derecha.
#
# Crea `emp_left` con el left join de `emp` y `dept` **por nombre de columna**.

# %%
### BEGIN SOLUTION
emp_left = emp.join(dept, "dept_id", "left")
### END SOLUTION
### BEGIN STARTER
emp_left = ...
### END STARTER

# %% [test]
check(
    "Tarea 3 · 6 filas y la clave una sola vez, la primera",
    lambda: emp_left.count() == 6 and emp_left.columns == ["dept_id", "emp_id", "name", "dept_name"],
    'Usa emp.join(dept, "dept_id", "left"): la clave como texto, y emp a la izquierda.',
)
check(
    "Tarea 3 · Jorge está, con dept_name nulo",
    lambda: emp_left.filter(F.col("name") == "Jorge").first()["dept_name"] is None,
    "Un left join no pierde filas de la izquierda: Jorge sale con NULL en lo que venía de dept.",
)
check(
    "Tarea 3 · solo una fila sin departamento",
    lambda: emp_left.filter(F.col("dept_name").isNull()).count() == 1,
    "Solo Jorge (d06) no tiene departamento en dept.",
)

# %%
emp_left.show()

# %% [markdown]
# `right` es lo mismo al revés: conserva todo lo de la derecha. Aquí aparece `Legal`, el
# departamento sin empleados, con nulos en lo que venía de `emp`. Y `full` conserva las
# filas de los dos lados: 7 filas, con Jorge y con Legal.

# %%
emp.join(dept, "dept_id", "right").orderBy("dept_id").show()
print("full:", emp.join(dept, "dept_id", "full").count(), "filas")

# %% [markdown]
# ## Tarea 4 · Anti join: lo que no cruza
#
# `anti` devuelve las filas de la izquierda que **no** tienen pareja en la derecha, y solo
# con las columnas de la izquierda. Es la forma directa de preguntar "¿qué falta?".
#
# Crea dos DataFrames: `emp_without_dept`, los empleados cuyo departamento no existe en
# `dept`, y `dept_without_emp`, los departamentos que no tienen ningún empleado.

# %%
### BEGIN SOLUTION
emp_without_dept = emp.join(dept, "dept_id", "anti")
dept_without_emp = dept.join(emp, "dept_id", "anti")
### END SOLUTION
### BEGIN STARTER
emp_without_dept = ...
dept_without_emp = ...
### END STARTER

# %% [test]
check(
    "Tarea 4 · solo Jorge, y solo con las columnas de emp",
    lambda: emp_without_dept.columns == ["dept_id", "emp_id", "name"] and emp_without_dept.collect()[0].asDict() == {"dept_id": "d06", "emp_id": 6, "name": "Jorge"},
    'Usa emp.join(dept, "dept_id", "anti"). Un anti join no añade columnas de la derecha.',
)
check(
    "Tarea 4 · una sola fila en emp_without_dept",
    lambda: emp_without_dept.count() == 1,
    "Solo Jorge está en un departamento que no existe. Si te salen 5, has usado semi en vez de anti.",
)
check(
    "Tarea 4 · Legal es el único departamento vacío",
    lambda: dept_without_emp.columns == ["dept_id", "dept_name"] and dept_without_emp.collect()[0]["dept_name"] == "Legal" and dept_without_emp.count() == 1,
    "Para los departamentos sin empleados, dept va a la izquierda: dept.join(emp, ...).",
)

# %%
emp_without_dept.show()
dept_without_emp.show()

# %% [markdown]
# ## Tarea 5 · BigMart y su tabla de tiendas
#
# `outlets.csv` tiene una fila por tienda. Cuatro de sus columnas ya están en las ventas
# (`Outlet_Establishment_Year`, `Outlet_Size`, `Outlet_Location_Type` y `Outlet_Type`); las
# otras tres son nuevas: `City`, `Manager` y `Staff`. Y la tabla no cuadra del todo con las
# ventas, a propósito: falta una tienda que vende y sobra una que no vende nada.

# %%
sales = (
    spark.read.format("csv")
    .option("header", True)
    .option("inferSchema", True)
    .load(dataset_path("bigmart_sales.csv"))
)
outlets = (
    spark.read.format("csv")
    .option("header", True)
    .option("inferSchema", True)
    .load(dataset_path("outlets.csv"))
)
print("Ventas:", sales.count(), "filas · Tiendas:", outlets.count())
outlets.show(truncate=False)

# %% [markdown]
# Si cruzas `sales` con `outlets` entera por `Outlet_Identifier`, las otras cuatro columnas
# repetidas vuelven a quedar duplicadas, y `Outlet_Type` se vuelve ambigua. La costumbre
# es **seleccionar de la tabla pequeña solo la clave y las columnas que aportan** antes del
# join.
#
# Crea `outlet_info` con `Outlet_Identifier`, `City`, `Manager` y `Staff`, y `sales_city`
# con el inner join de `sales` y `outlet_info` por `Outlet_Identifier`.

# %%
### BEGIN SOLUTION
outlet_info = outlets.select("Outlet_Identifier", "City", "Manager", "Staff")
sales_city = sales.join(outlet_info, "Outlet_Identifier", "inner")
### END SOLUTION
### BEGIN STARTER
outlet_info = ...
sales_city = ...
### END STARTER

# %% [test]
check(
    "Tarea 5 · 7995 filas: las 528 de OUT019 se pierden",
    lambda: sales_city.count() == 7995,
    "OUT019 vende pero no está en outlets. Con inner, sus 528 filas desaparecen: 8523 − 528 = 7995.",
)
check(
    "Tarea 5 · 15 columnas: las 12 de sales más City, Manager y Staff",
    lambda: len(sales_city.columns) == 15 and sales_city.columns[-3:] == ["City", "Manager", "Staff"],
    'Selecciona en outlet_info solo la clave y las tres columnas nuevas, y haz el join por nombre: sales.join(outlet_info, "Outlet_Identifier", "inner").',
)
check(
    "Tarea 5 · OUT049 está en Delhi y hay 9 ciudades",
    lambda: sales_city.filter(F.col("Outlet_Identifier") == "OUT049").first()["City"] == "Delhi" and sales_city.select("City").distinct().count() == 9,
    "Cada fila de ventas recibe la ciudad de su tienda. Son 9 ciudades porque OUT019 no está y OUT099 no vende.",
)

# %%
sales_city.select("Item_Identifier", "Outlet_Identifier", "Item_Outlet_Sales", "City", "Manager").show(5)

# %% [markdown]
# El join abre la puerta a preguntas que antes no se podían hacer: con `groupBy` del módulo
# anterior, las ventas por ciudad.

# %%
sales_city.groupBy("City").agg(F.round(F.sum("Item_Outlet_Sales"), 2).alias("total_sales")).orderBy(F.desc("total_sales")).show()

# %% [markdown]
# ## Tarea 6 · No perder ventas y encontrar la tienda que no vende
#
# El inner join de la tarea anterior tiró 528 ventas sin decir nada. Si lo que quieres es
# **enriquecer** las ventas sin perder ninguna, el join tiene que ser `left`. Y para saber
# qué tienda del catálogo no vende nada, un `anti` desde `outlets`.
#
# Crea `sales_all`, el left join de `sales` con `outlet_info`, e `idle_outlets`, las
# tiendas de `outlets` que no aparecen en `sales`.

# %%
### BEGIN SOLUTION
sales_all = sales.join(outlet_info, "Outlet_Identifier", "left")
idle_outlets = outlets.join(sales, "Outlet_Identifier", "anti")
### END SOLUTION
### BEGIN STARTER
sales_all = ...
idle_outlets = ...
### END STARTER

# %% [test]
check(
    "Tarea 6 · sales_all conserva las 8523 filas con 15 columnas",
    lambda: sales_all.count() == 8523 and len(sales_all.columns) == 15,
    'Usa sales.join(outlet_info, "Outlet_Identifier", "left"): un left join no pierde filas de la izquierda.',
)
check(
    "Tarea 6 · 528 filas sin City, todas de OUT019",
    lambda: sales_all.filter(F.col("City").isNull()).count() == 528 and sales_all.filter(F.col("City").isNull()).select("Outlet_Identifier").distinct().collect()[0][0] == "OUT019",
    "Las filas de OUT019 salen con City, Manager y Staff a NULL.",
)
check(
    "Tarea 6 · OUT099 es la tienda que no vende, con las 8 columnas de outlets",
    lambda: idle_outlets.count() == 1 and idle_outlets.first()["Outlet_Identifier"] == "OUT099" and idle_outlets.columns == outlets.columns,
    'Usa outlets.join(sales, "Outlet_Identifier", "anti"): outlets a la izquierda, y el anti join solo devuelve sus columnas.',
)

# %%
sales_all.filter(F.col("City").isNull()).select("Item_Identifier", "Outlet_Identifier", "City", "Manager", "Staff").show(3)
idle_outlets.show(truncate=False)

# %% [markdown]
# ## Para terminar · dos trampas de los joins
#
# **1. Las claves repetidas multiplican.** Si la tabla pequeña tiene una tienda dos veces,
# cada venta de esa tienda sale dos veces. Con `OUT049` duplicada, el inner join pasa de
# 7995 a 8925 filas: 930 de más, una por cada venta de esa tienda. Comprueba siempre que
# la clave es única en la tabla de referencia.

# %%
outlets_dup = outlet_info.union(outlet_info.filter(F.col("Outlet_Identifier") == "OUT049"))
print("outlets_dup:", outlets_dup.count(), "filas · inner join:", sales.join(outlets_dup, "Outlet_Identifier", "inner").count(), "filas")

# %% [markdown]
# **2. Las claves nulas nunca cruzan.** Un `NULL` no es igual a nada, ni a otro `NULL`. Un
# empleado sin departamento y un departamento con clave nula no se emparejan: el inner
# join los ignora y el anti join los devuelve.

# %%
emp_null = emp.union(spark.createDataFrame([(7, "Nadie", None)], "emp_id INT, name STRING, dept_id STRING"))
dept_null = dept.union(spark.createDataFrame([(None, "Sin depto")], "dept_id STRING, dept_name STRING"))
print("inner:", emp_null.join(dept_null, "dept_id", "inner").count(), "filas")
emp_null.join(dept_null, "dept_id", "anti").show()

# %% [summary]
