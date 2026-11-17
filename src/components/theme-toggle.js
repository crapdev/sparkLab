import { h } from '../utils/dom.js';
import { getTheme, setTheme } from '../services/storage.js';

const prefersDark = () => globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;

/** Theme actually shown, resolving "system" to light or dark. */
function effectiveTheme() {
  const theme = getTheme();
  if (theme !== 'system') return theme;
  return prefersDark() ? 'dark' : 'light';
}

/** Apply the saved theme to the document. "system" removes the override. */
export function applyTheme() {
  const theme = getTheme();
  if (theme === 'system') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = theme;
}

/** Button that switches between light and dark and remembers the choice. */
export function createThemeToggle() {
  const button = h('button', { type: 'button', class: 'theme-toggle' });

  function render() {
    const dark = effectiveTheme() === 'dark';
    button.textContent = dark ? '☀' : '☾';
    button.setAttribute('aria-label', dark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro');
    button.title = button.getAttribute('aria-label');
  }

  button.addEventListener('click', () => {
    setTheme(effectiveTheme() === 'dark' ? 'light' : 'dark');
    applyTheme();
    render();
  });

  render();
  return button;
}
