# 05 · Fases, entregas y despliegue

Cuatro fases, con una parada para tu revisión al final de cada una.

| Fase | Entrega                            | Estado                      |
| ---- | ---------------------------------- | --------------------------- |
| 1    | Revisión del material y este plan  | En revisión                 |
| 2    | Base del sitio + módulo 1 completo | Pendiente de tu visto bueno |
| 3    | Módulos 2 a 15                     | Pendiente                   |
| 4    | Publicación en GitHub y Vercel     | Pendiente                   |

## Fase 2 · Base del sitio y módulo 1

Orden de trabajo, con un commit por paso:

| #   | Commit                                   | Contenido                                                                            |
| --- | ---------------------------------------- | ------------------------------------------------------------------------------------ |
| 1   | `chore: scaffold Vite project`           | `package.json`, Vite, `.gitignore` (con `material/`, `.venv/`, `dist/`), rama `main` |
| 2   | `chore: add ESLint, Prettier and Vitest` | Configuración y scripts de npm                                                       |
| 3   | `chore: add datasets`                    | Renombrar el CSV, `drivers.json`, script de descarga                                 |
| 4   | `feat: add storage service`              | `storage.js` con sus tests                                                           |
| 5   | `feat: add router and layout`            | Router, cabecera, pie con créditos, tema claro y oscuro                              |
| 6   | `feat: add content loader`               | Carga de módulos, Markdown, diagramas, test de validación                            |
| 7   | `feat: add exercise components`          | Quiz, completar código, predecir salida                                              |
| 8   | `feat: add home and progress views`      | Inicio, "Continuar donde quedaste", exportar e importar                              |
| 9   | `feat: add lab tooling`                  | `build-labs.py`, `check-labs.py`, `set-data-url.py`, `.venv`                         |
| 10  | `feat: add module 01 fundamentals`       | Teoría, diagramas, ejercicios, quiz y lab                                            |
| 11  | `feat: add cheatsheet`                   | Buscador con las funciones del módulo 1                                              |
| 12  | `docs: add README`                       | Cómo instalar, desarrollar, añadir un módulo y créditos                              |

Verificación antes de pedirte revisión:

- `npm run lint`, `npm test` y `npm run build` sin errores.
- `npm run labs:check`: la solución del lab 1 pasa y el lab sin resolver falla.
- Sitio revisado en el navegador: los dos temas, móvil, progreso que persiste
  al recargar, exportar e importar.

Lo que te pediré al terminar:

- Revisar el módulo 1: tono, nivel y cantidad de ejercicios. Lo que ajustes ahí
  se aplica a los otros 14.
- Abrir el lab 1 en Colab una vez. Para eso el repositorio tiene que estar ya en
  GitHub, o puedes subir el `.ipynb` a Colab a mano para la prueba.

## Fase 3 · Módulos 2 a 15

Un módulo por commit, en orden. Para cada uno:

1. Escribir el `source.py` del lab y ejecutarlo en local hasta que pase.
2. Copiar las salidas reales a los ejercicios de "predecir la salida".
3. Escribir teoría, diagramas, ejercicios y quiz.
4. Añadir sus funciones a la chuleta.
5. `npm test` y `npm run labs:check`.

Te aviso al terminar cada bloque (A a E), no cada módulo, para que puedas
revisar por tandas sin interrumpir el ritmo.

## Fase 4 · Publicación

Pasos que te daré detallados al final; el resumen:

1. Crear un repositorio **público** en GitHub y subir el código.
2. Rellenar `USUARIO/REPOSITORIO` en `src/config.js`.
3. Importar el repositorio en Vercel (detecta Vite solo).
4. Con la URL publicada, ejecutar `scripts/set-data-url.py <url>/data` y subir
   el cambio.
5. Abrir un lab desde el sitio publicado y comprobar el ciclo completo.

Crear el repositorio, la cuenta de Vercel y hacer `git push` lo haces tú; yo no
publico nada sin que me lo pidas.

## Cuándo un módulo está terminado

- [ ] Teoría escrita con palabras propias, con al menos un diagrama.
- [ ] Enlaces a los minutos del video (salvo módulos extra).
- [ ] Entre 5 y 8 ejercicios y un quiz de 5 a 8 preguntas, todos con explicación.
- [ ] Salidas de ejemplo copiadas de una ejecución real.
- [ ] `solution.ipynb` pasa todos los tests en local.
- [ ] `lab.ipynb` sin resolver falla en los tests.
- [ ] Contenido extra marcado como tal.
- [ ] Funciones del módulo añadidas a la chuleta.
- [ ] Lint, tests y build sin errores.

## Riesgos

| Riesgo                                   | Qué pasaría                      | Qué hago                                                                                               |
| ---------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Colab cambia de versión de Python o Java | La celda de instalación falla    | Versión de PySpark fijada; la celda comprueba Java; tú pruebas el lab 1 en Colab                       |
| `delta-spark` inestable en Colab         | No hay práctica de Delta         | Delta queda en teoría y quiz                                                                           |
| Las notas tienen errores que no detecté  | Contenido incorrecto             | Todo el código se ejecuta; las dudas quedan en [04](04-source-review.md); el notebook oficial ayudaría |
| El repositorio queda privado             | Los botones de Colab no abren    | Avisado; tiene que ser público                                                                         |
| La URL de Vercel cambia                  | Los notebooks no descargan datos | Un comando la actualiza en todos                                                                       |
| Licencia de BigMart                      | Poco probable para uso educativo | Origen citado; alternativa descrita en [03](03-labs.md#licencias)                                      |
| `localStorage` bloqueado o borrado       | El usuario pierde el progreso    | El sitio funciona igual; exportar a JSON como copia                                                    |

## Fuera de alcance

- Backend, cuentas de usuario o progreso sincronizado entre dispositivos.
- Ejecutar o emular Spark en el navegador.
- Corrección automática de los labs desde el sitio: el usuario marca el lab como
  hecho.
- Structured Streaming, MLlib y administración de clústeres.
