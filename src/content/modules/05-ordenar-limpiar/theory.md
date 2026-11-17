## Ordenar: sort y orderBy

`sort` y `orderBy` son la misma función con dos nombres. Reciben una o varias columnas y, para cada una, el sentido: ascendente, que es el de por defecto, o descendente.

```python
sales.sort(F.col("Item_Weight").desc()).select("Item_Identifier", "Item_Weight", "Item_MRP").show(3)
```

```output
+---------------+-----------+--------+
|Item_Identifier|Item_Weight|Item_MRP|
+---------------+-----------+--------+
|          FDC02|      21.35|259.9278|
|          FDC02|      21.35|258.3278|
|          FDC02|      21.35|258.5278|
+---------------+-----------+--------+
only showing top 3 rows
```

Hay varias formas de escribir lo mismo. Todas estas ordenan por precio de mayor a menor:

```python
sales.sort(F.col("Item_MRP").desc())
sales.sort(F.desc("Item_MRP"))
sales.orderBy("Item_MRP", ascending=False)
```

### Varias columnas

Con varias columnas, la segunda solo decide cuando la primera empata. Cada una lleva su propio sentido:

```python
sales.sort(F.col("Item_Weight").desc(), F.col("Item_Visibility").asc())
```

Siete productos pesan 21.35, el máximo. Entre ellos, el de menor visibilidad queda el primero. Existe también una forma con listas, que se lee peor pero aparece en muchos tutoriales: `sales.sort(["Item_Weight", "Item_Visibility"], ascending=[False, True])`.

### Dónde quedan los nulos

> [!NOTE]
> Al ordenar de forma ascendente, los nulos salen **primero**; en descendente, **al final**. Así, `sort("Item_Weight")` empieza por 1463 filas sin peso. Si no es lo que quieres, hay variantes explícitas: `asc_nulls_last()` y `desc_nulls_first()`.

`sort` es una transformación **wide**: para ordenar hay que comparar filas que están en particiones distintas, así que provoca un shuffle. No lo pongas en medio de un pipeline si solo lo necesitas al final.

## Los N primeros: sort + limit

`limit(n)` recorta un DataFrame a `n` filas. Con `sort` delante, da los N mayores o menores:

```python
sales.sort(F.col("Item_MRP").desc()).limit(3).select("Item_Identifier", "Item_Type", "Item_MRP").show()
```

```output
+---------------+---------+--------+
|Item_Identifier|Item_Type|Item_MRP|
+---------------+---------+--------+
|          FDS13|   Canned|266.8884|
|          FDR25|   Canned|266.8884|
|          FDK51|    Dairy|266.6884|
+---------------+---------+--------+
```

> [!WARNING]
> `limit` sin `sort` devuelve las primeras filas que Spark encuentra, y eso puede cambiar de una ejecución a otra. "Las 10 primeras" solo significa algo después de ordenar.

## Quitar columnas: drop

`drop` es el contrario de `select`: en vez de decir qué columnas quieres, dices cuáles sobran. Acepta varias separadas por comas:

```python
sales.drop("Item_Visibility", "Item_Type").columns
```

```output
['Item_Identifier', 'Item_Weight', 'Item_Fat_Content', 'Item_MRP', 'Outlet_Identifier',
 'Outlet_Establishment_Year', 'Outlet_Size', 'Outlet_Location_Type', 'Outlet_Type', 'Item_Outlet_Sales']
```

Como `withColumnRenamed`, **no avisa** si la columna no existe: con una errata, devuelve el DataFrame intacto. Después de un `drop` importante, mira `df.columns`.

## Duplicados: dropDuplicates y distinct

`dropDuplicates()` sin argumentos quita las filas en las que **todas** las columnas coinciden. `distinct()` hace exactamente lo mismo. Con una lista de columnas, `dropDuplicates(["col1", "col2"])` compara solo esas y se queda con **una** fila por combinación.

Con un DataFrame pequeño de pedidos, con filas repetidas de verdad:

```python
orders.show()
```

```output
+--------+--------+-----------+------+
|order_id|customer|  item_type|amount|
+--------+--------+-----------+------+
|       1|     ana|      Dairy|  12.5|
|       2|    luis|       Meat|  30.0|
|       2|    luis|       Meat|  30.0|
|       3|     ana|      Dairy|   8.0|
|       4|   marta|Snack Foods|   5.5|
|       4|   marta|Snack Foods|   5.5|
|       4|   marta|Snack Foods|   5.5|
|       5|    luis|      Dairy|  12.5|
+--------+--------+-----------+------+
```

| Llamada                                            | Filas | Qué compara                           |
| -------------------------------------------------- | ----- | ------------------------------------- |
| `orders.dropDuplicates()`                          | 5     | Las cuatro columnas                   |
| `orders.distinct()`                                | 5     | Lo mismo                              |
| `orders.dropDuplicates(["customer"])`              | 3     | Solo `customer`: una fila por cliente |
| `orders.dropDuplicates(["customer", "item_type"])` | 4     | La pareja cliente y tipo              |

> [!WARNING]
> Con una lista de columnas, Spark conserva **una** de las filas repetidas, pero **no garantiza cuál**. Si necesitas la más reciente o la más cara, hay que elegirla con una window function, que verás en el módulo 10.

Un detalle sobre BigMart: **no tiene ninguna fila totalmente repetida**. `sales.dropDuplicates().count()` devuelve 8523, igual que antes. Muchos tutoriales lo usan como ejemplo de deduplicación y no se nota que no ha cambiado nada.

Para ver los valores distintos de una columna, selecciona primero y quita repetidos después: `sales.select("Item_Type").distinct()` devuelve 16 filas de una columna. Al revés, `sales.distinct().select("Item_Type")`, devuelve las 8523.

## Nulos: quitar con dropna

`dropna` elimina filas con nulos y tiene dos mandos:

- `how`: `"any"`, el de por defecto, quita la fila si **alguna** columna mirada es nula; `"all"` solo si lo son **todas**.
- `subset`: la lista de columnas que se miran. Sin él, se miran todas.

![Tres resultados de dropna sobre una tabla de cuatro filas: how any deja una, how all deja tres y subset sobre Size deja dos](diagram:dropna-modes 'Los tres modos de dropna sobre la misma tabla, y lo que hacen con BigMart.')

En BigMart hay nulos en dos columnas, `Item_Weight` (1463) y `Outlet_Size` (2410), y ninguna fila los tiene en las dos a la vez:

```python
sales.dropna(how="any").count()                 # 4650
sales.dropna(how="all").count()                 # 8523
sales.dropna(subset=["Outlet_Size"]).count()    # 6113
```

`how="any"` tira el 45 % de las filas. Casi siempre lo que quieres es `subset`: quitar las filas a las que les falta **la** columna que necesitas para lo que viene después.

> [!EXTRA]
> `dropna(thresh=n)` conserva las filas con al menos `n` valores no nulos. Y `df.na.drop(...)` y `df.na.fill(...)` son otros nombres de `dropna` y `fillna`; los verás en código ajeno.

## Nulos: rellenar con fillna

`fillna(valor)` sustituye los nulos por un valor, y tiene una regla que sorprende: **solo rellena las columnas cuyo tipo encaja con el valor**. Un texto rellena las de texto; un número, las numéricas. Las demás se quedan como están, sin aviso.

```python
sales.fillna("Not Available").filter(F.col("Outlet_Size").isNull()).count()   # 0
sales.fillna("Not Available").filter(F.col("Item_Weight").isNull()).count()   # 1463: sigue igual
```

Ni siquiera pedirlo con `subset` lo fuerza: `sales.fillna("Not Available", subset=["Item_Weight"])` deja los 1463 nulos donde estaban. Un diccionario evita el problema, porque da a cada columna un valor de su tipo:

```python
filled = sales.fillna({"Outlet_Size": "Unknown", "Item_Weight": 12.86})
```

El 12.86 es la media de los pesos conocidos; rellenar con la media o la mediana es habitual, pero tiene un coste: a partir de ahí, 1463 filas tienen un peso inventado y cualquier estadística sobre esa columna lo arrastra. Un valor claramente artificial, como `"Unknown"` en `Outlet_Size`, al menos se puede filtrar después.

## Errores comunes

- **Ordenar y esperar que los nulos queden al final.** En ascendente van primero. Usa `asc_nulls_last()`.
- **`limit` sin `sort`.** Devuelve filas cualesquiera, no "las primeras".
- **`drop` con una errata.** No da error; la columna sigue ahí.
- **`dropDuplicates()` sin argumentos en una tabla sin duplicados exactos.** No cambia nada. Piensa qué columnas definen un repetido y pásalas.
- **`dropna()` a secas.** Es `how="any"` sobre todas las columnas: puede tirar casi la mitad de los datos. Usa `subset`.
- **`fillna("texto")` esperando que rellene números.** Solo toca las columnas de texto. Usa un diccionario.
- **Olvidar asignar.** `sales.dropna()` solo, sin `sales = ...`, no cambia `sales`. Los DataFrames son inmutables.
