## Cuando las funciones de F no alcanzan

Spark trae cientos de funciones en `F`, y con ellas se resuelve casi todo. Pero a veces la lógica que necesitas no existe como función nativa: una regla de negocio enrevesada, una librería de Python que ya hace el cálculo, un parser propio. Para eso están las **UDF** (_user defined functions_): escribes una función de Python y Spark la aplica a cada fila.

Son tres pasos: la función, el envoltorio con `F.udf` y la aplicación con `withColumn`.

```python
def price_band(mrp):
    if mrp < 100:
        return "cheap"
    if mrp < 200:
        return "mid"
    return "premium"


band_udf = F.udf(price_band, "string")
sales.withColumn("band", band_udf("Item_MRP")).select("Item_Identifier", "Item_MRP", "band").show(3)
```

```output
+---------------+--------+-------+
|Item_Identifier|Item_MRP|   band|
+---------------+--------+-------+
|          FDA15|249.8092|premium|
|          DRC01| 48.2692|  cheap|
|          FDN15| 141.618|    mid|
+---------------+--------+-------+
only showing top 3 rows
```

La función recibe **un valor** de cada fila, no una columna, y devuelve un valor. El envoltorio es lo que le enseña a Spark a llamarla fila a fila. También se puede escribir como decorador, que es lo mismo con menos nombres: `@F.udf("string")` encima de `def price_band`.

Sin el envoltorio, la función recibe una `Column` y no un número. Para una comparación como `mrp < 100`, Python intenta convertir la columna en verdadero o falso y Spark lo rechaza: `[CANNOT_CONVERT_COLUMN_INTO_BOOL] Cannot convert column into bool: please use '&' for 'and', '|' for 'or', '~' for 'not' when building DataFrame boolean expressions`. Curiosamente, una función aritmética como `x * x` sí funciona sobre una `Column`, porque `Column * Column` es una expresión de Spark: en ese caso ya no es una UDF, es la versión nativa.

## El tipo de retorno

El segundo argumento de `F.udf` es el tipo que devuelve la función, y Spark **no lo adivina**: si no lo das, asume `string` y convierte a texto lo que salga. Muchos tutoriales se saltan este argumento, y el cuadrado de un precio acaba siendo una cadena:

```python
def square(x):
    return x * x


untyped = sales.withColumn("mrp_sq", F.udf(square)("Item_MRP"))
print(untyped.select("mrp_sq").dtypes)
untyped.orderBy(F.desc("mrp_sq")).select("Item_MRP", "mrp_sq").show(3)
```

```output
[('mrp_sq', 'string')]
+--------+-------------+
|Item_MRP|       mrp_sq|
+--------+-------------+
| 99.9384|9987.68379456|
| 99.9358|9987.16412164|
| 99.9042|9980.84917764|
+--------+-------------+
only showing top 3 rows
```

El "máximo" es 9987, el texto que va último alfabéticamente, y no 71229, el cuadrado del precio más alto. Nada ha fallado: Spark ha ordenado cadenas. Con el tipo declarado, la columna es numérica y el orden es el que esperas:

```python
sales.withColumn("mrp_sq", F.udf(square, "double")("Item_MRP")).orderBy(F.desc("mrp_sq")).select("Item_MRP", "mrp_sq").show(3)
```

```output
+--------+--------------+
|Item_MRP|        mrp_sq|
+--------+--------------+
|266.8884|71229.41805456|
|266.8884|71229.41805456|
|266.6884|71122.70269456|
+--------+--------------+
only showing top 3 rows
```

El tipo se escribe como texto (`"double"`, `"int"`, `"string"`, `"boolean"`) o con las clases de `pyspark.sql.types` (`DoubleType()`, `IntegerType()`…). Tiene que ser el tipo que **de verdad** devuelve la función: si declaras `"int"` y devuelves un `float`, Spark lo trunca sin avisar; si declaras `"string"` y devuelves un número, lo convierte en texto.

> [!WARNING]
> Spark pasa los nulos a la función como `None`. Si la función no lo espera, el worker de Python revienta con un error larguísimo que termina en el `TypeError` de siempre: con `Item_Weight`, que tiene 1463 nulos, `lambda w: w * 1000` falla con `TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'`. Protege siempre la entrada: `if weight is None: return None`. Las funciones nativas no tienen este problema; un `NULL` entra y un `NULL` sale.

## Por qué una UDF es lenta

Los executors de Spark corren en la JVM, y la JVM no sabe ejecutar Python. Para aplicar una UDF, cada executor arranca un **proceso de Python aparte**, le manda los datos por lotes, espera que los devuelva y los vuelve a leer. Ese viaje de ida y vuelta, serializar, cruzar al otro proceso, deserializar, es lo que cuesta, y se paga por cada fila.

![Una función nativa se ejecuta dentro de la JVM; una UDF manda cada lote a un proceso de Python y lo recoge de vuelta](diagram:udf-roundtrip 'La función nativa no sale de la JVM. La UDF cruza dos veces entre procesos por cada lote de filas.')

Se ve en el plan de ejecución. La versión nativa es un `CASE WHEN` dentro del `Project`; la UDF aparece como un paso aparte, `ArrowEvalPython`:

```python
banded.select("band").explain()
```

```output
== Physical Plan ==
*(1) Project [pythonUDF0#605 AS band#515]
+- ArrowEvalPython [price_band(Item_MRP#22)#514], [pythonUDF0#605], 101
   +- FileScan csv [Item_MRP#22] ...
```

Y hay un segundo coste, menos visible: el optimizador de Spark **no puede mirar dentro** de una función de Python. Un `filter(F.col("Item_MRP") >= 200)` se empuja hasta la lectura del archivo (`PushedFilters: [GreaterThanOrEqual(Item_MRP,200.0)]`); un `filter(band_udf("Item_MRP") == "premium")` obliga a leer todas las filas, pasarlas por Python y filtrar después.

Medido con 2 millones de filas, elevar al cuadrado:

| Forma                     | Tiempo | Dónde corre                         |
| ------------------------- | ------ | ----------------------------------- |
| `F.col("x") * F.col("x")` | 0.15 s | JVM, código compilado               |
| `pandas_udf`              | 0.54 s | Python, por lotes (`pandas.Series`) |
| `F.udf`                   | 0.80 s | Python, una llamada por fila        |

Con una función tan simple la diferencia es de unas pocas veces; con lógica más pesada y más datos, son órdenes de magnitud. La regla práctica es: **antes de escribir una UDF, busca la función nativa**. Casi siempre existe.

## Reescribir una UDF con funciones nativas

Las bandas de precio son un `when` encadenado, y los gramos son una multiplicación con `round` y `cast`. Las dos versiones dan exactamente lo mismo, y la nativa no necesita proteger los nulos:

```python
compared = banded.withColumn(
    "band_native", F.when(F.col("Item_MRP") < 100, "cheap").when(F.col("Item_MRP") < 200, "mid").otherwise("premium")
)
compared.filter(~F.col("band").eqNullSafe(F.col("band_native"))).count()
```

```output
0
```

Para comprobar que dos columnas coinciden en todas las filas, compara con `eqNullSafe` y no con `!=`: un `NULL != NULL` no es verdadero, y el `filter` descartaría justo las filas que quieres ver.

Cosas que la gente escribe como UDF y ya existen en `F`: pasar a mayúsculas (`upper`), recortar (`trim`), sacar trozos (`substring`, `split`), fechas (`datediff`, `date_add`), condiciones (`when`), redondeos (`round`), expresiones regulares (`regexp_replace`, `regexp_extract`), listas (`array_contains`, `transform`). La chuleta de este sitio es un buen índice.

## pandas_udf: Python, pero por lotes

Cuando de verdad hace falta Python, por ejemplo para usar una librería que no tiene equivalente en Spark, `pandas_udf` es la forma rápida. En vez de llamar a la función una vez por fila, Spark le pasa **lotes enteros** como `pandas.Series`, y la función devuelve otra `Series` del mismo tamaño. El viaje entre procesos sigue existiendo, pero se hace una vez por lote y el cálculo dentro de Python es vectorizado.

```python
import pandas as pd
from pyspark.sql.functions import pandas_udf


@pandas_udf("double")
def square_pd(s: pd.Series) -> pd.Series:
    return s * s


sales.withColumn("mrp_sq", square_pd("Item_MRP"))
```

Se escribe siempre como decorador, con el tipo de retorno y las **anotaciones de tipo** en la firma: así Spark sabe que es una `pandas_udf` escalar. Los nulos llegan como `NaN` dentro de la `Series` y salen como `NULL`, sin que tengas que protegerlos.

> [!EXTRA]
> Una UDF también se puede registrar para usarla desde SQL: `spark.udf.register("price_band_sql", price_band, "string")`, y después `SELECT price_band_sql(Item_MRP) FROM sales`. Lo verás en el módulo de Spark SQL. Y en Spark 4 las UDF normales ya viajan en formato Arrow por lotes (por eso el plan dice `ArrowEvalPython` y no `BatchEvalPython`), pero la función sigue llamándose una vez por fila: la `pandas_udf` es la que vectoriza el cálculo.

## Errores comunes

- **No declarar el tipo de retorno.** La columna sale como `string`, y ordenar o sumar da resultados raros sin ningún error.
- **Declarar un tipo que no es el que devuelve la función.** `"int"` con un `float` trunca; `"string"` con un número lo convierte a texto. Sin avisar.
- **No proteger la función de los nulos.** `TypeError` dentro del worker de Python, con un error de varias pantallas.
- **Llamar a la función sin envolverla.** Recibe una `Column`: `CANNOT_CONVERT_COLUMN_INTO_BOOL` en cualquier `if`.
- **Pasar un número suelto como argumento.** `band_udf("Item_MRP", 1.0)` da `NOT_EXPECTED_TYPE`: los argumentos tienen que ser columnas o nombres de columna; para una constante, `F.lit(1.0)`.
- **Escribir una UDF para algo que ya hace `F`.** Es el error más caro. Busca primero.
- **Filtrar con una UDF.** El filtro no se puede empujar a la lectura: Spark lee y procesa todas las filas en Python antes de descartar.
