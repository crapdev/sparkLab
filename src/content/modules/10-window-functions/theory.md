## Calcular por fila mirando a las vecinas

`groupBy` resume: muchas filas se convierten en una. Pero hay preguntas que necesitan **las dos cosas a la vez**: cada fila y algo calculado sobre sus vecinas. "¿Qué puesto ocupa este producto en su tienda?", "¿cuánto llevamos acumulado hasta esta venta?", "¿qué porcentaje del total de la tienda es esta fila?". Para eso están las window functions: una **ventana** es el conjunto de filas que Spark mira para calcular el valor de cada fila, y el resultado conserva todas las filas.

Se escriben en dos partes: la función y la ventana sobre la que actúa, con `.over(...)`.

```python
from pyspark.sql.window import Window

sales.withColumn("row_num", F.row_number().over(Window.orderBy("Item_Identifier", "Outlet_Identifier")))
```

La ventana se construye con hasta tres piezas:

| Pieza         | Qué decide                                                      | Ejemplo                                                      |
| ------------- | --------------------------------------------------------------- | ------------------------------------------------------------ |
| `partitionBy` | En qué grupos se parte la ventana (empieza de cero en cada uno) | `Window.partitionBy("Outlet_Identifier")`                    |
| `orderBy`     | En qué orden se recorren las filas de la ventana                | `.orderBy(F.desc("Item_Outlet_Sales"))`                      |
| `rowsBetween` | Qué filas entran en el cálculo de cada fila: el **marco**       | `.rowsBetween(Window.unboundedPreceding, Window.currentRow)` |

Todo el módulo usa dos juegos de datos: `scores`, seis jugadores con puntos y equipo, y BigMart. En BigMart, la pareja `Item_Identifier` + `Outlet_Identifier` es única, y eso importa: una ventana ordenada por una columna con repetidos deja **empates**, y con empates `row_number` reparte los números como le llegan. Desempata siempre.

```python
scores = spark.createDataFrame(
    [("Ana", "A", 90), ("Luis", "A", 90), ("Marta", "B", 85), ("Pedro", "A", 85), ("Sofía", "B", 70), ("Jorge", "B", 60)],
    "name STRING, team STRING, points INT",
)
```

## Numerar y clasificar: row_number, rank, dense_rank

Las tres dan un número a cada fila siguiendo el `orderBy` de la ventana. Se diferencian en qué hacen con los empates:

![Seis jugadores ordenados por puntos con las columnas row_number, rank y dense_rank: los empates comparten número en rank y dense_rank](diagram:rank-vs-dense 'row_number nunca repite; rank y dense_rank dan el mismo número a los empatados, y solo rank salta después.')

```python
by_points = Window.orderBy(F.desc("points"))
scores.withColumn("row_number", F.row_number().over(by_points)).withColumn("rank", F.rank().over(by_points)).withColumn("dense_rank", F.dense_rank().over(by_points)).show()
```

```output
+-----+----+------+----------+----+----------+
| name|team|points|row_number|rank|dense_rank|
+-----+----+------+----------+----+----------+
|  Ana|   A|    90|         1|   1|         1|
| Luis|   A|    90|         2|   1|         1|
|Marta|   B|    85|         3|   3|         2|
|Pedro|   A|    85|         4|   3|         2|
|Sofía|   B|    70|         5|   5|         3|
|Jorge|   B|    60|         6|   6|         4|
+-----+----+------+----------+----+----------+
```

- **`row_number`** da siempre 1, 2, 3… Con empate, quién recibe el 1 depende de cómo lleguen las filas: si necesitas que sea reproducible, añade columnas al `orderBy` hasta que el orden sea único.
- **`rank`** da el mismo número a los empatados y luego **salta** los números consumidos: 1, 1, 3.
- **`dense_rank`** da el mismo número a los empatados y **no salta**: 1, 1, 2. Su máximo es el número de valores distintos.

En BigMart, ordenando por `Item_Identifier` descendente, `NCZ54` es el último producto alfabéticamente y está en siete tiendas: sus siete filas tienen `rank` 1 y `dense_rank` 1, y el siguiente producto, `NCZ53`, recibe `rank` 8 y `dense_rank` 2. El `dense_rank` máximo es 1559, uno por producto; el `rank` máximo, 8518.

> [!WARNING]
> Las tres funciones exigen una ventana **ordenada**. Sin `orderBy` da `[WINDOW_FUNCTION_FRAME_NOT_ORDERED] Window function row_number requires the window to be ordered`. Y una ventana sin `partitionBy` obliga a Spark a mover **todos los datos a una sola partición** para numerarlos de seguido: con 8523 filas no se nota, con millones es un cuello de botella. Los logs lo avisan con `No Partition Defined for Window operation`.

## Partir la ventana: partitionBy

`partitionBy` divide las filas en grupos y la función empieza de cero en cada uno. Con `orderBy` dentro de cada grupo, tienes el patrón más usado de todo el módulo, el **top N por grupo**:

```python
by_team = Window.partitionBy("team").orderBy(F.desc("points"), "name")
scores.withColumn("rank_in_team", F.row_number().over(by_team)).show()
```

```output
+-----+----+------+------------+
| name|team|points|rank_in_team|
+-----+----+------+------------+
|  Ana|   A|    90|           1|
| Luis|   A|    90|           2|
|Pedro|   A|    85|           3|
|Marta|   B|    85|           1|
|Sofía|   B|    70|           2|
|Jorge|   B|    60|           3|
+-----+----+------+------------+
```

Un `filter(F.col("rank_in_team") <= 2)` deja los dos mejores de cada equipo. En BigMart, numerando dentro de cada `Outlet_Identifier` por `Item_Outlet_Sales` descendente y filtrando `<= 3`, quedan 30 filas, 3 por tienda; en `OUT027` ganan `NCE42` (13086.96), `FDQ19` (12117.56) y `FDZ20` (11445.10).

El mismo patrón con N = 1 es la forma de **deduplicar eligiendo** qué fila sobrevive. `dropDuplicates(["Item_Identifier"])` deja una fila por producto, pero una cualquiera; con `row_number` sobre `Window.partitionBy("Item_Identifier").orderBy(F.desc("Item_Outlet_Sales"), "Outlet_Identifier")` y `filter(rn == 1)` te quedas con la tienda donde más vendió, y el desempate por `Outlet_Identifier` hace el resultado reproducible: `FDA15` vende 6474.2392 en tres tiendas y se queda con `OUT013`.

> [!TIP]
> La window function no se puede usar dentro de `filter`: `[WINDOW_FUNCTION_NOT_ALLOWED_IN_CLAUSE] It is not allowed to use window functions inside WHERE clause`. Primero la calculas en una columna con `withColumn`, después filtras por esa columna, y al final la quitas con `drop` si no la quieres.

## Agregar sin colapsar

Cualquier agregación, `F.sum`, `F.avg`, `F.max`, `F.count`, también acepta `.over(...)`. La diferencia con `groupBy` es que **las filas no desaparecen**: cada una recibe el resultado de agregar su ventana.

![scores agrupado por equipo da 2 filas; con una ventana por equipo siguen las 6 filas y cada una lleva el total de su equipo](diagram:window-vs-groupby 'groupBy colapsa; la ventana conserva las filas y añade el total del grupo a cada una.')

Con `partitionBy` y sin `orderBy`, la ventana es el grupo entero, y el resultado es el total del grupo pegado en cada fila. Es lo que necesitas para calcular el peso de cada fila dentro de su grupo:

```python
by_outlet = Window.partitionBy("Outlet_Identifier")
sales.withColumn("outlet_total", F.sum("Item_Outlet_Sales").over(by_outlet)).withColumn(
    "share_pct", F.round(F.col("Item_Outlet_Sales") / F.col("outlet_total") * 100, 2)
).select("Item_Identifier", "Outlet_Identifier", "Item_Outlet_Sales", "outlet_total", "share_pct").show(3)
```

```output
+---------------+-----------------+-----------------+------------------+---------+
|Item_Identifier|Outlet_Identifier|Item_Outlet_Sales|      outlet_total|share_pct|
+---------------+-----------------+-----------------+------------------+---------+
|          FDX07|           OUT010|           732.38|188340.17240000013|     0.39|
|          FDE51|           OUT010|         178.4344|188340.17240000013|     0.09|
|          FDV38|           OUT010|         163.7868|188340.17240000013|     0.09|
+---------------+-----------------+-----------------+------------------+---------+
only showing top 3 rows
```

Siguen siendo 8523 filas con 10 totales distintos, uno por tienda. Con `groupBy` tendrías los 10 totales en 10 filas y harías falta un `join` para volver a pegarlos a las ventas.

## El marco: qué filas entran en el cálculo

Cuando la ventana tiene `orderBy`, Spark no agrega el grupo entero sino un **marco**: un tramo de filas alrededor de la actual. Lo defines con `rowsBetween(inicio, fin)`, y las tres marcas que usarás son `Window.unboundedPreceding` (desde la primera fila), `Window.currentRow` (la fila actual) y `Window.unboundedFollowing` (hasta la última). Una suma acumulada es el marco que va desde el principio hasta la fila actual:

![Cinco instantáneas del marco de una suma acumulada: en cada fila el marco incluye una fila más y la suma crece 10, 30, 45, 50, 80](diagram:window-frame 'El marco crece fila a fila; cada fila recibe la suma de su marco.')

```python
daily = spark.createDataFrame([(1, 10.0), (2, 20.0), (3, 15.0), (4, 5.0), (5, 30.0)], "day INT, amount DOUBLE")
by_day = Window.orderBy("day")
daily.withColumn("running", F.sum("amount").over(by_day.rowsBetween(Window.unboundedPreceding, Window.currentRow))).withColumn(
    "moving3", F.sum("amount").over(by_day.rowsBetween(-2, 0))
).withColumn("total", F.sum("amount").over(by_day.rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing))).show()
```

```output
+---+------+-------+-------+-----+
|day|amount|running|moving3|total|
+---+------+-------+-------+-----+
|  1|  10.0|   10.0|   10.0| 80.0|
|  2|  20.0|   30.0|   30.0| 80.0|
|  3|  15.0|   45.0|   45.0| 80.0|
|  4|   5.0|   50.0|   40.0| 80.0|
|  5|  30.0|   80.0|   50.0| 80.0|
+---+------+-------+-------+-----+
```

- `rowsBetween(unboundedPreceding, currentRow)`: suma acumulada.
- `rowsBetween(-2, 0)`: las dos filas anteriores y la actual, la base de una media móvil.
- `rowsBetween(unboundedPreceding, unboundedFollowing)`: todas las filas, el total en cada una. En BigMart, 1201681.48 en las 8523 filas.

En BigMart, la suma acumulada de `Item_MRP` ordenando por `Item_Type`, `Item_Identifier` y `Outlet_Identifier` empieza en `FDA11` de `Baking Goods`: 94.34, 187.49, 282.23… y termina en el total general, 1201681.48.

### Qué pasa sin marco

Muchos tutoriales enseñan que `F.sum("Item_MRP").over(Window.orderBy("Item_Type"))`, sin marco, "repite el total de cada tipo en sus filas". No es exactamente eso. Con `orderBy` y sin marco, el marco por defecto va **desde el principio hasta la fila actual, incluyendo sus empates**: todas las filas con el mismo valor de orden comparten resultado, y ese resultado acumula los valores anteriores.

```python
sales.withColumn("cum_mrp", F.round(F.sum("Item_MRP").over(Window.orderBy("Item_Type")), 2)).select("Item_Type", "cum_mrp").distinct().orderBy("Item_Type").show(3)
```

```output
+------------+---------+
|   Item_Type|  cum_mrp|
+------------+---------+
|Baking Goods| 81894.74|
|      Breads|117273.86|
|   Breakfast|132870.55|
+------------+---------+
only showing top 3 rows
```

Las filas de `Baking Goods` sí llevan el total de `Baking Goods` (81894.74), porque es el primer tipo. Pero las de `Breads` llevan `Baking Goods` más `Breads` (117273.86), no los 35379.12 de `Breads`. Para un total por tipo, quita el `orderBy` y usa `partitionBy("Item_Type")`; para un acumulado fila a fila, pon el marco y un orden sin empates.

> [!EXTRA]
> `rangeBetween` define el marco por **valor** en vez de por número de filas: `rangeBetween(-7, 0)` sobre una columna de días son "los últimos 7 días", tenga las filas que tenga. Exige que el `orderBy` sea numérico o de fecha: sobre texto da `DATATYPE_MISMATCH.SPECIFIED_WINDOW_FRAME_UNACCEPTED_TYPE`. El marco por defecto con `orderBy` es, de hecho, un `rangeBetween(unboundedPreceding, currentRow)`, y por eso los empates comparten valor.

## Mirar a la fila de al lado: lag y lead

`F.lag("col")` trae el valor de la fila anterior dentro de la ventana y `F.lead("col")` el de la siguiente. La primera fila no tiene anterior y recibe `NULL`, salvo que pases un valor por defecto: `F.lag("amount", 1, 0)`.

```python
daily.withColumn("prev", F.lag("amount").over(by_day)).withColumn("next", F.lead("amount").over(by_day)).withColumn("diff", F.col("amount") - F.lag("amount", 1, 0).over(by_day)).show()
```

```output
+---+------+----+----+-----+
|day|amount|prev|next| diff|
+---+------+----+----+-----+
|  1|  10.0|NULL|20.0| 10.0|
|  2|  20.0|10.0|15.0| 10.0|
|  3|  15.0|20.0| 5.0| -5.0|
|  4|   5.0|15.0|30.0|-10.0|
|  5|  30.0| 5.0|NULL| 25.0|
+---+------+----+----+-----+
```

Es la forma de calcular diferencias entre filas consecutivas: ventas de hoy menos ventas de ayer, o cuánto cambió un producto de una tienda a la siguiente con `Window.partitionBy("Item_Identifier").orderBy("Outlet_Identifier")`.

> [!NOTE]
> Una window function con `partitionBy` es una transformación **wide**: Spark reparte las filas por la clave de partición (shuffle) y las ordena dentro de cada grupo. Medido en BigMart: 2 jobs y 3 stages, con o sin `partitionBy`. La diferencia está en el paralelismo: sin `partitionBy`, todas las filas pasan por una sola tarea.

## Errores comunes

- **Ventana sin `orderBy` con `row_number`, `rank` o `lag`.** `WINDOW_FUNCTION_FRAME_NOT_ORDERED`. Estas funciones necesitan saber qué fila va antes.
- **Window function dentro de `filter`.** `WINDOW_FUNCTION_NOT_ALLOWED_IN_CLAUSE`. Calcúlala en una columna y filtra después.
- **Olvidar `.over()`.** `WINDOW_FUNCTION_WITHOUT_OVER_CLAUSE`. Y pasarle un texto en vez de una ventana, `.over("Item_Identifier")`, da `NOT_EXPECTED_TYPE`.
- **`row_number` con empates sin desempatar.** Funciona, pero el resultado cambia entre ejecuciones. Añade columnas al `orderBy`.
- **Esperar un total por grupo con `orderBy` y sin marco.** Da un acumulado con empates. Para el total del grupo, `partitionBy` sin `orderBy`.
- **Sin `partitionBy` en datos grandes.** Una sola partición, una sola tarea. Parte la ventana siempre que la pregunta lo permita.
- **Confundir `rank` y `dense_rank`.** Los dos empatan igual; solo `rank` salta números después del empate.
