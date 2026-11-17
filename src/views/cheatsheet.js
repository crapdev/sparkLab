import { h, replaceChildren } from '../utils/dom.js';
import { getCheatsheet, getModule, isPublished } from '../services/content.js';
import { codeBlockHtml, renderInline } from '../services/markdown.js';
import { normalizeText } from '../services/checkers.js';

const ALL = 'Todas';

// T = transformación (perezosa, devuelve un DataFrame); A = acción (ejecuta el plan).
const KIND_LABEL = { transformación: 'T', acción: 'A' };
const KIND_CLASS = { transformación: 'transformation', acción: 'action' };

function matches(entry, query) {
  if (!query) return true;
  const haystack = normalizeText(
    [
      entry.name,
      entry.signature,
      entry.description,
      entry.category,
      entry.kind ?? '',
      ...(entry.keywords ?? []),
    ].join(' '),
  );
  return query.split(' ').every((word) => haystack.includes(word));
}

function entryCard(entry) {
  const module = getModule(entry.module);
  return h(
    'li',
    { class: 'sheet-entry' },
    h(
      'header',
      { class: 'sheet-entry__header' },
      h('h2', { class: 'sheet-entry__name' }, entry.name),
      h(
        'span',
        { class: 'sheet-entry__badges' },
        entry.kind &&
          h(
            'span',
            { class: `badge badge--${KIND_CLASS[entry.kind]}`, title: entry.kind },
            KIND_LABEL[entry.kind],
          ),
        h('span', { class: 'badge' }, entry.category),
      ),
    ),
    h('code', { class: 'sheet-entry__signature' }, entry.signature),
    h('p', { class: 'sheet-entry__description', html: renderInline(entry.description) }),
    h('div', { html: codeBlockHtml(entry.example, 'python') }),
    entry.gotcha &&
      h('p', {
        class: 'sheet-entry__gotcha',
        html: `<strong>Ojo:</strong> ${renderInline(entry.gotcha)}`,
      }),
    module &&
      isPublished(module) &&
      h(
        'a',
        { class: 'sheet-entry__module', href: `#/modulo/${module.id}` },
        `Módulo ${module.order} · ${module.title}`,
      ),
  );
}

export function cheatsheetView() {
  const entries = [...getCheatsheet()].sort((a, b) => a.name.localeCompare(b.name));
  const categories = [ALL, ...new Set(entries.map((entry) => entry.category))];
  let category = ALL;

  const search = h('input', {
    type: 'search',
    class: 'sheet__search',
    placeholder: 'Busca una función: filter, duplicados, contar…',
    'aria-label': 'Buscar en la chuleta',
    autocomplete: 'off',
  });
  const filters = h('div', { class: 'sheet__filters', role: 'group', 'aria-label': 'Categorías' });
  const count = h('p', { class: 'sheet__count', 'aria-live': 'polite' });
  const list = h('ul', { class: 'sheet__list' });

  function render() {
    const query = normalizeText(search.value);
    const visible = entries.filter(
      (entry) => (category === ALL || entry.category === category) && matches(entry, query),
    );
    count.textContent = visible.length === 1 ? '1 función' : `${visible.length} funciones`;
    replaceChildren(
      list,
      visible.length
        ? visible.map(entryCard)
        : h('li', { class: 'sheet__empty' }, 'Nada coincide. Prueba con otra palabra o en inglés.'),
    );
    replaceChildren(
      filters,
      categories.map((name) => {
        const button = h(
          'button',
          {
            type: 'button',
            class: `chip chip--button${name === category ? ' is-active' : ''}`,
            'aria-pressed': String(name === category),
          },
          name,
        );
        button.addEventListener('click', () => {
          category = name;
          render();
        });
        return button;
      }),
    );
  }

  search.addEventListener('input', render);
  render();

  return h(
    'div',
    { class: 'page sheet' },
    h('h1', {}, 'Chuleta de PySpark'),
    h(
      'p',
      { class: 'page__lead' },
      'Referencia rápida de las funciones que aparecen en los módulos. Crece con cada módulo nuevo. ',
      h('strong', {}, 'T'),
      ' marca una transformación, que solo añade pasos al plan, y ',
      h('strong', {}, 'A'),
      ' una acción, que pone a Spark a ejecutar. Las expresiones de columna, como F.col o when, no llevan etiqueta: se usan dentro de una transformación.',
    ),
    search,
    filters,
    count,
    list,
  );
}
