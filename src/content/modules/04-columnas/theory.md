## withColumn: la herramienta para casi todo

`withColumn(nombre, expresión)` devuelve un DataFrame nuevo con una columna más. Si el nombre ya existe, **la sustituye** en su misma posición. Con esa única función se crea, se calcula, se limpia y se convierte.

La expresión tiene que ser una columna de Spark. Hay tres formas habituales de conseguir una:

| Quieres…              | Expresión                                  |
| --------------------- | ------------------------------------------ |
| Un valor constante    | `F.lit("new")`                             |
| Un cálculo            | `F.col("Item_Weight") * F.col("Item_MRP")` |
| Una columna existente | `F.col("Item_MRP")`                        |

```python
sales.withColumn("flag", F.lit("new")).select("Item_Identifier", "flag").show(3)
```

```output
+---------------+----+
|Item_Identifier|flag|
+---------------+----+
|          FDA15| new|
|          DRC01| new|
|          FDN15| new|
+---------------+----+
only showing top 3 rows
```

> [!WARNING]
> **Un valor suelto de Python no es una columna.** `withColumn("flag", "new")` falla con `PySparkTypeError: [NOT_EXPECTED_TYPE] Argument 'col' should be Column, got str.` Para una constante hace falta `F.lit()`. Dentro de una operación con una columna, en cambio, un número suelto sí vale: `F.col("Item_MRP") * 2`.

## Columnas calculadas

Los operadores aritméticos funcionan entre columnas y con números:

```python
priced = sales.withColumn("weight_price", F.col("Item_Weight") * F.col("Item_MRP"))
priced.select("Item_Weight", "Item_MRP", "weight_price").show(3)
```

```output
+-----------+--------+------------------+
|Item_Weight|Item_MRP|      weight_price|
+-----------+--------+------------------+
|        9.3|249.8092|2323.2255600000003|
|       5.92| 48.2692|285.75366399999996|
|       17.5| 141.618|          2478.315|
+-----------+--------+------------------+
only showing top 3 rows
```

Dos cosas que conviene saber de las columnas calculadas:

- **Los nulos se propagan.** `Item_Weight` tiene 1463 nulos; `weight_price` también. Cualquier operación con un nulo da nulo.
- **Las comparaciones también son columnas.** `F.col("Item_MRP") > 200` crea una columna de tipo `boolean`, con `true` y `false`. Es útil como bandera y como paso previo a un `when`.

Para redondear, `F.round(F.col("Item_MRP"), 1)`. Y para varias columnas de golpe existe `withColumns`, que recibe un diccionario: `sales.withColumns({"flag": F.lit("new"), "double_mrp": F.col("Item_MRP") * 2})`.

## Renombrar: withColumnRenamed frente a alias

En el módulo anterior viste `alias`, que renombra dentro de un `select`. Eso obliga a enumerar todas las columnas que quieres conservar. Cuando solo quieres cambiar un nombre y dejar el resto igual, usa `withColumnRenamed`:

```python
sales.withColumnRenamed("Item_Weight", "Item_WT").columns[:3]
```

```output
['Item_Identifier', 'Item_WT', 'Item_Fat_Content']
```

> [!NOTE]
> Si el nombre que quieres cambiar no existe, por ejemplo por una errata, `withColumnRenamed` **no da error**: devuelve el DataFrame sin cambios. Después de renombrar, comprueba `df.columns`.

## Limpiar texto: regexp_replace

`F.regexp_replace(columna, patrón, reemplazo)` sustituye lo que encaja con una **expresión regular**. Se usa junto con `withColumn` sobre el mismo nombre para limpiar una columna en su sitio.

`Item_Fat_Content` trae cinco variantes para dos valores. Así se unifican:

```python
clean = (
    sales.withColumn("Item_Fat_Content", F.regexp_replace(F.col("Item_Fat_Content"), "^(LF|low fat)$", "Low Fat"))
    .withColumn("Item_Fat_Content", F.regexp_replace(F.col("Item_Fat_Content"), "^reg$", "Regular"))
)
clean.groupBy("Item_Fat_Content").count().show()
```

```output
+----------------+-----+
|Item_Fat_Content|count|
+----------------+-----+
|         Low Fat| 5517|
|         Regular| 3006|
+----------------+-----+
```

Los anclajes `^` y `$` obligan a que el patrón sea el valor **completo**. Sin ellos, el patrón encaja en cualquier trozo del texto, y a veces eso es lo que quieres y a veces no.

> [!WARNING]
> El patrón es una expresión regular, no un texto literal. Algunos caracteres tienen significado especial: `.` encaja con **cualquier** carácter, así que `regexp_replace(col, ".", ",")` convierte `1.5` en `,,,`. Para un punto literal hay que escaparlo: `"\\."`.

## Convertir tipos: cast

`F.col("x").cast("tipo")` cambia el tipo de una columna. El tipo se puede escribir como texto o como objeto de `pyspark.sql.types`:

```python
typed = sales.withColumn("Outlet_Establishment_Year", F.col("Outlet_Establishment_Year").cast("string"))
typed = typed.withColumn("mrp_int", F.col("Item_MRP").cast("int"))
typed.select("Outlet_Establishment_Year", "Item_MRP", "mrp_int").printSchema()
```

```output
root
 |-- Outlet_Establishment_Year: string (nullable = true)
 |-- Item_MRP: double (nullable = true)
 |-- mrp_int: integer (nullable = true)
```

De `double` a `int`, `cast` **trunca**: `249.8092` pasa a `249`, no a `250`. Para redondear antes, `F.round`.

### Cuando el valor no se puede convertir

Spark 4 trae activado el **modo ANSI**, y eso cambia una costumbre antigua. Un `cast` que no puede convertir un valor ya no devuelve `NULL` en silencio: **falla cuando se ejecuta**, es decir, en la acción, no en la línea del `withColumn`.

```python
sales.withColumn("id_num", F.col("Item_Identifier").cast("int")).show(3)
```

```output
NumberFormatException: [CAST_INVALID_INPUT] The value 'FDA15' of the type "STRING" cannot be
cast to "INT" because it is malformed. Correct the value as per the syntax, or change its
target type. Use `try_cast` to tolerate malformed input and return NULL instead.
```

El mensaje dice la alternativa: `try_cast` convierte lo que puede y deja `NULL` en lo demás.

```python
sales.withColumn("id_num", F.col("Item_Identifier").try_cast("int")).select("Item_Identifier", "id_num").show(3)
```

```output
+---------------+------+
|Item_Identifier|id_num|
+---------------+------+
|          FDA15|  NULL|
|          DRC01|  NULL|
|          FDN15|  NULL|
+---------------+------+
only showing top 3 rows
```

La misma regla alcanza a las operaciones. Si conviertes `Item_Weight` a `string` y luego lo multiplicas por `2`, Spark intenta volver a convertirlo a entero y falla con `9.3`. Mantén los números como números hasta el final.

> [!EXTRA]
> Con `spark.conf.set("spark.sql.ansi.enabled", "false")` se recupera el comportamiento antiguo: el `cast` imposible devuelve `NULL`. Muchos tutoriales y respuestas en foros dan por hecho ese comportamiento, porque hasta Spark 3 era el de por defecto. Si un código que copias devuelve nulos donde el tuyo lanza un error, esta es la causa.

## Columnas condicionales: when y otherwise

`F.when(condición, valor)` es el `CASE WHEN` de SQL. Se encadenan varios `when` y se cierra con `otherwise`, que recoge lo que no cumplió ninguna condición:

```python
banded = sales.withColumn(
    "price_band",
    F.when(F.col("Item_MRP") < 100, "cheap").when(F.col("Item_MRP") < 200, "mid").otherwise("expensive"),
)
banded.groupBy("price_band").count().show()
```

```output
+----------+-----+
|price_band|count|
+----------+-----+
|     cheap| 2439|
| expensive| 1440|
|       mid| 4644|
+----------+-----+
```

![Flujo de decisión de un when encadenado: una fila prueba las condiciones en orden y la primera que se cumple decide el valor](diagram:when-chain 'Una fila con Item_MRP = 141.618 recorre el when encadenado.')

Las condiciones se evalúan **en orden** y gana la primera que se cumple. Por eso la segunda rama no necesita decir "mayor o igual que 100": las filas menores de 100 ya salieron por la primera. Y por eso el orden importa: si pones `< 200` antes que `< 100`, la rama `cheap` no recibe ninguna fila.

Los valores de las ramas pueden ser constantes, como aquí, o columnas. Un uso muy habitual es limpiar una columna dejando lo demás como está:

```python
clean = sales.withColumn(
    "Item_Fat_Content",
    F.when(F.col("Item_Fat_Content").isin("LF", "low fat"), "Low Fat")
    .when(F.col("Item_Fat_Content") == "reg", "Regular")
    .otherwise(F.col("Item_Fat_Content")),
)
```

### Los huecos

> [!WARNING]
> **Sin `otherwise`, lo que no cumple ninguna condición queda en `NULL`.** Y dos condiciones que parecen cubrirlo todo pueden dejar huecos. `Item_Weight` tiene 43 filas que pesan exactamente 10 y 1463 nulos. Con `< 10` y `> 10`, esas 1506 filas no entran en ninguna rama.

```python
gaps = sales.withColumn("size", F.when(F.col("Item_Weight") < 10, "light").when(F.col("Item_Weight") > 10, "heavy"))
gaps.groupBy("size").count().show()
```

```output
+-----+-----+
| size|count|
+-----+-----+
| NULL| 1506|
|light| 2377|
|heavy| 4640|
+-----+-----+
```

Dos costumbres lo evitan: que los límites caigan siempre en una rama (`<` con `>=`, o `<=` con `>`) y terminar con un `otherwise`, aunque sea con una etiqueta como `"unknown"` que luego puedas buscar.

Los valores de todas las ramas deben ser del mismo tipo. Mezclar `"cheap"` con un `0` en el `otherwise` obliga a Spark a convertir y, en modo ANSI, falla.

## Errores comunes

- **Un string donde hace falta una columna.** `withColumn("flag", "new")` da `NOT_EXPECTED_TYPE`. Envuélvelo en `F.lit()`.
- **Olvidar el `otherwise`.** Las filas sin rama quedan en `NULL` sin aviso.
- **Condiciones con hueco.** `< 10` y `> 10` dejan fuera el 10 exacto y los nulos.
- **El orden de los `when`.** Una condición amplia antes de una estrecha se lleva todas las filas.
- **Esperar `NULL` de un `cast` imposible.** En Spark 4 es un error al ejecutar. Para nulos, `try_cast`.
- **Operar con números guardados como texto.** `F.col("texto") * 2` falla si el texto tiene decimales. Convierte antes con `cast("double")`.
- **Un `.` sin escapar en `regexp_replace`.** Encaja con cualquier carácter.
- **Confiar en `withColumnRenamed` con una errata.** No da error: comprueba `df.columns`.
