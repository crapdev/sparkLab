import { h, replaceChildren } from '../utils/dom.js';
import { getModuleIds, getModules, isPublished } from '../services/content.js';
import { getModuleStatus, getOverallStatus } from '../services/progress.js';
import {
  exportProgress,
  getProgress,
  importProgress,
  isStorageAvailable,
  resetProgress,
} from '../services/storage.js';
import { applyTheme } from '../components/theme-toggle.js';
import { createProgressBar } from '../components/progress-bar.js';

const IMPORT_ERRORS = {
  'invalid-json': 'El archivo no es un JSON válido.',
  'not-an-export': 'El archivo no es una exportación de PySpark Labs.',
  'unsupported-version': 'El archivo es de una versión que este sitio no sabe leer.',
  'invalid-progress': 'El archivo no contiene un progreso válido.',
};

function downloadJson(content, fileName) {
  const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }));
  const link = h('a', { href: url, download: fileName });
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function progressTable() {
  const progress = getProgress();
  const rows = getModules()
    .filter(isPublished)
    .map((module) => {
      const { parts, percent, completed } = getModuleStatus(module, progress);
      return h(
        'tr',
        {},
        h(
          'th',
          { scope: 'row' },
          h('a', { href: `#/modulo/${module.id}` }, `${module.order}. ${module.title}`),
        ),
        h('td', {}, parts.theory.done ? 'Leída' : '—'),
        h(
          'td',
          {},
          parts.exercises.applies ? `${parts.exercises.solved}/${parts.exercises.total}` : '—',
        ),
        h(
          'td',
          {},
          parts.quiz.bestScore === null ? '—' : `${parts.quiz.bestScore}/${parts.quiz.total}`,
        ),
        h('td', {}, parts.lab.done ? 'Hecho' : '—'),
        h('td', {}, completed ? 'Completado' : `${percent} %`),
      );
    });

  return h(
    'div',
    { class: 'table-wrap' },
    h(
      'table',
      { class: 'progress-table' },
      h(
        'thead',
        {},
        h(
          'tr',
          {},
          ['Módulo', 'Teoría', 'Ejercicios', 'Quiz', 'Lab', 'Estado'].map((title) =>
            h('th', { scope: 'col' }, title),
          ),
        ),
      ),
      h('tbody', {}, rows),
    ),
  );
}

export function progressView() {
  const summary = h('div', {});
  const message = h('div', { 'aria-live': 'polite' });

  function showMessage(kind, text) {
    replaceChildren(
      message,
      h('div', { class: `feedback feedback--${kind}` }, h('p', { class: 'feedback__title' }, text)),
    );
  }

  function render() {
    const overall = getOverallStatus();
    replaceChildren(
      summary,
      h(
        'p',
        { class: 'page__lead' },
        `${overall.completed} de ${overall.total} módulos completados · ${overall.percent} % del contenido publicado.`,
      ),
      createProgressBar(overall.percent, 'Progreso global'),
      progressTable(),
    );
  }

  const fileInput = h('input', { type: 'file', accept: 'application/json,.json', hidden: true });
  fileInput.addEventListener('change', async () => {
    const [file] = fileInput.files;
    if (!file) return;
    const result = importProgress(await file.text(), { knownModuleIds: getModuleIds() });
    fileInput.value = '';
    if (!result.ok) {
      showMessage('wrong', IMPORT_ERRORS[result.error] ?? 'No se pudo importar el archivo.');
      return;
    }
    applyTheme();
    render();
    const skipped = result.skipped.length
      ? ` Se ignoraron ${result.skipped.length} módulos que ya no existen.`
      : '';
    showMessage('right', `Progreso importado: ${result.modules} módulos.${skipped}`);
  });

  const exportButton = h(
    'button',
    { type: 'button', class: 'btn btn--primary' },
    'Exportar progreso',
  );
  exportButton.addEventListener('click', () => {
    const date = new Date().toISOString().slice(0, 10);
    downloadJson(exportProgress(), `pyspark-labs-progreso-${date}.json`);
    showMessage('right', 'Archivo descargado. Guárdalo como copia de seguridad.');
  });

  const importButton = h(
    'button',
    { type: 'button', class: 'btn btn--ghost' },
    'Importar progreso',
  );
  importButton.addEventListener('click', () => {
    const replace = globalThis.confirm(
      'Importar reemplaza tu progreso actual por el del archivo. ¿Continuar?',
    );
    if (replace) fileInput.click();
  });

  const resetButton = h(
    'button',
    { type: 'button', class: 'btn btn--danger' },
    'Borrar mi progreso',
  );
  resetButton.addEventListener('click', () => {
    const confirmed = globalThis.confirm(
      'Se borrará todo tu progreso en este navegador. No se puede deshacer. ¿Continuar?',
    );
    if (!confirmed) return;
    resetProgress();
    render();
    showMessage('info', 'Progreso borrado.');
  });

  render();

  return h(
    'div',
    { class: 'page' },
    h('h1', {}, 'Tu progreso'),
    !isStorageAvailable() &&
      h(
        'div',
        { class: 'feedback feedback--wrong' },
        h('p', { class: 'feedback__title' }, 'Tu navegador no deja guardar datos'),
        h(
          'p',
          { class: 'feedback__text' },
          'El progreso solo durará mientras tengas esta pestaña abierta. Suele pasar en modo privado. Exporta tu progreso antes de cerrar.',
        ),
      ),
    summary,
    h('h2', {}, 'Copia de seguridad'),
    h(
      'p',
      {},
      'El progreso se guarda solo en este navegador, sin cuenta ni servidor. Para llevarlo a otro dispositivo o no perderlo, expórtalo a un archivo e impórtalo donde quieras.',
    ),
    h('div', { class: 'page__actions' }, exportButton, importButton, resetButton, fileInput),
    message,
  );
}
