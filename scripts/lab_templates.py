"""Cells shared by every lab notebook.

build-labs.py expands directives such as `# %% [install]` into these cells, so
the install step, the test helper and the dataset download are written once.
Text shown to the learner is in Spanish; code is in English.
"""

COLAB_BADGE = "https://colab.research.google.com/assets/colab-badge.svg"
PLACEHOLDER_MARKER = "YOUR"


def is_configured(value):
    """True when a site.config.json value is no longer a placeholder."""
    return bool(value) and PLACEHOLDER_MARKER not in value


def colab_url(config, lab_dir, file_name):
    return (
        f"https://colab.research.google.com/github/{config['githubRepo']}"
        f"/blob/{config['githubBranch']}/labs/{lab_dir}/{file_name}"
    )


def data_base_urls(config):
    """Where notebooks download datasets from, in order of preference."""
    urls = []
    if is_configured(config.get("siteUrl")):
        urls.append(f"{config['siteUrl'].rstrip('/')}/data")
    if is_configured(config.get("githubRepo")):
        urls.append(
            f"https://raw.githubusercontent.com/{config['githubRepo']}"
            f"/{config['githubBranch']}/public/data"
        )
    return urls


def header_cell(meta, config, lab_dir, variant):
    """First markdown cell: title, Colab badge, goal and instructions."""
    number = lab_dir.split("-")[0]
    is_solution = variant == "solution"
    file_name = "solution.ipynb" if is_solution else "lab.ipynb"
    title = f"Lab {number} · {meta['title']}"
    lines = [f"# {'Solución · ' if is_solution else ''}{title}", ""]

    if is_configured(config.get("githubRepo")):
        lines += [f"[![Abrir en Colab]({COLAB_BADGE})]({colab_url(config, lab_dir, file_name)})", ""]

    lines += [f"**Objetivo:** {meta['objective']}", "", f"**Tiempo estimado:** {meta['minutes']} minutos", ""]

    if is_solution:
        lines += [
            "> Esta es la solución completa. Intenta resolver el laboratorio por tu cuenta antes",
            "> de leerla: equivocarse y corregir es donde más se aprende.",
            "",
        ]
    else:
        lines += [
            "## Antes de empezar",
            "",
            "1. Ve a **Archivo → Guardar una copia en Drive**. Así trabajas sobre tu copia y no pierdes nada.",
            "2. Ejecuta las celdas **en orden**, de arriba abajo (`Shift + Enter`).",
            "3. Donde veas `...` te toca escribir código. Las celdas de test te dicen si está bien:",
            "   ✅ es correcto y ❌ viene con una pista.",
            "4. Si te atascas, vuelve a la teoría del módulo antes de mirar la solución.",
            "",
        ]

    if is_configured(config.get("siteUrl")):
        lines.append(f"Módulo en el sitio: {config['siteUrl'].rstrip('/')}/#/modulo/{meta['id']}")
        lines.append("")

    return "\n".join(lines).rstrip()


INSTALL_MARKDOWN = """## Preparación

Esta celda instala la versión de PySpark con la que se probó el laboratorio y comprueba
que hay una versión de Java compatible. En Colab tarda alrededor de un minuto la primera vez."""


def install_cell(config):
    return f'''import importlib.metadata
import os
import re
import shutil
import subprocess
import sys

PYSPARK_VERSION = "{config["pysparkVersion"]}"
MIN_JAVA_VERSION = 17


def installed_pyspark_version():
    try:
        return importlib.metadata.version("pyspark")
    except importlib.metadata.PackageNotFoundError:
        return None


def java_major_version():
    java = shutil.which("java")
    if java is None:
        return 0
    output = subprocess.run([java, "-version"], capture_output=True, text=True).stderr
    match = re.search(r'version "(\\d+)', output)
    return int(match.group(1)) if match else 0


if installed_pyspark_version() != PYSPARK_VERSION:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", f"pyspark=={{PYSPARK_VERSION}}"],
        check=True,
    )

if java_major_version() < MIN_JAVA_VERSION:
    if "google.colab" not in sys.modules:
        raise RuntimeError("Spark 4 necesita Java 17 o superior. Instálalo y repite esta celda.")
    subprocess.run(["apt-get", "install", "-y", "-qq", "openjdk-17-jdk-headless"], check=True)
    os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-17-openjdk-amd64"
    os.environ["PATH"] = os.environ["JAVA_HOME"] + "/bin:" + os.environ["PATH"]

print(f"PySpark {{PYSPARK_VERSION}} y Java {{java_major_version()}} listos.")'''


HELPERS_MARKDOWN = """La siguiente celda define `check`, la función que usan los tests. No hace falta que la
modifiques: ejecútala y sigue."""

HELPERS_CELL = '''RESULTS = {}


def check(name, condition, hint):
    """Run one test: `condition` is a function that must return True."""
    try:
        passed = bool(condition())
        error = None
    except Exception as exc:  # A broken answer is a failed test, not a crash.
        passed, error = False, exc
    RESULTS[name] = passed
    if passed:
        print(f"✅ {name}")
        return
    detail = f" ({type(error).__name__}: {error})" if error else ""
    print(f"❌ {name}{detail}")
    print(f"   Pista: {hint}")
    assert passed, f"{name} · {hint}"'''


def data_markdown(datasets):
    names = ", ".join(f"`{name}`" for name in datasets)
    return f"""## Datos

Esta celda descarga {names} la primera vez y los deja en la carpeta `data/`.
Usa `dataset_path("nombre")` para obtener la ruta de un archivo."""


def data_cell(config, datasets):
    urls = ",\n    ".join(f'"{url}"' for url in data_base_urls(config))
    names = ", ".join(f'"{name}"' for name in datasets)
    return f'''import os
import urllib.request

DATA_BASE_URLS = [
    {urls},
]
DATA_DIR = os.environ.get("PYSPARK_LABS_DATA_DIR", "data")
DATASETS = [{names}]


def dataset_path(name):
    """Return the local path of a dataset, downloading it the first time."""
    path = os.path.join(DATA_DIR, name)
    if os.path.exists(path):
        return path
    os.makedirs(DATA_DIR, exist_ok=True)
    for base_url in DATA_BASE_URLS:
        try:
            urllib.request.urlretrieve(f"{{base_url}}/{{name}}", path)
            return path
        except OSError:
            continue  # Try the next mirror.
    raise RuntimeError(f"No se pudo descargar {{name}}. Revisa tu conexión y repite la celda.")


for dataset in DATASETS:
    print("Listo:", dataset_path(dataset))'''


SUMMARY_MARKDOWN = """## Resumen

Ejecuta esta celda al final. Si todos los tests pasan, vuelve al sitio y marca el
laboratorio como completado."""


def summary_cell(expected_tests):
    return f'''EXPECTED_TESTS = {expected_tests}
passed_tests = sum(RESULTS.values())

print(f"{{passed_tests}} de {{EXPECTED_TESTS}} tests superados")
for test_name, passed in RESULTS.items():
    print("  ✅" if passed else "  ❌", test_name)

assert passed_tests == EXPECTED_TESTS, "Todavía quedan tareas por resolver."
print("\\n🎉 ¡Laboratorio completado! Vuelve al sitio y márcalo como hecho.")'''
