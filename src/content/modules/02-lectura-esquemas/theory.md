## Leer es describir el archivo

Todo empieza en `spark.read`. Le dices a Spark tres cosas: en qué **formato** está el archivo, qué **opciones** aplican y **dónde** está.

```python
sales = (
    spark.read.format("csv")
    .option("header", True)
    .option("inferSchema", True)
    .load("data/bigmart_sales.csv")
)
```

Los paréntesis de fuera solo sirven para partir la cadena en varias líneas. Existe también una forma abreviada que hace lo mismo:

```python
sales = spark.read.csv("data/bigmart_sales.csv", header=True, inferSchema=True)
```

El resultado es un DataFrame, y todo DataFrame tiene un **esquema**: la lista de sus columnas con el tipo de cada una. Este módulo trata de quién decide ese esquema: Spark o tú.

## Las dos opciones de siempre en CSV

Un CSV es texto plano. No dice cómo se llaman sus columnas ni de qué tipo son, así que Spark no lo sabe si no se lo indicas. Con el CSV de BigMart:

| Opciones                 | Filas | Nombres de columna     | Tipos               |
| ------------------------ | ----- | ---------------------- | ------------------- |
| Ninguna                  | 8524  | `_c0`, `_c1`, `_c2`…   | Todo `string`       |
| `header`                 | 8523  | Los de la primera fila | Todo `string`       |
| `header` + `inferSchema` | 8523  | Los de la primera fila | Deducidos por Spark |

Sin `header`, la cabecera se cuenta como una fila de datos: por eso sale una fila de más. Para ver el esquema que ha quedado se usa `printSchema()`:

```python
sales.printSchema()
```

```output
root
 |-- Item_Identifier: string (nullable = true)
 |-- Item_Weight: double (nullable = true)
 |-- Item_Fat_Content: string (nullable = true)
 |-- Item_Visibility: double (nullable = true)
 |-- Item_Type: string (nullable = true)
 |-- Item_MRP: double (nullable = true)
 |-- Outlet_Identifier: string (nullable = true)
 |-- Outlet_Establishment_Year: integer (nullable = true)
 |-- Outlet_Size: string (nullable = true)
 |-- Outlet_Location_Type: string (nullable = true)
 |-- Outlet_Type: string (nullable = true)
 |-- Item_Outlet_Sales: double (nullable = true)
```

## Lo que cuesta inferSchema

Para deducir los tipos, Spark tiene que leer el archivo entero antes de que tú le pidas nada. Con un archivo pequeño no se nota; con uno de cientos de gigas, esa pasada extra es tiempo y dinero.

![Con inferSchema Spark abre el archivo dos veces antes de cualquier acción; con un esquema dado no lo abre hasta que hay una acción](diagram:infer-vs-schema 'Dar el esquema ahorra una pasada completa por el archivo.')

Hay un segundo motivo para no depender de la inferencia: **Spark adivina, y a veces adivina distinto de lo que necesitas**. Un código postal como `01234` se convierte en el número `1234`. Y si un día llega un archivo con un valor raro en una columna numérica, la columna entera pasa a ser texto y lo que venga después falla.

En exploración, `inferSchema` es perfecto. En un proceso que se ejecuta todos los días, el esquema se escribe.

## El esquema como texto: DDL

La forma más corta de dar un esquema es un string con pares `nombre TIPO` separados por comas, igual que en un `CREATE TABLE` de SQL. Se llama **DDL**.

```python
SALES_DDL = """
    Item_Identifier STRING,
    Item_Weight DOUBLE,
    Item_Fat_Content STRING,
    Item_Visibility DOUBLE,
    Item_Type STRING,
    Item_MRP DOUBLE,
    Outlet_Identifier STRING,
    Outlet_Establishment_Year INT,
    Outlet_Size STRING,
    Outlet_Location_Type STRING,
    Outlet_Type STRING,
    Item_Outlet_Sales DOUBLE
"""

sales = spark.read.format("csv").option("header", True).schema(SALES_DDL).load("data/bigmart_sales.csv")
```

`header` sigue haciendo falta: sin ella, Spark leería la cabecera como una fila de datos.

Los tipos más habituales:

| En DDL      | Con objetos       | En `printSchema()` | Para qué            |
| ----------- | ----------------- | ------------------ | ------------------- |
| `STRING`    | `StringType()`    | `string`           | Texto               |
| `INT`       | `IntegerType()`   | `integer`          | Enteros             |
| `BIGINT`    | `LongType()`      | `long`             | Enteros muy grandes |
| `DOUBLE`    | `DoubleType()`    | `double`           | Decimales           |
| `BOOLEAN`   | `BooleanType()`   | `boolean`          | Verdadero o falso   |
| `DATE`      | `DateType()`      | `date`             | Fechas sin hora     |
| `TIMESTAMP` | `TimestampType()` | `timestamp`        | Fecha y hora        |

## El esquema como objetos: StructType

El mismo esquema se puede construir con objetos de Python. `StructType` representa la tabla y cada `StructField` una columna.

![Anatomía de un StructField: nombre de la columna, tipo de dato y si admite nulos, junto a su equivalente en DDL](diagram:struct-field 'Un StructField y su equivalente en DDL.')

```python
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

schema = StructType(
    [
        StructField("Item_Identifier", StringType()),
        StructField("Item_Weight", DoubleType()),
    ]
)
```

¿Cuál usar? El DDL es más corto y se lee mejor. `StructType` compensa cuando el esquema se construye o se modifica con código, o cuando quieres reutilizar el de otro DataFrame, que está en `df.schema`.

> [!NOTE]
> Al leer archivos, Spark ignora el tercer argumento de `StructField`: aunque escribas `False`, la columna queda como `nullable = true`. Tiene sentido: Spark no puede garantizar que un archivo que no controla no traiga huecos.

## Dos trampas de los esquemas en CSV

> [!WARNING]
> **El esquema se aplica por posición, no por nombre.** Spark no comprueba que tus nombres coincidan con la cabecera del archivo. Si cambias el orden, los datos acaban bajo el nombre equivocado y no hay ningún aviso.

```python
swapped = (
    spark.read.format("csv")
    .option("header", True)
    .schema("Item_Weight STRING, Item_Identifier STRING")
    .load("data/bigmart_sales.csv")
)
swapped.show(2)
```

```output
+-----------+---------------+
|Item_Weight|Item_Identifier|
+-----------+---------------+
|      FDA15|            9.3|
|      DRC01|           5.92|
+-----------+---------------+
only showing top 2 rows
```

> [!WARNING]
> **Un valor que no encaja en el tipo se convierte en `NULL`.** Por defecto Spark no falla: deja vacío lo que no puede convertir. Si declaras `Item_Identifier INT`, los 8523 identificadores salen nulos, porque `FDA15` no es un número.

```output
+---------------+-----------+
|Item_Identifier|Item_Weight|
+---------------+-----------+
|           NULL|        9.3|
|           NULL|       5.92|
+---------------+-----------+
only showing top 2 rows
```

Las dos trampas tienen el mismo antídoto: después de leer con un esquema nuevo, mira unas filas con `show()` y cuenta los nulos de las columnas importantes.

> [!EXTRA]
> Ese comportamiento se llama modo `PERMISSIVE` y es el que viene por defecto. Con `.option("mode", "FAILFAST")`, Spark lanza un error en cuanto encuentra un valor que no encaja. Ojo: el error salta cuando una acción necesita convertir esa columna, así que un simple `count()` puede no detectarlo.

## Leer JSON

En JSON cada registro lleva los nombres de sus campos, así que `header` no existe, y Spark deduce los tipos siempre: `inferSchema` tampoco. Basta con el formato y la ruta.

```python
drivers = spark.read.format("json").load("data/drivers.json")
drivers.printSchema()
```

```output
root
 |-- code: string (nullable = true)
 |-- dob: string (nullable = true)
 |-- driverId: long (nullable = true)
 |-- driverRef: string (nullable = true)
 |-- name: struct (nullable = true)
 |    |-- forename: string (nullable = true)
 |    |-- surname: string (nullable = true)
 |-- nationality: string (nullable = true)
 |-- number: long (nullable = true)
 |-- url: string (nullable = true)
```

Tres detalles de ese esquema:

- Las columnas salen en **orden alfabético**, no en el orden del archivo.
- `dob`, la fecha de nacimiento, queda como `string`. Spark no deduce fechas en JSON.
- `name` es un **struct**: una columna que contiene otras columnas.

Deducir el esquema de un JSON también cuesta: Spark recorre el archivo entero, y eso es 1 job al leer. Con un esquema escrito por ti son 0, y además eliges el orden de las columnas y puedes pedir `dob DATE`.

En JSON el esquema se empareja **por nombre**, al revés que en CSV. Si pides un campo que no existe en el archivo, la columna sale entera en `NULL`, también sin aviso.

### Una línea o varias

Spark espera el formato **JSON Lines**: un registro completo en cada línea. Muchos archivos JSON no son así, sino un único array con sangría.

![Comparación entre JSON Lines, con un registro por línea, y un JSON multilínea formado por un array con sangría](diagram:json-lines-vs-multiline 'El mismo contenido en los dos formatos.')

Si lees un archivo multilínea sin avisar, Spark intenta interpretar cada línea como un registro, no entiende ninguna y devuelve una sola columna:

```python
broken = spark.read.format("json").load("data/drivers_multiline.json")
print(broken.columns)
```

```output
['_corrupt_record']
```

`_corrupt_record` es la señal de que Spark no pudo interpretar el archivo. Se arregla con una opción:

```python
drivers = spark.read.format("json").option("multiLine", True).load("data/drivers_multiline.json")
```

> [!WARNING]
> El error contrario es más traicionero. Si lees un archivo JSON Lines con `multiLine` activado, Spark lee el primer registro y se detiene: el archivo de 885 pilotos devuelve **1 fila**, sin ningún error.

### Campos anidados

Para llegar a un campo dentro de un struct se usa un punto. La columna resultante toma el nombre del campo:

```python
drivers.select("driverRef", "name.forename", "name.surname").show(2)
```

```output
+---------+--------+---------+
|driverRef|forename|  surname|
+---------+--------+---------+
|   Cannoc|    John|   Cannon|
|   Changy|   Alain|de Changy|
+---------+--------+---------+
only showing top 2 rows
```

Con `"name.*"` se sacan todos los campos del struct de una vez.

## Errores comunes

- **Olvidar `header`.** Las columnas se llaman `_c0`, `_c1`… y aparece una fila de más.
- **Escribir `true` en minúscula.** En Python es `True`; `true` da `NameError`.
- **Olvidar los paréntesis del tipo.** Es `StringType()`, no `StringType`.
- **Cambiar el orden de las columnas en un esquema de CSV.** Los datos quedan bajo otro nombre.
- **Ver `_corrupt_record` y seguir adelante.** Casi siempre significa que falta `multiLine`.
