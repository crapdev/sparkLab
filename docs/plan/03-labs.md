# 03 · Laboratorios, tests y datasets

## Idea general

PySpark necesita la JVM y no corre en el navegador. Cada módulo tiene un
notebook que se abre en Google Colab con un clic. El usuario lo resuelve allí,
los tests le dicen si está bien, guarda su copia en su Drive y vuelve al sitio a
marcar el lab como completado.

## Por qué hace falta el repositorio de GitHub

Colab solo abre notebooks desde tres sitios: GitHub, Google Drive o un Gist. No
puede abrir un archivo servido por Vercel. El botón "Abrir en Google Colab" es
un enlace con esta forma:

```
https://colab.research.google.com/github/USUARIO/REPOSITORIO/blob/main/labs/01-fundamentos/lab.ipynb
```

Por eso necesito saber `USUARIO/REPOSITORIO`. Dos consecuencias:

- **El repositorio tiene que ser público.** Si es privado, tus compañeros no
  podrán abrir los notebooks.
- **No bloquea nada ahora.** El valor vive en `src/config.js` y se rellena
  cuando crees el repo. Mientras tanto los botones apuntan a un marcador.

## Una sola fuente por lab

Cada lab se escribe una vez, en `labs/NN-slug/source.py`, con la solución
marcada. `scripts/build-labs.py` genera los dos notebooks:

```python
# %% [markdown]
# ## Tarea 1 · Filtra las bebidas ligeras

# %%
# TODO: keep only "Soft Drinks" lighter than 10 kg
### BEGIN SOLUTION
light_drinks = df.filter((F.col("Item_Type") == "Soft Drinks") & (F.col("Item_Weight") < 10))
### END SOLUTION
### STARTER
# light_drinks = ...
### END STARTER

# %% tags=["test"]
check("Tarea 1", light_drinks.count() == 166, "Revisa el operador entre las dos condiciones.")
```

| Notebook         | Contiene                             |
| ---------------- | ------------------------------------ |
| `lab.ipynb`      | El bloque `STARTER`, sin la solución |
| `solution.ipynb` | El bloque `SOLUTION`, sin el starter |

Los dos se guardan en el repositorio, porque Colab los abre desde GitHub.

## Estructura de un notebook

1. **Cabecera:** título, objetivo, enlace de vuelta al módulo e instrucción de
   "Archivo → Guardar una copia en Drive".
2. **Instalación:** una celda que instala la versión fijada de PySpark.
3. **Sesión:** crea la `SparkSession`.
4. **Datos:** descarga los datasets desde `DATA_BASE_URL`.
5. **Utilidades de test:** la función `check()`.
6. **Tareas:** cada una con explicación, celda de código y celda de tests.
7. **Resumen:** cuántas tareas pasan y un mensaje final.

### La función `check`

Los `assert` sueltos dan un error poco amigable. Cada test usa una función
pequeña definida en el propio notebook, que por dentro hace un `assert`:

```python
def check(name, condition, hint):
    """Assert a condition and print a readable result."""
    if not condition:
        print(f"❌ {name}: todavía no. Pista: {hint}")
    assert condition, f"{name}: {hint}"
    print(f"✅ {name}")
```

El texto que ve el usuario va en español; el código, en inglés.

### Qué comprueban los tests

- Número de filas y columnas.
- Nombres y tipos de las columnas (`df.schema`).
- Valores concretos: una agregación, una fila conocida.
- Estado en disco, en los módulos de escritura y tablas.

Los tests no dependen del orden de las filas salvo que la tarea sea ordenar, ni
de la fecha del día.

## `scripts/check-labs.py`

Recorre todos los labs y comprueba dos cosas:

| Comprobación                                    | Qué garantiza                             |
| ----------------------------------------------- | ----------------------------------------- |
| `solution.ipynb` se ejecuta entero sin errores  | La solución es correcta y los tests pasan |
| `lab.ipynb` sin resolver **falla** en los tests | Los tests prueban algo de verdad          |

Usa los datos locales de `public/data/` (variable de entorno
`PYSPARK_LABS_DATA_DIR`), así no depende de la red ni de que el sitio esté
publicado. Se ejecuta con `npm run labs:check`.

## La URL de los datasets

Los notebooks de Colab descargan los datos del sitio en Vercel. Como esa URL no
existe hasta publicar, cada notebook tiene una única constante:

```python
DATA_BASE_URL = "https://TU-SITIO.vercel.app/data"
```

`scripts/set-data-url.py https://pyspark-labs.vercel.app/data` la cambia en
todos los `source.py` y regenera los notebooks. Es un comando, una vez, después
del primer despliegue.

## Versiones

Comprobado en PyPI el 2026-11-16:

| Paquete       | Última versión | Nota                                |
| ------------- | -------------- | ----------------------------------- |
| `pyspark`     | 4.3.0          | Soporta Python 3.11 a 3.14          |
| `delta-spark` | 4.4.1          | Exige `pyspark` entre 4.0.1 y 4.2.0 |

- **Propuesta:** fijar `pyspark==4.2.0`, la más reciente compatible con Delta.
  Se confirma instalándola en local antes de escribir el primer lab.
- **Java:** Spark 4 necesita Java 17 o superior. En local hay Java 21. En Colab
  la celda de instalación comprobará la versión y, si hace falta, instalará
  OpenJDK 17.
- **Local frente a Colab:** aquí hay Python 3.14 y en Colab otra versión. Con la
  misma versión de PySpark fijada en los dos lados el comportamiento es el
  mismo, pero **yo no puedo ejecutar Colab**. Cuando el lab 1 esté listo te
  pediré que lo abras allí una vez y confirmes que la celda de instalación y
  los tests funcionan.
- **Delta Lake:** si `delta-spark` da problemas en Colab, el módulo 12 se queda
  con Delta en teoría y quiz, sin sección práctica.

El entorno local va en `.venv/` (ignorado por git) con `requirements-labs.txt`.

## Datasets

Todos en `public/data/`, un solo lugar.

| Archivo                  | Contenido                                                  | Origen                                     | Usado en               |
| ------------------------ | ---------------------------------------------------------- | ------------------------------------------ | ---------------------- |
| `bigmart_sales.csv`      | 8523 filas, 12 columnas                                    | El que ya tenías (renombrado, sin espacio) | Casi todos los módulos |
| `drivers.json`           | 885 pilotos de F1, un objeto por línea, con `name` anidado | API Jolpica-F1                             | Módulos 2 y 6          |
| `drivers_multiline.json` | 20 pilotos como array con sangría                          | Derivado del anterior                      | Módulo 2 (`multiLine`) |

Los DataFrames pequeños de ejemplo (union, joins, `collect_list`) se crean
dentro del notebook con `spark.createDataFrame`, no son archivos.

### `drivers.json`

Ergast, la fuente original, cerró; Jolpica-F1 es su sucesora y mantiene los
mismos datos. La API no devuelve el formato del curso, así que
`scripts/fetch-drivers.py` lo convierte: un JSON por línea, con `name` como
objeto anidado (`forename`, `surname`), que es lo que hace interesante el
ejercicio de `multiLine` y de campos anidados.

Dos diferencias con el archivo del curso, que no afectan a lo que se practica:

- `driverId` es un número correlativo propio, no el ID original de Ergast.
- Hay más pilotos, porque incluye las temporadas recientes.

Trae nulos de forma natural, útiles para practicar: 765 pilotos sin `code` y
811 sin `number`.

### Licencias

- **BigMart Sales** viene de un reto de práctica de Analytics Vidhya y circula
  ampliamente en Kaggle, pero no tiene una licencia abierta explícita. Para un
  recurso educativo sin ánimo de lucro es el uso habitual; lo dejo indicado en
  el README con su origen. Si prefieres no redistribuirlo, la alternativa es
  que cada notebook lo descargue de otra fuente.
- **Jolpica-F1** se cita como fuente en el README y en la página "Acerca".

## Flujo del usuario

1. Abre el módulo en el sitio y lee la teoría.
2. Pulsa "Abrir en Google Colab".
3. En Colab: "Guardar una copia en Drive", ejecuta la instalación y resuelve.
4. Los tests muestran ✅ o ❌ con una pista.
5. Vuelve al sitio y marca el lab como completado.
6. Si se atasca, el módulo enlaza a `solution.ipynb`.
