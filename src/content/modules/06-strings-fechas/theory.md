## Texto: mayúsculas y minúsculas

Las funciones de texto viven en `F`, reciben una columna y devuelven otra. Las tres más usadas cambian las mayúsculas:

| Función          | `"soft drinks"` pasa a | Para qué                                                |
| ---------------- | ---------------------- | ------------------------------------------------------- |
| `F.upper(col)`   | `SOFT DRINKS`          | Comparar o cruzar texto sin que importen las mayúsculas |
| `F.lower(col)`   | `soft drinks`          | Lo mismo, en minúsculas; es la convención más habitual  |
| `F.initcap(col)` | `Soft Drinks`          | Presentar: primera letra de cada palabra en mayúscula   |

```python
sales.select(F.initcap("Item_Type").alias("initcap"), F.lower("Item_Type").alias("lower"), F.upper("Item_Type").alias("upper")).distinct().show(3)
```

```output
+------------+------------+------------+
|     initcap|       lower|       upper|
+------------+------------+------------+
|Baking Goods|baking goods|BAKING GOODS|
|      Breads|      breads|      BREADS|
|   Breakfast|   breakfast|   BREAKFAST|
+------------+------------+------------+
only showing top 3 rows
```

Antes de comparar textos que vienen de fuentes distintas, o de hacer un join por una columna de texto, pásalos por `lower` o `upper`: `"British"` y `"british"` son valores distintos para Spark.

> [!WARNING]
> `initcap` **no** unifica variantes. Sobre `Item_Fat_Content` convierte `LF` en `Lf` y `reg` en `Reg`, que siguen siendo valores distintos de `Low Fat` y `Regular`. Para unificar, `lower` primero y un `when` después, como en el módulo anterior. Y en nombres de persona también sorprende: `initcap("alain de changy")` devuelve `Alain De Changy`.

## Texto: trozos y uniones

| Función                            | Qué hace                                                        | Ejemplo                                        |
| ---------------------------------- | --------------------------------------------------------------- | ---------------------------------------------- |
| `F.substring(col, inicio, largo)`  | Corta un trozo. El inicio cuenta **desde 1**                    | `substring("Item_Identifier", 1, 2)` → `FD`    |
| `F.length(col)`                    | Número de caracteres                                            | `length("Item_Identifier")` → `5`              |
| `F.trim(col)`                      | Quita espacios por los dos lados                                | `"  Low Fat "` → `Low Fat`                     |
| `F.concat_ws(sep, col1, col2, …)`  | Une columnas con un separador; **salta** las nulas              | `concat_ws(" ", forename, surname)`            |
| `F.concat(col1, col2, …)`          | Une columnas sin separador; si **alguna es nula, todo es nulo** | `concat(driverRef, lit("-"), code)`            |
| `F.regexp_extract(col, patrón, g)` | Saca el trozo que encaja con una expresión regular              | `regexp_extract("Item_Identifier", r"\d+", 0)` |

Los identificadores de BigMart codifican la familia del producto en sus dos primeras letras. Con `substring` se saca y se cuenta:

```python
sales.withColumn("prefix", F.substring("Item_Identifier", 1, 2)).groupBy("prefix").count().orderBy("prefix").show()
```

```output
+------+-----+
|prefix|count|
+------+-----+
|    DR|  799|
|    FD| 6125|
|    NC| 1599|
+------+-----+
```

> [!NOTE]
> La diferencia entre `concat` y `concat_ws` con los nulos importa. En los pilotos, 765 de 885 no tienen `code`. `concat("driverRef", F.lit("-"), "code")` devuelve 765 nulos; `concat_ws("-", "driverRef", "code")` no devuelve ninguno: para esos pilotos deja solo `driverRef`.

## Fechas: primero conviértelas

Una fecha que llega de un CSV o de un JSON es **texto**. Lo parece todo menos una fecha: `"1985-01-07"` es un `string`, y mientras lo sea no puedes sumarle días ni restarle otra fecha de forma fiable. El primer paso es siempre `F.to_date`:

```python
dated = drivers.withColumn("dob", F.to_date("dob"))
dated.select("driverRef", "dob").printSchema()
```

```output
root
 |-- driverRef: string (nullable = true)
 |-- dob: date (nullable = true)
```

Sin segundo argumento, `to_date` espera el formato `yyyy-MM-dd`. Si el texto viene de otra forma, hay que dar el patrón:

```python
F.to_date(F.lit("07/01/1985"), "dd/MM/yyyy")   # 1985-01-07
```

> [!WARNING]
> Un texto que no encaja con el patrón **no devuelve nulo**: en Spark 4 falla al ejecutar, igual que `cast`. `to_date(F.lit("1985-01-07"), "dd/MM/yyyy")` lanza `CANNOT_PARSE_TIMESTAMP`, y sin patrón un `07/01/1985` lanza `CAST_INVALID_INPUT`. Para obtener `NULL` en vez de error existe `F.try_to_date`.

Como `dob` ya venía en `yyyy-MM-dd`, algunas funciones funcionan incluso sobre el texto: `F.year("dob")` devuelve 1933 sin convertir nada, porque Spark convierte por debajo. Eso engaña: en cuanto la fecha llegue como `07/01/1985`, la conversión implícita falla. Convierte al leer y trabaja con fechas de verdad.

## Fechas: partes, sumas y restas

Con una columna `date`:

| Función                             | Devuelve                    | Ejemplo con `1985-01-07`              |
| ----------------------------------- | --------------------------- | ------------------------------------- |
| `F.year`, `F.month`, `F.dayofmonth` | Un entero                   | `1985`, `1`, `7`                      |
| `F.date_add(fecha, n)`              | Una fecha `n` días después  | `date_add("dob", 7)` → `1985-01-14`   |
| `F.date_sub(fecha, n)`              | Una fecha `n` días antes    | `date_sub("dob", 7)` → `1984-12-31`   |
| `F.add_months(fecha, n)`            | Una fecha `n` meses después | `add_months("dob", 1)` → `1985-02-07` |
| `F.current_date()`                  | La fecha de hoy             |                                       |

`date_add` con un número negativo también resta: `date_add("dob", -7)` es lo mismo que `date_sub("dob", 7)`.

### Distancia entre dos fechas

- `F.datediff(fin, inicio)` devuelve **días**, como entero.
- `F.months_between(fin, inicio)` devuelve **meses**, con decimales.

En las dos, el primer argumento es la fecha **más reciente**. Si las cambias de orden, el resultado sale negativo:

![Línea de tiempo con dob y una fecha de referencia: datediff(referencia, dob) es positivo y datediff(dob, referencia) negativo](diagram:datediff-order 'Hamilton nació el 7 de enero de 1985; a 1 de enero de 2025 había vivido 14 604 días.')

Para una **edad en años cumplidos**, lo cómodo es `months_between` dividido entre 12 y redondeado hacia abajo con `F.floor`:

```python
REFERENCE = F.to_date(F.lit("2025-01-01"))
aged = dated.withColumn("age", F.floor(F.months_between(REFERENCE, F.col("dob")) / 12).cast("int"))
aged.filter(F.col("driverRef") == "hamilton").select("dob", "age").show()
```

```output
+----------+---+
|       dob|age|
+----------+---+
|1985-01-07| 39|
+----------+---+
```

`floor` devuelve `bigint`; el `cast("int")` es solo para que el tipo quede limpio. Dividir `datediff` entre 365.25 da lo mismo casi siempre, pero `months_between` respeta los años bisiestos sin trucos.

> [!NOTE]
> En un proceso real la referencia sería `F.current_date()`. En el laboratorio se usa una fecha fija para que los tests den siempre lo mismo. Es una buena costumbre también fuera del laboratorio: un cálculo que depende del día en que se ejecuta es difícil de probar.

## Fechas: de fecha a texto con date_format

`F.date_format(fecha, patrón)` hace el camino contrario a `to_date`: convierte una fecha en **texto** con el formato que pidas.

```python
hamilton.select(
    F.date_format("dob", "dd/MM/yyyy").alias("europeo"),
    F.date_format("dob", "MMMM yyyy").alias("mes_largo"),
    F.date_format("dob", "EEEE").alias("dia_semana"),
).show()
```

```output
+----------+------------+----------+
|   europeo|   mes_largo|dia_semana|
+----------+------------+----------+
|07/01/1985|January 1985|    Monday|
+----------+------------+----------+
```

Las letras del patrón distinguen mayúsculas y minúsculas:

| Letra  | Significa        | Ejemplo   |
| ------ | ---------------- | --------- |
| `yyyy` | Año              | `1985`    |
| `MM`   | Mes, con cero    | `01`      |
| `MMMM` | Mes, con nombre  | `January` |
| `dd`   | Día del mes      | `07`      |
| `EEEE` | Día de la semana | `Monday`  |
| `HH`   | Hora (0 a 23)    | `00`      |
| `mm`   | **Minutos**      | `00`      |

> [!WARNING]
> Dos trampas del patrón. **`mm` son minutos**, no meses: `"dd-mm-yyyy"` devuelve `07-00-1985` sin ningún error. Y **`YYYY` no se acepta**: es el "año por semanas" y Spark 3 y posteriores lo rechazan con `INCONSISTENT_BEHAVIOR_CROSS_VERSION.DATETIME_PATTERN_RECOGNITION`. Año siempre en minúsculas, mes siempre en mayúsculas. Los nombres de mes y de día salen en inglés.

El resultado de `date_format` es un `string`. Si lo guardas sobre la misma columna, pierdes la fecha: ponlo en una columna nueva y deja la fecha de verdad para calcular.

## Errores comunes

- **Tratar una fecha como texto.** Funciona por casualidad mientras el formato sea `yyyy-MM-dd`, y se rompe con cualquier otro. Convierte con `to_date` al leer.
- **Esperar `NULL` de un `to_date` que no puede convertir.** En Spark 4 es un error. Para nulos, `try_to_date`.
- **`datediff` o `months_between` al revés.** Sale negativo. El primer argumento es la fecha más reciente.
- **`YYYY` en el patrón.** Error. Es `yyyy`.
- **`mm` para el mes.** Son minutos y salen `00`, sin error. El mes es `MM`.
- **Sobrescribir la fecha con `date_format`.** Te quedas con texto. Usa otra columna.
- **`substring` empezando en 0.** El primer carácter es el 1.
- **`concat` con una columna que puede ser nula.** El resultado entero es nulo. Usa `concat_ws`.
- **`initcap` para limpiar variantes.** Solo cambia mayúsculas: `LF` sigue sin ser `Low Fat`.
