import { h } from '../utils/dom.js';
import { renderInline } from '../services/markdown.js';
import { SITE, colabUrl, githubUrl, isRepoConfigured } from '../config.js';
import { formatMinutes } from '../utils/dom.js';

/**
 * Lab panel: what the lab covers, the Colab button and the "done" checkbox.
 *
 * @param {object} lab - "lab" section of module.json
 * @param {{ done: boolean, onToggleDone: (done: boolean) => void }} options
 */
export function createLabCard(lab, { done, onToggleDone }) {
  const checkbox = h('input', { type: 'checkbox', class: 'lab__checkbox' });
  checkbox.checked = done;
  checkbox.addEventListener('change', () => onToggleDone(checkbox.checked));

  const openButton = isRepoConfigured
    ? h(
        'a',
        {
          class: 'btn btn--primary btn--large',
          href: colabUrl(lab.path),
          target: '_blank',
          rel: 'noopener noreferrer',
        },
        'Abrir en Google Colab',
      )
    : h('span', { class: 'btn btn--primary btn--large btn--disabled' }, 'Abrir en Google Colab');

  return h(
    'section',
    { class: 'lab' },
    h('p', { class: 'lab__summary', html: renderInline(lab.summary) }),
    h(
      'dl',
      { class: 'lab__facts' },
      h('div', {}, h('dt', {}, 'Duración'), h('dd', {}, formatMinutes(lab.minutes))),
      h('div', {}, h('dt', {}, 'PySpark'), h('dd', {}, SITE.pysparkVersion)),
      h(
        'div',
        {},
        h('dt', {}, 'Datos'),
        h('dd', {}, lab.datasets?.length ? lab.datasets.join(', ') : 'Se generan en el notebook'),
      ),
    ),
    h('h3', {}, 'Qué vas a hacer'),
    h(
      'ol',
      { class: 'lab__tasks' },
      lab.tasks.map((task) => h('li', { html: renderInline(task) })),
    ),
    h('h3', {}, 'Cómo funciona'),
    h(
      'ol',
      { class: 'lab__steps' },
      h('li', {}, 'Abre el notebook en Google Colab con el botón de abajo.'),
      h('li', {
        html: 'En Colab, elige <strong>Archivo → Guardar una copia en Drive</strong> para no perder tu trabajo.',
      }),
      h(
        'li',
        {},
        'Ejecuta las celdas en orden. Cada tarea trae sus tests: verás ✅ o ❌ con una pista.',
      ),
      h(
        'li',
        {},
        'Cuando todos los tests pasen, vuelve aquí y marca el laboratorio como completado.',
      ),
    ),
    h(
      'div',
      { class: 'lab__actions' },
      openButton,
      isRepoConfigured &&
        h(
          'a',
          {
            class: 'btn btn--ghost',
            href: colabUrl(lab.path, 'solution.ipynb'),
            target: '_blank',
            rel: 'noopener noreferrer',
          },
          'Ver la solución',
        ),
      isRepoConfigured &&
        h(
          'a',
          {
            class: 'btn btn--ghost',
            href: githubUrl(`${lab.path}/lab.ipynb`),
            target: '_blank',
            rel: 'noopener noreferrer',
          },
          'Ver en GitHub',
        ),
    ),
    !isRepoConfigured &&
      h(
        'p',
        { class: 'lab__note' },
        'El botón se activará cuando el repositorio esté publicado en GitHub.',
      ),
    h(
      'p',
      { class: 'lab__note' },
      'Intenta resolverlo antes de mirar la solución: equivocarse es parte de aprender.',
    ),
    h(
      'label',
      { class: 'lab__done' },
      checkbox,
      h('span', {}, 'He terminado el laboratorio y todos los tests pasan'),
    ),
  );
}
