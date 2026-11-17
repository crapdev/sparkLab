## Dos cortes distintos

Casi todo lo que harás con un DataFrame empieza por quedarte con una parte de él. Hay dos formas de recortar, y conviene no confundirlas:

- **`select` recorta columnas.** Devuelve las columnas que le pides, con todas las filas.
- **`filter` recorta filas.** Devuelve las filas que cumplen una condición, con todas las columnas.

![select deja un DataFrame con menos columnas y las mismas filas; filter deja las mismas columnas y menos filas](diagram:select-vs-filter 'Los dos recortes sobre el CSV de BigMart. Los números son reales.')

Las dos son transformaciones: no leen nada hasta que una acción como `show()` o `count()` lo pide, y las dos devuelven un DataFrame nuevo. El original no cambia.

## select con nombres

La forma más corta de seleccionar es pasar los nombres de las columnas como strings:

```python
sales.select("Item_Identifier", "Item_Weight", "Item_Fat_Content").show(3)
```

```output
+---------------+-----------+----------------+
|Item_Identifier|Item_Weight|Item_Fat_Content|
+---------------+-----------+----------------+
|          FDA15|        9.3|         Low Fat|
|          DRC01|       5.92|         Regular|
|          FDN15|       17.5|         Low Fat|
+---------------+-----------+----------------+
only showing top 3 rows
```

Las columnas salen en el orden en que las pides. Si pides una que no existe, Spark lanza un `AnalysisException` y sugiere nombres parecidos:

```output
[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter with name
`Item_Price` cannot be resolved. Did you mean one of the following?
[`Item_MRP`, `Item_Type`, `Item_Weight`, `Outlet_Size`, `Item_Identifier`].
```

## F.col: la columna como objeto

Un string solo sirve para **nombrar** una columna. Para hacer algo con ella, como renombrarla, compararla o usarla en una operación, hace falta un **objeto columna**. Se obtiene con `F.col("nombre")`:

```python
from pyspark.sql import functions as F

sales.select(
    F.col("Item_Identifier").alias("Item_ID"),
    F.col("Item_MRP").alias("Price"),
).show(3)
```

```output
+-------+--------+
|Item_ID|   Price|
+-------+--------+
|  FDA15|249.8092|
|  DRC01| 48.2692|
|  FDN15| 141.618|
+-------+--------+
only showing top 3 rows
```

`alias` cambia el nombre en el DataFrame **resultado**. En `sales` la columna sigue llamándose `Item_MRP`. Y si en el resultado intentas usar el nombre antiguo, Spark no lo encuentra.

Dentro de un `select` se pueden mezclar strings y objetos columna, y también escribir expresiones. Una expresión sin alias recibe un nombre feo, que conviene arreglar:

```python
sales.select("Item_Identifier", F.col("Item_MRP") * 2).columns
```

```output
['Item_Identifier', '(Item_MRP * 2)']
```

> [!NOTE]
> Hay otras dos formas de obtener la misma columna como objeto: `sales.Item_MRP` y `sales["Item_MRP"]`. Funcionan igual, pero atan la expresión a un DataFrame concreto. `F.col("Item_MRP")` no depende de ninguno, y por eso es la que verás en la mayoría del código.

## filter y where

`filter` recibe una condición y devuelve las filas que la cumplen. La condición es una columna comparada con un valor:

```python
sales.filter(F.col("Item_Fat_Content") == "Regular").count()
```

```output
2889
```

`where` es un alias exacto de `filter`: elige el que te suene mejor. La condición también se puede escribir como un trozo de SQL dentro de un string, y a veces resulta más corto:

```python
sales.where("Item_Fat_Content = 'Regular'").count()  # 2889
```

Los operadores de comparación son los de Python: `==`, `!=`, `<`, `<=`, `>`, `>=`.

> [!WARNING]
> **Comparar con un valor mal escrito no da error: da cero filas.** `F.col("Item_Fat_Content") == "regular"` devuelve 0, porque los datos dicen `Regular`. Antes de filtrar por texto, mira los valores que hay: `sales.select("Item_Fat_Content").distinct().show()`. En BigMart aparecen cinco variantes: `Low Fat`, `Regular`, `LF`, `reg` y `low fat`.

## Combinar condiciones: &, | y ~

Aquí está el tropiezo más habitual de PySpark. Los `and`, `or` y `not` de Python **no sirven** con columnas. Se usan tres operadores:

| Quieres decir | En Python normal | Con columnas de Spark |
| ------------- | ---------------- | --------------------- |
| y             | `and`            | `&`                   |
| o             | `or`             | `\|`                  |
| no            | `not`            | `~`                   |

Y una regla sin excepciones: **cada condición va entre paréntesis**.

```python
light_drinks = sales.filter((F.col("Item_Type") == "Soft Drinks") & (F.col("Item_Weight") < 10))
light_drinks.count()
```

```output
166
```

### Por qué hacen falta los paréntesis

En Python, `&` se evalúa **antes** que `==` y `<`. Si escribes la condición sin paréntesis, Python la agrupa así:

```python
F.col("Item_Type") == ("Soft Drinks" & F.col("Item_Weight")) < 10
```

Eso no tiene sentido, y además la comparación encadenada `a == b < c` lleva un `and` escondido. El resultado es el mismo error que si hubieras escrito `and` tú:

```output
PySparkValueError: [CANNOT_CONVERT_COLUMN_INTO_BOOL] Cannot convert column into bool:
please use '&' for 'and', '|' for 'or', '~' for 'not' when building DataFrame boolean
expressions.
```

Ese mensaje aparece siempre que Python intenta convertir una columna en `True` o `False`. Una columna no es ni lo uno ni lo otro: es una expresión que Spark evaluará más tarde, fila a fila. Cuando lo veas, busca un `and`, un `or`, un `not` o unos paréntesis que faltan.

### Negar con ~

`~` niega una condición completa, así que también va con paréntesis:

```python
fresh = sales.filter(
    ((F.col("Item_Type") == "Dairy") | (F.col("Item_Type") == "Meat"))
    & ~(F.col("Outlet_Location_Type") == "Tier 3")
)
fresh.count()
```

```output
667
```

Si olvidas los paréntesis de la negación, `~F.col("Outlet_Location_Type") == "Tier 3"` intenta negar la columna de texto antes de compararla, y Spark falla al ejecutar con un error de conversión a `BOOLEAN`.

## isNull e isin

Dos condiciones que no se escriben con operadores sino como métodos de la columna:

```python
sales.filter(F.col("Outlet_Size").isNull()).count()                             # 2410
sales.filter(F.col("Outlet_Location_Type").isin("Tier 1", "Tier 2")).count()   # 5173
```

- `isNull()` es verdadera cuando el valor falta. Su contrario es `isNotNull()`.
- `isin(a, b, c)` es verdadera cuando el valor es uno de la lista. Equivale a encadenar varios `==` con `|`, pero es mucho más corto. También acepta una lista de Python: `isin(["Tier 1", "Tier 2"])`.

Se combinan con los demás como cualquier condición:

```python
sales.filter(F.col("Outlet_Size").isNull() & F.col("Outlet_Location_Type").isin("Tier 1", "Tier 2")).count()
```

```output
1855
```

> [!WARNING]
> **`== None` no detecta nulos.** `sales.filter(F.col("Outlet_Size") == None).count()` devuelve `0`, aunque hay 2410 filas sin tamaño. En SQL, y por tanto en Spark, nada es igual a nulo, ni siquiera otro nulo. Para nulos, siempre `isNull()`.

## Los nulos no se dejan comparar

Esa misma regla tiene una consecuencia que sorprende. `Item_Weight` tiene 1463 valores nulos. Si separas las filas en "pesan menos de 10" y "no pesan menos de 10", las dos partes deberían sumar 8523:

```python
sales.filter(F.col("Item_Weight") < 10).count()      # 2377
sales.filter(~(F.col("Item_Weight") < 10)).count()   # 4683
```

Suman 7060. Faltan exactamente las 1463 filas con el peso nulo. Una comparación con un nulo no es verdadera ni falsa, es **desconocida**, y `filter` solo se queda con lo que es verdadero. Ni `x < 10` ni su negación la rescatan.

Si quieres conservar los nulos en un filtro, tienes que pedirlo:

```python
sales.filter((F.col("Item_Weight") < 10) | F.col("Item_Weight").isNull()).count()  # 3840
```

## Para profundizar

> [!EXTRA]
> **Más condiciones sobre texto y rangos.** Son métodos de la columna, como `isin`:
>
> | Método                | Verdadero cuando…                              | En BigMart |
> | --------------------- | ---------------------------------------------- | ---------- |
> | `.between(10, 20)`    | el valor está entre los dos, ambos incluidos   | 4224 filas |
> | `.like("FD%")`        | el texto encaja con el patrón SQL (`%` = algo) | 6125 filas |
> | `.startswith("FD")`   | el texto empieza así                           | 6125 filas |
> | `.endswith("Foods")`  | el texto termina así                           | 2204 filas |
> | `.contains("Drinks")` | el texto contiene eso                          | 659 filas  |
>
> Todas distinguen mayúsculas de minúsculas: `.like("low%")` encuentra 112 filas, las de `low fat`; `.like("Low%")` encuentra las 5089 de `Low Fat`.

> [!EXTRA]
> **`selectExpr`** es un `select` que acepta trozos de SQL. Sirve para renombrar y calcular sin `F.col`:
>
> ```python
> sales.selectExpr("Item_Identifier AS Item_ID", "Item_MRP > 200 AS expensive").show(3)
> ```
>
> ```output
> +-------+---------+
> |Item_ID|expensive|
> +-------+---------+
> |  FDA15|     true|
> |  DRC01|    false|
> |  FDN15|    false|
> +-------+---------+
> only showing top 3 rows
> ```

## Errores comunes

- **Usar `and`, `or` o `not`.** El error `CANNOT_CONVERT_COLUMN_INTO_BOOL` lo dice claro: cámbialos por `&`, `|` y `~`.
- **Olvidar los paréntesis.** Mismo error que el anterior. Cada condición, entre paréntesis.
- **Escribir `&&` o `||`.** No existen en Python: `SyntaxError`.
- **Un valor mal escrito.** Cero filas sin ningún aviso. Mira primero los valores con `distinct()`.
- **`== None` para buscar nulos.** Siempre cero filas. Usa `isNull()`.
- **Llamar `.alias()` a un string.** `"Item_MRP".alias("Price")` da `AttributeError`. El alias es de `F.col("Item_MRP")`.
- **Usar el nombre antiguo después de un alias.** Tras `select(F.col("Item_MRP").alias("Price"))`, la columna se llama `Price` y solo `Price`.
