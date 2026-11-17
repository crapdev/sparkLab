import { h } from '../utils/dom.js';

/** Accessible progress bar. `percent` goes from 0 to 100. */
export function createProgressBar(percent, label = 'Progreso') {
  const value = Math.max(0, Math.min(100, Math.round(percent)));
  const fill = h('div', { class: 'progress__fill' });
  fill.style.width = `${value}%`;
  return h(
    'div',
    {
      class: `progress${value === 100 ? ' progress--full' : ''}`,
      role: 'progressbar',
      'aria-label': label,
      'aria-valuemin': 0,
      'aria-valuemax': 100,
      'aria-valuenow': value,
    },
    fill,
  );
}
