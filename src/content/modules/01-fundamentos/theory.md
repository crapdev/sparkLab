## El problema que resuelve Spark

Tienes que procesar un archivo. Si cabe en la memoria de tu portátil, con pandas te basta. Pero los datos crecen, y cuando ya no caben tienes dos caminos:

- **Escalar hacia arriba (vertical):** comprar una máquina más grande. Funciona hasta que se acaba el presupuesto o no existe una máquina mayor.
- **Escalar hacia los lados (horizontal):** repartir el trabajo entre muchas máquinas normales. Si necesitas más capacidad, añades máquinas.

Spark es un **motor de cómputo distribuido**: toma tu código, lo divide en trozos y los ejecuta en paralelo sobre un grupo de máquinas, llamado **clúster**. Tú escribes como si trabajaras con una sola tabla y Spark se ocupa del reparto.

## Las piezas de un clúster

![Arquitectura de Spark: tu código llega al driver, que pide recursos al cluster manager y reparte tasks entre los executors de tres workers](diagram:cluster-architecture 'El driver planifica; los executors hacen el trabajo.')

| Pieza               | Qué hace                                                                                                                |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Driver**          | Recibe tu código, construye el plan, lo divide en tasks y las reparte. Es el cerebro.                                   |
| **Executors**       | Procesos que ejecutan las tasks sobre los datos y devuelven resultados. Son las manos.                                  |
| **Workers**         | Las máquinas donde viven los executors.                                                                                 |
| **Cluster manager** | Decide cuántos recursos (CPU y memoria) recibe cada aplicación. Puede ser YARN, Kubernetes o el gestor propio de Spark. |

Una idea para no olvidar: **los datos grandes nunca deberían pasar por el driver**. El driver coordina; quien mueve los datos son los executors. Por eso traerse un DataFrame enorme a Python con `collect()` suele acabar mal.

> [!NOTE]
> En Colab, y en tu portátil, Spark corre en **modo local**: el driver y los executors viven en un solo proceso y usan los núcleos de esa máquina. No hay clúster de verdad, pero el código es idéntico al que escribirías para mil máquinas.

## Transformaciones y acciones

Los DataFrames de Spark son **inmutables**: ninguna operación cambia un DataFrame, siempre devuelve uno nuevo. Las operaciones son de dos tipos.

|                  | Transformación                                                  | Acción                                                           |
| ---------------- | --------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Qué devuelve** | Otro DataFrame                                                  | Un resultado en Python, o algo en pantalla                       |
| **Ejecuta algo** | No                                                              | Sí                                                               |
| **Ejemplos**     | `select`, `filter`, `withColumn`, `groupBy`, `orderBy`, `limit` | `show`, `count`, `collect`, `take`, `first`, `toPandas`, `write` |

```python
from pyspark.sql import functions as F

numbers = spark.range(1, 1001)                        # ids from 1 to 1000
multiples = numbers.filter(F.col("id") % 7 == 0)      # transformation
squared = multiples.withColumn("squared", F.col("id") * F.col("id"))  # transformation

squared.show(3)                                       # action
```

```output
+---+-------+
| id|squared|
+---+-------+
|  7|     49|
| 14|    196|
| 21|    441|
+---+-------+
only showing top 3 rows
```

## Lazy evaluation: Spark no tiene prisa

Las tres primeras líneas del ejemplo no calculan nada. Spark solo apunta los pasos en un **plan**. El cálculo empieza cuando llega la acción, `show(3)`.

![Evaluación perezosa: range, filter y withColumn solo se apuntan en un plan; al llegar la acción count, Spark optimiza el plan y lo ejecuta](diagram:lazy-evaluation 'Las transformaciones construyen la receta; la acción la cocina.')

¿Por qué esperar? Porque al ver la receta completa, Spark puede **optimizarla** antes de ejecutarla: aplicar los filtros cuanto antes, leer solo las columnas que se usan o juntar varios pasos en uno. Si ejecutara cada línea al momento, perdería esa oportunidad.

Puedes ver el plan sin ejecutarlo con `explain()`:

```python
squared.explain()
```

```output
== Physical Plan ==
*(1) Project [id#0L, (id#0L * id#0L) AS squared#8L]
+- *(1) Filter ((id#0L % 7) = 0)
   +- *(1) Range (1, 1001, step=1, splits=8)
```

Se lee de abajo arriba: genera el rango, filtra, y calcula la columna nueva. El `splits=8` es el número de particiones, que en modo local depende de los núcleos de tu máquina.

## Las acciones que vas a usar

Una acción es el momento en que Spark deja de apuntar y se pone a calcular. Estas son las que aparecen una y otra vez. Los jobs están medidos sobre el pipeline anterior, de 142 filas en 8 particiones:

| Acción                | Qué devuelve                                   | Para qué                                      | Jobs · tasks |
| --------------------- | ---------------------------------------------- | --------------------------------------------- | ------------ |
| `show(n)`             | Nada: imprime una tabla                        | Mirar unas filas                              | 1 · 1        |
| `count()`             | Un `int`                                       | Saber cuántas filas hay                       | 1 · 9        |
| `take(n)` y `head(n)` | Una lista de `n` objetos `Row`                 | Traer unas pocas filas a Python               | 1 · 1        |
| `first()` y `head()`  | Un `Row`, o `None` si está vacío               | Sacar un valor, por ejemplo de una agregación | 1 · 1        |
| `collect()`           | Una lista con **todas** las filas              | Traer un resultado pequeño entero a Python    | 1 · 8        |
| `toPandas()`          | Un DataFrame de **pandas** con todas las filas | Seguir en pandas o dibujar un gráfico         | 1 · 8        |
| `write.…`             | Nada: crea archivos                            | Guardar el resultado en disco                 | 1 · 8        |

Las que traen pocas filas (`take`, `first`, `show`) leen solo la partición que necesitan: 1 task. Las que traen todo (`collect`, `toPandas`, `write`) tocan las 8 particiones.

```python
squared.take(2)
```

```output
[Row(id=7, squared=49), Row(id=14, squared=196)]
```

Un `Row` se usa como un diccionario: `squared.first()["squared"]` devuelve `49`. Es la forma habitual de sacar el número de una agregación: `df.agg(F.max("squared")).first()[0]`.

### limit() no es take()

Se parecen, pero están en bandos distintos:

- `df.limit(5)` es una **transformación**: devuelve otro DataFrame de como mucho 5 filas y no lanza ningún job. Sirve para recortar un DataFrame y seguir trabajando con él en Spark.
- `df.take(5)` es una **acción**: devuelve una lista de Python con 5 `Row` y lanza un job.

Por eso `df.limit(5).show()` lanza 1 job: el de `show`, no el de `limit`.

> [!WARNING]
> **`collect()` y `toPandas()` traen todo al driver.** El driver es un solo proceso con una memoria limitada. Con 142 filas, o con las 8523 de BigMart, no pasa nada. Con una tabla de 500 millones de filas, el driver se queda sin memoria y la sesión muere. Antes de llamar a cualquiera de las dos, reduce: filtra, agrega o usa `limit`. Y si solo quieres mirar, `show()` o `take(n)` bastan.

Escribir también es una acción, aunque no devuelva nada a Python: `df.write.mode("overwrite").csv("salida/multiples")` lanza un job y deja un archivo por partición, 8 en este caso. Lo verás a fondo en el módulo 12.

## Job, Stage y Task

Cuando una acción pone a Spark a trabajar, el trabajo se organiza en tres niveles:

- **Job:** todo el trabajo necesario para responder a una acción.
- **Stage:** un tramo del job que se puede hacer sin mover datos entre particiones.
- **Task:** la unidad mínima: un stage aplicado a **una partición**. Es lo que recibe un executor.

![Un job dividido en dos stages separados por un shuffle; cada stage tiene cuatro tasks, una por partición](diagram:job-stage-task 'Un groupBy sobre 4 particiones: 1 job, 2 stages, 8 tasks.')

Los datos de un DataFrame están repartidos en **particiones**. Cada stage lanza una task por partición, así que más particiones significa más tasks en paralelo.

> [!WARNING]
> Es habitual oír que «el código que envías es un job». No es exacto: **cada acción dispara al menos un job**. Una celda sin acciones no dispara ninguno, y una celda con tres acciones dispara al menos tres. Además, con las optimizaciones adaptativas de Spark (AQE), una sola acción puede repartirse en varios jobs. En el laboratorio lo mides.

Hay un caso que despista. Al leer un CSV aparece un job aunque no hayas llamado a ninguna acción. No es un error: para saber los nombres de las columnas (`header`) y sus tipos (`inferSchema`), Spark tiene que abrir el archivo. Medido en el laboratorio:

| Forma de leer el CSV          | Jobs al leer |
| ----------------------------- | ------------ |
| Solo `header`                 | 1            |
| `header` + `inferSchema`      | 2            |
| Con el esquema escrito por ti | 0            |

> [!EXTRA]
> **Narrow y wide.** Lo que separa un stage del siguiente es el tipo de transformación.
>
> - **Narrow** (`filter`, `select`, `withColumn`): cada partición se procesa sola. Varias seguidas caben en un mismo stage.
> - **Wide** (`groupBy`, `orderBy`, `join`): hay que juntar filas que están en particiones distintas. Ese movimiento se llama **shuffle**, es caro y abre un stage nuevo.
>
> Cuando un job va lento, casi siempre hay un shuffle detrás. Lo verás a fondo en el módulo 14.

## Por qué Spark es rápido y resistente

- **Trabaja en memoria.** Hadoop MapReduce, su antecesor, escribía en disco el resultado de cada paso intermedio. Spark mantiene esos resultados en memoria siempre que puede, y eso lo hace mucho más rápido en cadenas largas de operaciones.
- **Tolera fallos.** Spark recuerda la receta con la que se construyó cada dato, su **linaje**. Si una máquina se cae a mitad del trabajo, vuelve a calcular solo lo que se perdió.
- **Habla varios lenguajes.** Tiene API para Python, SQL, Scala y R. **PySpark** es la de Python, y todas acaban en el mismo motor.

## Colab frente a Databricks

Muchos tutoriales de PySpark usan Databricks. Los laboratorios de este sitio usan Google Colab, que es gratis y solo pide una cuenta de Google. El código de PySpark es el mismo; cambia lo que lo rodea:

| En Databricks               | En Colab                                           |
| --------------------------- | -------------------------------------------------- |
| `spark` ya existe           | La creas con `SparkSession.builder.getOrCreate()`  |
| `display(df)`               | `df.show()`                                        |
| Rutas `dbfs:/FileStore/...` | Rutas locales, como `data/archivo.csv`             |
| `dbutils.fs.ls(...)`        | `os.listdir(...)`                                  |
| Celda `%sql`                | `spark.sql("...")`                                 |
| Pestaña "Spark Jobs"        | `explain()` y la función `measure` del laboratorio |

> [!NOTE]
> Si quieres probar Databricks: **Community Edition**, la versión gratuita que aparece en muchos tutoriales, se retiró el 1 de enero de 2026. Su sustituta es **Free Edition**, con otro proceso de registro y otra forma de subir archivos.

Otra diferencia es de estilo. En muchos tutoriales las funciones se importan con `from pyspark.sql.functions import *`. Eso reemplaza funciones de Python como `sum`, `min`, `max` y `round` por las de Spark y provoca errores difíciles de entender. Aquí se usa la convención habitual en proyectos reales:

```python
from pyspark.sql import functions as F

df.filter(F.col("id") > 10)
```

Si sigues un tutorial que usa `import *`, donde escriba `col(...)` tú escribes `F.col(...)`.

## Errores comunes

- **Esperar que una transformación haga algo.** Si no ves resultados, probablemente falta la acción.
- **Olvidar que los DataFrames son inmutables.** `df.filter(...)` solo, sin asignarlo, no cambia `df`. Hay que guardar el resultado: `df = df.filter(...)`.
- **Usar `collect()` o `toPandas()` con datos grandes.** Traen todas las filas al driver y pueden dejarlo sin memoria. Para mirar, usa `show()` o `take(n)`; para traer, reduce antes.
- **Creer que `limit(5)` trae filas a Python.** Devuelve otro DataFrame. Para una lista, `take(5)`.
- **Escribir `true` en vez de `True`.** En Python los booleanos van con mayúscula; `true` da `NameError`.
