## Una columna que contiene una lista

Hasta ahora cada celda tenía un valor: un texto, un número, una fecha. Spark también admite columnas cuyo valor es una **lista**, el tipo `array`. Aparecen al leer JSON con listas dentro, al agrupar con `collect_list`, y sobre todo al **partir texto**.

```python
parts = sales.withColumn("type_parts", F.split("Outlet_Type", " "))
parts.select("Outlet_Type", "type_parts").distinct().show(truncate=False)
```

```output
+-----------------+--------------------+
|Outlet_Type      |type_parts          |
+-----------------+--------------------+
|Grocery Store    |[Grocery, Store]    |
|Supermarket Type1|[Supermarket, Type1]|
|Supermarket Type2|[Supermarket, Type2]|
|Supermarket Type3|[Supermarket, Type3]|
+-----------------+--------------------+
```

En el esquema, un array dice de qué tipo son sus elementos:

```output
root
 |-- type_parts: array (nullable = true)
 |    |-- element: string (containsNull = false)
```

## split: el separador es una regex

`F.split(columna, separador)` parte un texto y devuelve un `array<string>`. El segundo argumento no es un texto literal sino una **expresión regular**, igual que en `regexp_replace`. Con un espacio no se nota; con un punto o una barra vertical, sí:

```python
versions.select(F.split("version", ".").alias("wrong"), F.split("version", "\\.").alias("right")).show()
```

```output
+------------+---------+
|       wrong|    right|
+------------+---------+
|[, , , , , ]|[4, 2, 0]|
+------------+---------+
```

`.` significa "cualquier carácter", así que parte por todas partes y deja trozos vacíos. `|` significa "o" y parte entre cada carácter. Los dos se escapan con `\\`.

> [!EXTRA]
> `split` acepta un tercer argumento, el número máximo de trozos: `F.split("version", "\\.", 2)` devuelve `[4, 2.0]`. Y el camino de vuelta es `F.concat_ws("-", "type_parts")` o `F.array_join("type_parts", "-")`, que pegan los elementos con un separador.

## Un elemento por su posición

Los elementos se piden con corchetes, **empezando en 0**. El resultado es una columna normal del tipo de los elementos:

```python
parts.withColumn("type_code", F.col("type_parts")[1]).select("Outlet_Type", "type_code").distinct().show()
```

```output
+-----------------+---------+
|      Outlet_Type|type_code|
+-----------------+---------+
|    Grocery Store|    Store|
|Supermarket Type1|    Type1|
|Supermarket Type2|    Type2|
|Supermarket Type3|    Type3|
+-----------------+---------+
```

`F.col("type_parts").getItem(1)` es lo mismo. También existe `F.element_at("type_parts", 2)`, que cuenta **desde 1** y acepta negativos para contar desde el final: `element_at(col, -1)` es el último elemento.

> [!WARNING]
> Un índice que se sale de la lista **no devuelve nulo**. En Spark 4, con el modo ANSI, falla al ejecutar: `[INVALID_ARRAY_INDEX] The index 5 is out of bounds. The array has 2 elements.` Si quieres `NULL` en ese caso, el mensaje lo dice: `F.get("type_parts", 5)`.

## size: cuántos elementos

`F.size(array)` devuelve el número de elementos como entero. Con `split` delante, cuenta palabras:

```python
counted = sales.withColumn("word_count", F.size(F.split("Item_Type", " ")))
counted.groupBy("word_count").count().orderBy("word_count").show()
```

```output
+----------+-----+
|word_count|count|
+----------+-----+
|         1| 3260|
|         2| 3511|
|         3| 1752|
+----------+-----+
```

Los de tres palabras son `Fruits and Vegetables` y `Health and Hygiene`. `size` de una lista vacía es 0 y de una lista nula es `NULL`.

## explode: una fila por elemento

`F.explode(array)` es la función que da nombre al módulo en muchos cursos. Convierte **una fila con una lista** en **una fila por elemento**; las demás columnas se repiten en cada fila nueva.

![Dos filas con una lista de dos palabras se convierten en cuatro filas, una por palabra, con el resto de columnas repetido](diagram:explode-rows 'explode multiplica las filas por el tamaño de la lista.')

```python
exploded = parts.withColumn("type_word", F.explode("type_parts"))
print(parts.count(), "→", exploded.count())
exploded.groupBy("type_word").count().orderBy("type_word").show()
```

```output
8523 → 17046
+-----------+-----+
|  type_word|count|
+-----------+-----+
|    Grocery| 1083|
|      Store| 1083|
|Supermarket| 7440|
|      Type1| 5577|
|      Type2|  928|
|      Type3|  935|
+-----------+-----+
```

Es el paso previo a contar o agrupar **por elemento**: etiquetas de un producto, géneros de una película, ingredientes de una receta. Después del `explode`, cada elemento es una fila normal y vale todo lo que ya sabes.

> [!WARNING]
> **`explode` descarta las filas cuya lista está vacía o es nula**: no hay elementos que desplegar, así que la fila desaparece. Si necesitas conservarlas, `F.explode_outer` las deja con un `NULL` en la columna nueva. Con tres productos, uno con dos etiquetas, uno con lista vacía y uno con lista nula, `explode` devuelve 2 filas y `explode_outer` 4.

```output
+----------+------------+-----+
|product_id|        tags|  tag|
+----------+------------+-----+
|         1|[bio, local]|  bio|
|         1|[bio, local]|local|
|         2|          []| NULL|
|         3|        NULL| NULL|
+----------+------------+-----+
```

> [!EXTRA]
> `F.posexplode` hace lo mismo y añade una columna `pos` con la posición de cada elemento dentro de su lista, empezando en 0.

## array_contains: ¿está en la lista?

`F.array_contains(array, valor)` devuelve una columna `boolean`: `true` si el valor está en la lista, `false` si no, y `NULL` si la lista es nula.

```python
flagged = parts.withColumn("type1_flag", F.array_contains("type_parts", "Type1"))
flagged.groupBy("type1_flag").count().show()
```

```output
+----------+-----+
|type1_flag|count|
+----------+-----+
|      true| 5577|
|     false| 2946|
+----------+-----+
```

Sirve directamente como condición de filtro: `parts.filter(F.array_contains("type_parts", "Type1"))`. Y, como todas las comparaciones de texto en Spark, distingue mayúsculas: con `"type1"` no encuentra nada.

## Las funciones de arrays exigen arrays

`explode` y `array_contains` solo aceptan columnas de tipo `array` (o `map`, en el caso de `explode`). Sobre una columna de texto fallan **antes de ejecutar**, al analizar la consulta:

```output
AnalysisException: [DATATYPE_MISMATCH.UNEXPECTED_INPUT_TYPE] Cannot resolve
"array_contains(Outlet_Type, Type1)" due to data type mismatch: The first parameter
requires the "ARRAY" type, however "Outlet_Type" has the type "STRING".
```

Es un error muy común: aplicar la función al DataFrame original, que todavía tiene el texto, en vez de al que ya tiene el `split`. Cuando lo veas, mira el esquema con `printSchema()` y busca dónde se perdió el array.

## Errores comunes

- **`split` con `.` o `|` sin escapar.** Son regex: trozos vacíos o un trozo por carácter. Escríbelos como `"\\."` y `"\\|"`.
- **Índices desde 1.** `[0]` es el primer elemento. `element_at` sí empieza en 1.
- **Un índice fuera de la lista.** Error, no nulo. Para nulo, `F.get`.
- **`explode` o `array_contains` sobre texto.** `DATATYPE_MISMATCH`: la columna no es un array. Haz el `split` primero.
- **Perder filas con `explode`.** Las listas vacías y nulas desaparecen. Usa `explode_outer` si tienen que quedarse.
- **Olvidar que `explode` multiplica las filas.** Un `count()` después ya no cuenta productos, sino elementos.
