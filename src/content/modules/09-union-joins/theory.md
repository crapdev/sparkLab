## Dos formas de combinar

Hasta ahora cada módulo trabajaba con un solo DataFrame. En la práctica los datos vienen repartidos: las ventas de enero y las de febrero, los productos en una tabla y las tiendas en otra. Hay dos maneras de juntarlos, y conviene no confundirlas:

- **Apilar** filas: `union` pone un DataFrame debajo de otro. Mismas columnas, más filas.
- **Cruzar** tablas: `join` empareja las filas de dos DataFrames que comparten un valor en una columna, la **clave**. Más columnas, y un número de filas que depende del tipo de join.

Todo el módulo usa dos tablas de juguete que caben en pantalla: `emp`, seis empleados con su departamento, y `dept`, cinco departamentos. Fíjate en los detalles: `d03` tiene dos empleados, Jorge está en `d06`, que no existe en `dept`, y `Legal` (`d04`) no tiene a nadie.

```python
emp = spark.createDataFrame(
    [(1, "Ana", "d01"), (2, "Luis", "d02"), (3, "Marta", "d03"), (4, "Pedro", "d03"), (5, "Sofía", "d05"), (6, "Jorge", "d06")],
    "emp_id INT, name STRING, dept_id STRING",
)
dept = spark.createDataFrame(
    [("d01", "Ventas"), ("d02", "Marketing"), ("d03", "Datos"), ("d04", "Legal"), ("d05", "Soporte")],
    "dept_id STRING, dept_name STRING",
)
```

## Apilar filas: union y unionByName

`union` junta las filas de dos DataFrames **por posición**: la primera columna bajo la primera, la segunda bajo la segunda. No mira los nombres. Si los dos DataFrames tienen las columnas en el mismo orden, funciona; si no, mezcla los datos sin avisar.

![union empareja las columnas por posición y pone los nombres bajo dept_id; unionByName las empareja por nombre](diagram:union-by-position 'Con las columnas en otro orden, union mezcla los datos y unionByName los coloca bien. Las dos devuelven 8 filas.')

```python
new_hires = spark.createDataFrame([(7, "d02", "Elena"), (8, "d04", "Hugo")], "emp_id INT, dept_id STRING, name STRING")
emp.union(new_hires).show()
```

```output
+------+-----+-------+
|emp_id| name|dept_id|
+------+-----+-------+
|     1|  Ana|    d01|
|     2| Luis|    d02|
|     3|Marta|    d03|
|     4|Pedro|    d03|
|     5|Sofía|    d05|
|     6|Jorge|    d06|
|     7|  d02|  Elena|
|     8|  d04|   Hugo|
+------+-----+-------+
```

Elena ha acabado en `dept_id` y su departamento en `name`. No hay error porque las dos columnas son de texto. `unionByName` empareja las columnas **por nombre**, y es la forma que deberías usar siempre:

```python
emp.unionByName(new_hires).show()
```

```output
+------+-----+-------+
|emp_id| name|dept_id|
+------+-----+-------+
|     1|  Ana|    d01|
|     2| Luis|    d02|
|     3|Marta|    d03|
|     4|Pedro|    d03|
|     5|Sofía|    d05|
|     6|Jorge|    d06|
|     7|Elena|    d02|
|     8| Hugo|    d04|
+------+-----+-------+
```

El orden de las columnas del resultado lo marca el DataFrame de la izquierda. Tres detalles más:

- **`union` no quita duplicados.** `emp.union(emp)` tiene 12 filas; con `.distinct()` vuelven a ser 6. En SQL, `UNION` sí los quita; en Spark, `union` y `unionAll` son lo mismo.
- **El número de columnas tiene que coincidir.** `emp.union(dept)` da `[NUM_COLUMNS_MISMATCH] UNION can only be performed on inputs with the same number of columns, but the first input has 3 columns and the second input has 2 columns`.
- **Los tipos también cuentan.** Si por posición cae una columna de texto bajo una numérica, Spark intenta convertir el texto a número y, con ANSI activado, falla al ejecutar con `CAST_INVALID_INPUT`. Es un error tardío y confuso; `unionByName` lo evita de raíz.

> [!EXTRA]
> Si un DataFrame tiene columnas que al otro le faltan, `unionByName(otro, allowMissingColumns=True)` las rellena con `NULL` en vez de fallar con `UNRESOLVED_COLUMN_AMONG_FIELD_NAMES`.

## Cruzar tablas: la clave de unión

Un `join` necesita tres cosas: el DataFrame de la **derecha**, la **condición** que dice cuándo dos filas se emparejan y el **tipo** de join, que decide qué pasa con las filas que no encuentran pareja.

```python
emp.join(dept, "dept_id", "inner")
```

La condición más habitual es "la misma columna en los dos lados", y se escribe con el nombre de esa columna como texto. El tipo por defecto es `inner`. Lo que cambia entre un tipo y otro son las filas que sobreviven; los cuatro que vas a usar a diario son estos:

| Tipo    | Conserva                                        | Con `emp` y `dept` | Columnas                  |
| ------- | ----------------------------------------------- | ------------------ | ------------------------- |
| `inner` | Solo las filas cuya clave está en los dos lados | 5 filas            | Las de los dos DataFrames |
| `left`  | Todas las de la izquierda, cruzadas o no        | 6 filas            | Las de los dos DataFrames |
| `right` | Todas las de la derecha, cruzadas o no          | 6 filas            | Las de los dos DataFrames |
| `anti`  | Las de la izquierda que **no** tienen pareja    | 1 fila             | Solo las de la izquierda  |

### Inner join

![emp y dept cruzados con inner: 5 filas, d03 dos veces, sin Jorge ni Legal](diagram:join-inner 'Inner: solo las claves que existen en los dos lados.')

```python
emp.join(dept, "dept_id", "inner").show()
```

```output
+-------+------+-----+---------+
|dept_id|emp_id| name|dept_name|
+-------+------+-----+---------+
|    d01|     1|  Ana|   Ventas|
|    d02|     2| Luis|Marketing|
|    d03|     3|Marta|    Datos|
|    d03|     4|Pedro|    Datos|
|    d05|     5|Sofía|  Soporte|
+-------+------+-----+---------+
```

`d03` aparece dos veces porque dos empleados la tienen: cada fila de la izquierda se empareja con **cada** fila de la derecha que tenga su clave. Jorge (`d06`) y Legal (`d04`) desaparecen sin aviso. Esa es la trampa del inner join: pierde filas en silencio.

### Left y right

![emp y dept cruzados con left: 6 filas, Jorge con dept_name nulo](diagram:join-left 'Left: todas las filas de la izquierda; lo que no cruza sale con NULL.')

```python
emp.join(dept, "dept_id", "left").show()
```

```output
+-------+------+-----+---------+
|dept_id|emp_id| name|dept_name|
+-------+------+-----+---------+
|    d01|     1|  Ana|   Ventas|
|    d02|     2| Luis|Marketing|
|    d03|     3|Marta|    Datos|
|    d03|     4|Pedro|    Datos|
|    d05|     5|Sofía|  Soporte|
|    d06|     6|Jorge|     NULL|
+-------+------+-----+---------+
```

`left` promete no perder ninguna fila de la izquierda: Jorge sale con `NULL` en todo lo que venía de `dept`. Es el join de **enriquecer**: tienes una tabla principal y quieres añadirle columnas de otra sin perder nada. `right` es lo mismo con los papeles cambiados:

![emp y dept cruzados con right: 6 filas, Legal con emp_id y name nulos](diagram:join-right 'Right: todas las filas de la derecha; Legal sale con NULL en lo que venía de emp.')

```python
emp.join(dept, "dept_id", "right").orderBy("dept_id").show()
```

```output
+-------+------+-----+---------+
|dept_id|emp_id| name|dept_name|
+-------+------+-----+---------+
|    d01|     1|  Ana|   Ventas|
|    d02|     2| Luis|Marketing|
|    d03|     3|Marta|    Datos|
|    d03|     4|Pedro|    Datos|
|    d04|  NULL| NULL|    Legal|
|    d05|     5|Sofía|  Soporte|
+-------+------+-----+---------+
```

`a.join(b, k, "right")` devuelve las mismas filas que `b.join(a, k, "left")`, solo cambia el orden de las columnas. Mucha gente escribe siempre `left` y pone a la izquierda la tabla que no quiere perder; es más fácil de leer.

### Anti join: lo que falta

![emp y dept cruzados con anti: 1 fila, Jorge, solo con las columnas de emp](diagram:join-anti 'Anti: las filas de la izquierda que no cruzan con nada. No añade columnas.')

```python
emp.join(dept, "dept_id", "anti").show()
```

```output
+-------+------+-----+
|dept_id|emp_id| name|
+-------+------+-----+
|    d06|     6|Jorge|
+-------+------+-----+
```

`anti` responde a "¿qué filas de la izquierda no tienen pareja?". Devuelve solo columnas de la izquierda, y nunca más filas de las que había. Es la herramienta para comprobar datos: empleados sin departamento válido, ventas de una tienda que no está en el catálogo. En la otra dirección, `dept.join(emp, "dept_id", "anti")` devuelve `Legal`, el departamento sin empleados.

> [!EXTRA]
> Hay dos tipos más. `full` conserva las filas de los dos lados, cruzadas o no: con `emp` y `dept` son 7 filas, Jorge y Legal incluidos. `semi` es el contrario de `anti`: las filas de la izquierda que **sí** tienen pareja, sin añadir columnas de la derecha ni multiplicar filas. Es un filtro con otra tabla.
>
> ![full: 7 filas con Jorge y Legal](diagram:join-full 'Full: todas las filas de los dos lados.')
>
> ![semi: 5 filas de emp, sin columnas de dept](diagram:join-semi 'Semi: las filas de emp cuya clave está en dept, sin traer nada de dept.')
>
> Los nombres largos también valen: `left_outer`, `right_outer`, `full_outer`, `left_anti`, `left_semi`. Un tipo mal escrito da `[UNSUPPORTED_JOIN_TYPE] Unsupported join type 'lefty'`, con la lista completa.

## La clave repetida y la ambigüedad

Hay otra forma de escribir la condición, más explícita: comparar las dos columnas con `==`. Muchos tutoriales la usan, y conviene conocerla porque tiene un efecto secundario.

```python
emp.join(dept, emp["dept_id"] == dept["dept_id"], "inner").show()
```

```output
+------+-----+-------+-------+---------+
|emp_id| name|dept_id|dept_id|dept_name|
+------+-----+-------+-------+---------+
|     1|  Ana|    d01|    d01|   Ventas|
|     2| Luis|    d02|    d02|Marketing|
|     3|Marta|    d03|    d03|    Datos|
|     4|Pedro|    d03|    d03|    Datos|
|     5|Sofía|    d05|    d05|  Soporte|
+------+-----+-------+-------+---------+
```

La clave sale **dos veces**, una por tabla, y el resultado trae todas las columnas de los dos DataFrames en orden. En cuanto pides `dept_id` por nombre, Spark no sabe a cuál te refieres:

```python
emp_dept.select("dept_id").show()
```

```output
AnalysisException: [AMBIGUOUS_REFERENCE] Reference `dept_id` is ambiguous, could be: [`dept_id`, `dept_id`].
```

Tres salidas, de más a menos recomendable:

- **Unir por nombre de columna**, `emp.join(dept, "dept_id", "inner")`. La clave sale una sola vez y la primera. Es lo que has visto en las secciones anteriores, y lo que usa el laboratorio.
- **Decir de qué tabla viene**: `emp_dept.select("name", emp["dept_id"], "dept_name")`.
- **Tirar una de las dos** después del join: `emp_dept.drop(dept["dept_id"])`. Ojo, `drop("dept_id")` las tira las dos.

La forma explícita sigue haciendo falta cuando la clave **se llama distinto** en cada tabla (`emp["dept_id"] == dept["id"]`) o cuando la condición tiene más de una comparación. Para varias claves con el mismo nombre, una lista: `a.join(b, ["k1", "k2"], "inner")`.

> [!WARNING]
> Un `join` sin condición, `emp.join(dept)`, no falla: hace el producto cartesiano. Con 6 y 5 filas son 30; con dos tablas de un millón son un billón. Si ves un resultado enorme, revisa la condición.

## Con BigMart: ventas por un lado, tiendas por otro

A partir de este módulo hay un segundo archivo, `outlets.csv`, con una fila por tienda. Cuatro de sus columnas ya están en las ventas, porque BigMart las repite en cada fila: `Outlet_Establishment_Year`, `Outlet_Size`, `Outlet_Location_Type` y `Outlet_Type`. Las otras tres, `City`, `Manager` y `Staff`, **son inventadas para el curso** y no existen en las ventas: son las que hacen útil el join.

```output
+-----------------+-------------------------+-----------+--------------------+-----------------+----------+------------+-----+
|Outlet_Identifier|Outlet_Establishment_Year|Outlet_Size|Outlet_Location_Type|Outlet_Type      |City      |Manager     |Staff|
+-----------------+-------------------------+-----------+--------------------+-----------------+----------+------------+-----+
|OUT010           |1998                     |NULL       |Tier 3              |Grocery Store    |Nagpur    |Priya Nair  |12   |
|OUT013           |1987                     |High       |Tier 3              |Supermarket Type1|Indore    |Rahul Mehta |48   |
|OUT017           |2007                     |NULL       |Tier 2              |Supermarket Type1|Jaipur    |Anjali Rao  |35   |
|OUT018           |2009                     |Medium     |Tier 3              |Supermarket Type2|Nashik    |Vikram Singh|40   |
|OUT027           |1985                     |Medium     |Tier 3              |Supermarket Type3|Bhopal    |Neha Kapoor |60   |
|OUT035           |2004                     |Small      |Tier 2              |Supermarket Type1|Pune      |Arjun Desai |30   |
|OUT045           |2002                     |NULL       |Tier 2              |Supermarket Type1|Lucknow   |Kavita Joshi|33   |
|OUT046           |1997                     |Small      |Tier 1              |Supermarket Type1|Mumbai    |Sanjay Iyer |28   |
|OUT049           |1999                     |Medium     |Tier 1              |Supermarket Type1|Delhi     |Meera Pillai|42   |
|OUT099           |2012                     |Small      |Tier 2              |Supermarket Type1|Chandigarh|Rohan Bhatt |25   |
+-----------------+-------------------------+-----------+--------------------+-----------------+----------+------------+-----+
```

La tabla no cuadra del todo con las ventas, a propósito: `OUT019`, que vende 528 filas, **no está**, y `OUT099` está pero **no vende nada**. Es lo normal en datos reales, y es justo lo que distingue un tipo de join de otro.

Si cruzas `sales` con `outlets` entera por `Outlet_Identifier`, las otras cuatro columnas compartidas vuelven a salir duplicadas (19 columnas) y `Outlet_Type` se vuelve ambigua. La costumbre es **seleccionar de la tabla pequeña solo la clave y lo que aporta** antes del join:

```python
outlet_info = outlets.select("Outlet_Identifier", "City", "Manager", "Staff")
sales.join(outlet_info, "Outlet_Identifier", "inner").select("Item_Identifier", "Outlet_Identifier", "Item_Outlet_Sales", "City", "Manager").show(5)
```

```output
+---------------+-----------------+-----------------+------+------------+
|Item_Identifier|Outlet_Identifier|Item_Outlet_Sales|  City|     Manager|
+---------------+-----------------+-----------------+------+------------+
|          FDA15|           OUT049|         3735.138| Delhi|Meera Pillai|
|          DRC01|           OUT018|         443.4228|Nashik|Vikram Singh|
|          FDN15|           OUT049|          2097.27| Delhi|Meera Pillai|
|          FDX07|           OUT010|           732.38|Nagpur|  Priya Nair|
|          NCD19|           OUT013|         994.7052|Indore| Rahul Mehta|
+---------------+-----------------+-----------------+------+------------+
only showing top 5 rows
```

Los conteos de cada tipo, medidos sobre 8523 ventas y 10 tiendas:

| Join                                    | Filas | Por qué                                                         |
| --------------------------------------- | ----- | --------------------------------------------------------------- |
| `sales.join(outlet_info, key, "inner")` | 7995  | Se pierden las 528 ventas de `OUT019`, que no está en `outlets` |
| `sales.join(outlet_info, key, "left")`  | 8523  | Ninguna venta se pierde; 528 filas con `City` a `NULL`          |
| `sales.join(outlet_info, key, "right")` | 7996  | 7995 cruzadas más `OUT099`, con las columnas de venta a `NULL`  |
| `sales.join(outlet_info, key, "full")`  | 8524  | 8523 ventas más la fila de `OUT099`                             |
| `sales.join(outlets, key, "anti")`      | 528   | Las ventas sin tienda en el catálogo: todas de `OUT019`         |
| `outlets.join(sales, key, "anti")`      | 1     | La tienda que no vende: `OUT099`                                |

Con `inner` desaparecen 528 ventas sin que nada lo diga: si tu objetivo es enriquecer las ventas, el join es `left`, y después un `filter(F.col("City").isNull())` te dice qué quedó sin cruzar. Y una vez cruzadas, el `groupBy` del módulo anterior responde preguntas nuevas:

```python
sales.join(outlet_info, "Outlet_Identifier", "inner").groupBy("City").agg(F.round(F.sum("Item_Outlet_Sales"), 2).alias("total_sales")).orderBy(F.desc("total_sales")).show(3)
```

```output
+------+-----------+
|  City|total_sales|
+------+-----------+
|Bhopal| 3453926.05|
|  Pune| 2268122.94|
| Delhi| 2183969.81|
+------+-----------+
only showing top 3 rows
```

## Dos trampas que no dan error

**Las claves repetidas multiplican.** Cada fila de un lado se empareja con cada fila del otro que tenga su clave. Si en `dept` hubiera dos filas `d03`, Marta y Pedro saldrían dos veces cada uno: 7 filas en vez de 5. En BigMart, con `OUT049` duplicada en `outlets`, el inner join pasa de 7995 a 8925 filas: 930 de más, una por cada venta de esa tienda. Un left join tampoco te protege: también crece. Antes de cruzar, comprueba que la clave es única en la tabla de referencia, por ejemplo con `dropDuplicates(["Outlet_Identifier"])`.

**Las claves nulas nunca cruzan.** `NULL` no es igual a nada, ni siquiera a otro `NULL`. Un empleado con `dept_id` nulo y un departamento con clave nula no se emparejan: el inner join los ignora, el left los deja con nulos y el anti los devuelve. Si de verdad quieres que dos nulos se consideren iguales, la condición explícita tiene `emp["dept_id"].eqNullSafe(dept["dept_id"])`.

> [!NOTE]
> `join` es una transformación **wide**: para emparejar claves, Spark tiene que llevar las filas con la misma clave a la misma partición, y eso es un shuffle. Cuando una de las tablas es pequeña, como `outlets`, Spark la copia entera a cada executor (un _broadcast join_) y se ahorra el shuffle de la grande. Se ve en `explain()` como `BroadcastHashJoin`. El módulo de rendimiento vuelve sobre esto.

## Errores comunes

- **`union` con las columnas en otro orden.** Mezcla los datos sin avisar. Usa `unionByName`.
- **Esperar que `union` quite duplicados.** No lo hace: añade `distinct()` si lo necesitas.
- **`inner` cuando querías enriquecer.** Pierde las filas sin pareja en silencio. Para no perder nada, `left`.
- **Pedir la clave por nombre tras una condición explícita.** `AMBIGUOUS_REFERENCE`. Une por nombre de columna, o califica con `emp["dept_id"]`.
- **Cruzar con una tabla cuya clave no es única.** Las filas se multiplican. Comprueba la clave con `dropDuplicates` o un `groupBy().count()`.
- **Cruzar con la tabla entera cuando ya compartes columnas.** Columnas duplicadas y ambiguas. Selecciona de la tabla pequeña solo la clave y lo nuevo.
- **Confiar en que las claves nulas cruzan.** Nunca lo hacen. Si hace falta, `eqNullSafe`.
- **Un `join` sin condición.** Producto cartesiano: todas las filas con todas.
