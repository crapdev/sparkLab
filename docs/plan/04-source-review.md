# 04 · Revisión de las notas fuente

Las notas de `material/` las generó Gemini viendo el video por fotogramas. Sirven
como guion, pero el código y los ejemplos de filas no son fiables. Aquí está
todo lo que encontré dudoso, cómo lo sé y qué haré con ello.

Cómo leer la columna "Estado":

- **CSV:** comprobado contra `BigMart Sales.csv` (8523 filas, 12 columnas).
- **Pendiente:** lo sé por conocimiento de PySpark; se confirma al ejecutar en
  la fase de construcción. Si la ejecución me contradice, te aviso y corrijo.
- **Sin verificar:** no hay forma de saberlo sin el video o el notebook original.

## Errores que ya habías detectado

| Tema                                   | Tratamiento                                                             |
| -------------------------------------- | ----------------------------------------------------------------------- |
| Fila de ejemplo "ABC \| 1.2" inventada | Se usan filas reales; la primera es `FDA15`, 9.3, `Low Fat` (CSV)       |
| Esquemas con columnas faltantes        | Los esquemas DDL y `StructType` llevan las 12 columnas reales (CSV)     |
| `drivers.json` es el dataset de F1     | Reconstruido desde Jolpica-F1, ver [03-labs.md](03-labs.md#driversjson) |
| "El código de una celda es un Job"     | Se explica que cada acción dispara al menos un Job                      |

## Datos de ejemplo que no coinciden con el dataset

| Las notas dicen                                                   | Realidad                                                                            | Estado |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------ |
| `row_number`: `DRA12` tres veces y `DRA24` en la fila 4           | `DRA12` aparece 6 veces; `DRA24` empezaría en la 7                                  | CSV    |
| Suma acumulada con valores `51.0`, `144.0`, `195.0`               | `Item_MRP` tiene cuatro decimales (ej. 249.8092); esos valores parecen inventados   | CSV    |
| `dropDuplicates()` elimina filas repetidas                        | No hay ninguna fila totalmente duplicada; no cambia nada                            | CSV    |
| `regexp_replace` convierte `Regular` en `reg` y `Low Fat` en `LF` | El dato crudo ya trae cinco variantes: `Low Fat`, `Regular`, `LF`, `reg`, `low fat` | CSV    |
| El filtro de nulos devuelve Tier 1 o Tier 2                       | Solo hay Tier 2 con `Outlet_Size` nulo; ninguna fila Tier 1                         | CSV    |

Lo que **sí** coincide: 16 tipos de ítem; unas 6100 filas tras quitar nulos de
`Outlet_Size` (son 6113); `NCZ54` siete veces y `NCZ53` después con rank 8;
total de `Item_MRP` cerca de 1,2 millones (1 201 681); `Item_Fat_Content = 'LF'`
devuelve filas (316); y los conteos de los cuatro joins con el ejemplo
`d01`…`d06` (5, 6, 6 y 1).

## Explicaciones inexactas o incompletas

| Tema                          | Las notas dicen                                  | Lo correcto                                                                                                            | Estado               |
| ----------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | -------------------- |
| Suma con ventana sin marco    | Repite el total de cada `Item_Type` en sus filas | Da un acumulado en el que las filas empatadas comparten valor                                                          | Tratado en módulo 10 |
| UDF sin tipo de retorno       | Devuelve el cuadrado del valor                   | Lo devuelve como texto; hay que declarar el tipo                                                                       | Tratado en módulo 11 |
| `fillna("Not Available")`     | Rellena nulos en cualquier parte                 | Solo en columnas de texto; `Item_Weight` no cambia                                                                     | Pendiente            |
| `cast` con un valor imposible | Devuelve `NULL`                                  | En Spark 4 el modo ANSI está activado: falla al ejecutar con `CAST_INVALID_INPUT`; para `NULL` hay que usar `try_cast` | Tratado en módulo 4  |
| Delta frente a Parquet        | En Delta la metadata sale del archivo Parquet    | Los archivos siguen siendo Parquet con su footer; el log añade metadata de tabla                                       | Pendiente            |
| `save(".../data.csv")`        | Crea "el archivo (o carpeta)"                    | Crea una carpeta con ese nombre y archivos `part-` dentro                                                              | Pendiente            |
| Opciones al leer JSON         | Usa `inferSchema` y `header`                     | Ninguna de las dos aplica a JSON                                                                                       | Pendiente            |
| Hadoop                        | "Usaba memoria en disco"                         | MapReduce escribe resultados intermedios en disco; Spark los mantiene en memoria                                       | Conocimiento general |
| Cluster manager               | "Crea los worker nodes"                          | Asigna recursos; los executors corren en los workers                                                                   | Conocimiento general |
| Escalado                      | "Infinito"                                       | Horizontal, con límites prácticos                                                                                      | Conocimiento general |
| Anti join                     | "No existe en SQL clásico"                       | Spark SQL tiene `LEFT ANTI JOIN`; en SQL estándar se hace con `NOT EXISTS`                                             | Tratado en módulo 9  |
| `union`                       | Apila por posición                               | Cierto, y además no elimina duplicados (equivale a `UNION ALL`)                                                        | Tratado en módulo 9  |
| `date_format` con `YYYY`      | Da error                                         | Plausible: Spark 3 y posteriores rechazan los patrones de año por semana                                               | Pendiente            |
| Parquet                       | "Guardando la metadata particionada"             | Frase sin sentido; se ignora                                                                                           | —                    |

## Contradicciones

- **`Item_Weight` como texto.** La Parte 2 dice que `df` quedó de forma
  permanente con `Item_Weight` convertido a string, y a continuación ordena por
  esa columna. Ordenar texto da un orden alfabético ("9.3" va después de
  "21.35"), que no es lo que el video muestra. No sé si el instructor reasignó
  `df` o no. **Sin verificar.** En los labs cada módulo carga el CSV limpio, así
  que no arrastra este estado.
- **`fillna` y el punto anterior.** Si `Item_Weight` fuera texto, `fillna` sí lo
  rellenaría. Depende de la misma duda.

## Código que las notas no capturaron

| Falta                                     | Qué haré                                                            |
| ----------------------------------------- | ------------------------------------------------------------------- |
| Creación de `df1` y `df2` para `union`    | Los escribo con `spark.createDataFrame`                             |
| Creación de `df_book` para `collect_list` | Igual, con el ejemplo de usuarios y libros                          |
| Creación de `df1` y `df2` para joins      | Igual, respetando las claves `d01`…`d06` que sí describen las notas |
| Esquemas completos                        | Las 12 columnas con tipos inferidos del CSV                         |
| Columnas y filas de `drivers.json`        | Las del archivo reconstruido                                        |
| Código de Delta y de tablas externas      | Solo hay teoría; el código es mío                                   |
| `partitionBy` en ventanas                 | El índice lo nombra, las notas no lo muestran; va como extra        |

## Cosas del video que no aplican fuera de Databricks

| En el video                 | En Colab                                           |
| --------------------------- | -------------------------------------------------- |
| `display(df)`               | `df.show()`                                        |
| `dbutils.fs.ls(...)`        | `os.listdir(...)` o `!ls`                          |
| Rutas `dbfs:/FileStore/...` | Rutas locales del notebook                         |
| Celda `%sql`                | `spark.sql("...")`                                 |
| Clúster creado a mano       | `SparkSession.builder.getOrCreate()`               |
| Pestaña "Spark Jobs"        | `spark.sparkContext.statusTracker()` y `explain()` |

Además, creo que Databricks sustituyó Community Edition por Free Edition en
2025, con otro flujo de registro y de subida de archivos. Lo compruebo antes de
escribir esa sección; si es así, se dice en el módulo 1 para que nadie se pierda
siguiendo el video.

## Decisión de estilo: `import *`

El curso usa `from pyspark.sql.functions import *`. Eso reemplaza funciones
propias de Python como `sum`, `min`, `max` y `round` por las de Spark, y provoca
errores difíciles de entender. El sitio usa la convención profesional:

```python
from pyspark.sql import functions as F

df.groupBy("Item_Type").agg(F.sum("Item_MRP"))
```

El módulo 1 explica la diferencia para quien siga el video en paralelo.

## Cómo reducir la incertidumbre

El índice dice que el notebook oficial del curso está enlazado en la descripción
del video. Si lo descargas a `material/`, puedo cerrar todos los puntos "Sin
verificar" y contrastar el código en vez de reconstruirlo.
