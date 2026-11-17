import { h } from '../utils/dom.js';

export function notFoundView() {
  return h(
    'div',
    { class: 'page' },
    h('h1', {}, 'Página no encontrada'),
    h('p', {}, 'Esa dirección no existe o el módulo todavía no está publicado.'),
    h('a', { class: 'btn btn--primary', href: '#/' }, 'Volver al inicio'),
  );
}
