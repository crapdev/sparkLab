## Resumir es colapsar filas

Hasta ahora cada transformación devolvía filas del mismo "grano" que la entrada: un producto, un piloto. Agregar cambia el grano: muchas filas se **colapsan** en una por grupo, y de cada grupo solo queda lo que calcules.

![Cinco filas con Item_Type e Item_MRP se agrupan por tipo y quedan dos filas, una por tipo, con la suma de precios](diagram:groupby-collapse 'groupBy junta las filas que comparten un valor; agg calcula algo sobre cada grupo.')

En PySpark son dos pasos encadenados:

```python
sales.groupBy("Item_Type").agg(F.sum("Item_MRP")).show(3)
```

```output
+-------------+------------------+
|    Item_Type|     sum(Item_MRP)|
+-------------+------------------+
|Starchy Foods|21880.027399999995|
| Baking Goods| 81894.73640000001|
|       Breads| 35379.11979999999|
+-------------+------------------+
only showing top 3 rows
```

- `groupBy("Item_Type")` decide qué filas van juntas. No devuelve un DataFrame, sino un objeto intermedio al que solo se le puede pedir una agregación.
- `agg(F.sum("Item_MRP"))` calcula una o varias cosas por grupo y devuelve el DataFrame con una fila por grupo.

Dos detalles del resultado: la columna se llama como la fórmula, `sum(Item_MRP)`, salvo que le pongas `alias`; y los grupos salen en un orden cualquiera. Si quieres un nombre y un orden, pídelos:

```python
sales.groupBy("Item_Type").agg(F.sum("Item_MRP").alias("total_mrp")).orderBy(F.desc("total_mrp")).show(3)
```

```output
+---------------------+------------------+
|Item_Type            |total_mrp         |
+---------------------+------------------+
|Fruits and Vegetables|178124.08099999998|
|Snack Foods          |175433.92040000003|
|Household            |135976.52539999998|
+---------------------+------------------+
only showing top 3 rows
```

> [!NOTE]
> `groupBy` es una transformación **wide**: para juntar las filas de un mismo grupo hay que moverlas entre particiones, y eso es un shuffle, un stage más. Es el precio de agregar; las agregaciones de un pipeline suelen ser lo que más tarda.

## Las funciones de agregación

Todas viven en `F` y se usan dentro de `agg`:

| Función                      | Devuelve                                    | Con nulos                             |
| ---------------------------- | ------------------------------------------- | ------------------------------------- |
| `F.sum(col)`                 | La suma                                     | Los ignora                            |
| `F.avg(col)` o `F.mean(col)` | La media                                    | Los ignora: divide entre los no nulos |
| `F.min(col)`, `F.max(col)`   | El mínimo y el máximo; también con texto    | Los ignora                            |
| `F.count("*")`               | Número de filas del grupo                   | Las cuenta todas                      |
| `F.count(col)`               | Número de filas con esa columna **no nula** | No las cuenta                         |
| `F.countDistinct(col)`       | Número de valores distintos                 | No cuenta el nulo                     |
| `F.collect_list(col)`        | Un array con todos los valores del grupo    | Los salta                             |
| `F.collect_set(col)`         | Un array con los valores distintos          | Los salta                             |

La diferencia entre `count("*")` y `count(columna)` se ve en BigMart, donde `Item_Weight` tiene 1463 nulos:

```python
sales.agg(F.count("*"), F.count("Item_Weight"), F.countDistinct("Item_Identifier")).show()
```

```output
+--------+------------------+--------------------------------+
|count(1)|count(Item_Weight)|count(DISTINCT Item_Identifier)|
+--------+------------------+--------------------------------+
|    8523|              7060|                            1559|
+--------+------------------+--------------------------------+
```

Y una consecuencia de que `avg` ignore los nulos: la media de `Item_Weight` es 12.86, pero `sum / count("*")` daría 10.65. Spark hace lo correcto por defecto; conviene saber que lo hace.

Un `agg` sin `groupBy` agrega la tabla entera en una fila. Es la forma habitual de sacar un total: `sales.agg(F.sum("Item_MRP")).first()[0]` devuelve `1201681.48`.

## Varias agregaciones y varias claves

`agg` acepta tantas agregaciones como quieras, cada una con su alias, y `groupBy` tantas columnas como haga falta: hay un grupo por cada combinación de valores que exista.

```python
sales.groupBy("Outlet_Identifier").agg(
    F.count("*").alias("items"),
    F.round(F.avg("Item_MRP"), 2).alias("avg_mrp"),
    F.round(F.sum("Item_Outlet_Sales"), 2).alias("total_sales"),
).orderBy(F.desc("total_sales")).show(3)
```

```output
+-----------------+-----+-------+-----------+
|Outlet_Identifier|items|avg_mrp|total_sales|
+-----------------+-----+-------+-----------+
|           OUT027|  935|  139.8| 3453926.05|
|           OUT035|  930| 143.12| 2268122.94|
|           OUT049|  930|  140.3| 2183969.81|
+-----------------+-----+-------+-----------+
only showing top 3 rows
```

Con dos claves, `groupBy("Item_Type", "Outlet_Size")` da 64 grupos: 16 tipos por 4 tamaños, porque **el nulo también forma grupo**. Si no quieres el grupo de los nulos, fíltralos antes con `dropna(subset=["Outlet_Size"])`; quedan 48.

> [!WARNING]
> Después de un `groupBy`, solo existen las columnas de agrupación y las agregadas. Pedir otra, como `agg(F.col("Item_MRP"))`, da `[MISSING_AGGREGATION] The non-aggregating expression "Item_MRP" is based on columns which are not participating in the GROUP BY clause`. Spark no sabe cuál de los valores del grupo darte. Si te da igual cuál, el mensaje sugiere `any_value`; si no, agrega o añade la columna al `groupBy`.

## Listas por grupo: collect_list y collect_set

A veces no quieres un número por grupo sino **los valores**. `collect_list` los junta en un array, repetidos incluidos; `collect_set` quita los repetidos.

```python
books.groupBy("user").agg(F.collect_list("book").alias("all_books"), F.collect_set("book").alias("distinct_books")).show()
```

```output
+-----+---------------------+--------------+
|user |all_books            |distinct_books|
+-----+---------------------+--------------+
|user1|[book1, book2]       |[book2, book1]|
|user2|[book2]              |[book2]       |
|user3|[book1, book3, book1]|[book3, book1]|
+-----+---------------------+--------------+
```

El orden de los elementos dentro del array **no está garantizado**. Si lo necesitas estable, por ejemplo para comparar, envuélvelo en `F.array_sort`. Con BigMart, `collect_set("Outlet_Size")` por `Outlet_Type` dice qué tamaños tiene cada tipo de tienda: `Supermarket Type1` tiene los tres, los demás uno solo.

> [!WARNING]
> `collect_list` sobre un grupo grande crea un array enorme en una sola fila. Con los 5577 productos de `Supermarket Type1` todavía va bien; con millones, es una forma fácil de quedarse sin memoria. Pregúntate si de verdad necesitas la lista o te basta con un conteo.

## Tablas pivotadas

`pivot` convierte los valores de una columna en **columnas nuevas**, como una tabla dinámica de hoja de cálculo. Va entre `groupBy` y `agg`:

![Una tabla larga con Item_Type, Outlet_Size y la media se convierte en una ancha con una columna por tamaño](diagram:pivot-shape 'De formato largo a formato ancho: los valores de Outlet_Size pasan a ser columnas.')

```python
sales.groupBy("Item_Type").pivot("Outlet_Size", ["Small", "Medium", "High"]).agg(F.round(F.avg("Item_MRP"), 2)).show(3)
```

```output
+------------+------+------+------+
|   Item_Type| Small|Medium|  High|
+------------+------+------+------+
|Baking Goods|125.21|126.18| 129.2|
|      Breads|145.52|140.86|133.76|
|   Breakfast|130.57|134.54|147.49|
+------------+------+------+------+
only showing top 3 rows
```

El segundo argumento, la lista de valores, es opcional pero conviene ponerlo por dos motivos:

- **Eliges qué columnas salen y en qué orden.** Sin la lista, Spark saca todos los valores que encuentre, en orden alfabético, y los nulos aparecen como una columna llamada `null`: `['Item_Type', 'null', 'High', 'Medium', 'Small']`.
- **Ahorra trabajo.** Sin la lista, Spark tiene que recorrer los datos una vez más solo para descubrir los valores. Medido en BigMart: 7 jobs sin la lista frente a 3 con ella.

Una celda sin datos queda en `NULL`: si ningún producto de un tipo se vendió en tiendas grandes, su columna `High` está vacía.

> [!EXTRA]
> Con varias agregaciones dentro del `pivot`, las columnas se llaman `valor_alias`: `Tier 1_s`, `Tier 1_n`… Y dentro de un `pivot` no vale `F.count("*")`; usa `F.count(F.lit(1))` o `.count()` directamente.

## Agregar solo lo que cumple una condición

Un truco muy usado: combinar una agregación con un `when`. Como `count` ignora los nulos, `F.count(F.when(condición, 1))` cuenta solo las filas que cumplen la condición; el `when` sin `otherwise` deja las demás en nulo.

```python
sales.groupBy("Item_Type").agg(
    F.count("*").alias("items"),
    F.count(F.when(F.col("Item_Fat_Content") == "Regular", 1)).alias("regular_items"),
    F.sum(F.when(F.col("Item_MRP") > 200, 1).otherwise(0)).alias("expensive_items"),
).orderBy(F.desc("regular_items")).show(3)
```

```output
+---------------------+-----+-------------+---------------+
|Item_Type            |items|regular_items|expensive_items|
+---------------------+-----+-------------+---------------+
|Fruits and Vegetables|1232 |577          |217            |
|Snack Foods          |1200 |485          |216            |
|Frozen Foods         |856  |387          |166            |
+---------------------+-----+-------------+---------------+
only showing top 3 rows
```

`sum(when(...).otherwise(0))` es el mismo conteo escrito de otra forma. La misma idea sirve para medias condicionales: `F.avg(F.when(F.col("Item_Fat_Content") == "Regular", F.col("Item_MRP")))` es el precio medio solo de los productos `Regular`.

## Errores comunes

- **Usar el `sum` de Python en vez de `F.sum`.** Da `TypeError: unsupported operand type(s) for +: 'int' and 'str'`, que no menciona a Spark. Pasa al olvidar la `F.` o al importar con `import *`.
- **Pedir una columna que no está agregada ni en el `groupBy`.** `MISSING_AGGREGATION`. Agrégala o añádela al `groupBy`.
- **Olvidar el alias.** Columnas llamadas `sum(Item_MRP)` o `avg(Item_Weight)`, incómodas de usar después.
- **Esperar los grupos ordenados.** Salen en cualquier orden; añade `orderBy`.
- **`count("columna")` creyendo que cuenta filas.** Cuenta no nulos. Para filas, `count("*")`.
- **`pivot` sin la lista de valores en datos grandes.** Una pasada extra y una columna `null`.
- **`collect_list` sobre grupos enormes.** Arrays gigantes en una fila: memoria.
- **Hacer `select` o `show` sobre el `groupBy`.** `GroupedData` no tiene esos métodos: falta el `agg` (o un `.count()`).
