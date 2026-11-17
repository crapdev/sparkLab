import './styles/tokens.css';
import './styles/base.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/content.css';

import { h, replaceChildren } from './utils/dom.js';
import { SITE } from './config.js';
import { createRouter } from './router.js';
import { getOverallStatus } from './services/progress.js';
import { onProgressChange } from './services/storage.js';
import { applyTheme, createThemeToggle } from './components/theme-toggle.js';
import { homeView } from './views/home.js';
import { moduleView } from './views/module.js';
import { cheatsheetView } from './views/cheatsheet.js';
import { progressView } from './views/progress.js';
import { aboutView } from './views/about.js';
import { notFoundView } from './views/not-found.js';

const NAV_LINKS = [
  { href: '#/', label: 'Módulos', match: (path) => path === '/' || path.startsWith('/modulo') },
  { href: '#/chuleta', label: 'Chuleta', match: (path) => path.startsWith('/chuleta') },
  { href: '#/progreso', label: 'Progreso', match: (path) => path.startsWith('/progreso') },
  { href: '#/acerca', label: 'Acerca', match: (path) => path.startsWith('/acerca') },
];

const ROUTES = [
  { pattern: '/', view: homeView },
  { pattern: '/modulo/:id/:tab?', view: moduleView },
  { pattern: '/chuleta', view: cheatsheetView },
  { pattern: '/progreso', view: progressView },
  { pattern: '/acerca', view: aboutView },
];

applyTheme();

const navLinks = NAV_LINKS.map((link) => ({
  ...link,
  element: h('a', { class: 'nav__link', href: link.href }, link.label),
}));
const headerProgress = h('a', { class: 'header__progress', href: '#/progreso' });
const outlet = h('main', { id: 'contenido', class: 'container', tabindex: '-1' });

function renderHeaderProgress() {
  const { completed, total } = getOverallStatus();
  headerProgress.textContent = `${completed}/${total}`;
  headerProgress.title = `${completed} de ${total} módulos completados`;
  headerProgress.setAttribute('aria-label', headerProgress.title);
}

const shell = [
  h(
    'header',
    { class: 'header' },
    h(
      'div',
      { class: 'header__inner container' },
      h(
        'a',
        { class: 'brand', href: '#/' },
        h('span', { class: 'brand__mark', 'aria-hidden': 'true' }, '✦'),
        SITE.siteName,
      ),
      h(
        'nav',
        { class: 'nav', 'aria-label': 'Principal' },
        navLinks.map((link) => link.element),
      ),
      h('div', { class: 'header__tools' }, headerProgress, createThemeToggle()),
    ),
  ),
  outlet,
  h(
    'footer',
    { class: 'footer' },
    h(
      'div',
      { class: 'container footer__inner' },
      h(
        'p',
        {},
        `${SITE.siteName} · Teoría, ejercicios y laboratorios para practicar PySpark. `,
        h('a', { href: '#/acerca' }, 'Cómo funciona'),
      ),
    ),
  ),
];

document.getElementById('app').append(...shell);

let renderToken = 0;

const router = createRouter(ROUTES, {
  notFound: notFoundView,
  async onRoute({ view, params, path }) {
    const token = (renderToken += 1);
    navLinks.forEach((link) => {
      const active = link.match(path);
      link.element.classList.toggle('is-active', active);
      if (active) link.element.setAttribute('aria-current', 'page');
      else link.element.removeAttribute('aria-current');
    });

    const content = await view(params);
    if (token !== renderToken) return; // A newer navigation won the race.

    const previousPath = outlet.dataset.path;
    replaceChildren(outlet, content);
    outlet.dataset.path = path;
    renderHeaderProgress();

    // Switching tabs inside a module keeps the module header out of the way:
    // the page only moves if the tab bar was scrolled out of view.
    const sameModule =
      previousPath &&
      path.startsWith('/modulo/') &&
      previousPath.split('/')[2] === path.split('/')[2];
    const tabs = content.querySelector('.tabs');
    if (!sameModule || !tabs) globalThis.scrollTo(0, 0);
    else if (tabs.getBoundingClientRect().top < 0) tabs.scrollIntoView({ block: 'start' });
    document.title = content.querySelector('h1')
      ? `${content.querySelector('h1').firstChild.textContent} · ${SITE.siteName}`
      : SITE.siteName;
  },
});

onProgressChange(renderHeaderProgress);

// Copy buttons of every code block, handled in one place.
document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-copy]');
  if (!button) return;
  const code = button.parentElement.querySelector('code')?.textContent ?? '';
  try {
    await navigator.clipboard.writeText(code);
    button.textContent = 'Copiado';
  } catch {
    button.textContent = 'No se pudo copiar';
  }
  setTimeout(() => {
    button.textContent = 'Copiar';
  }, 1500);
});

router.start();
