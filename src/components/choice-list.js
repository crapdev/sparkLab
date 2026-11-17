import { h } from '../utils/dom.js';
import { renderInline, escapeHtml } from '../services/markdown.js';

let groupCounter = 0;

/**
 * List of radio buttons or checkboxes.
 *
 * @param {{ options: string[], multi?: boolean, format?: 'text' | 'code', legend?: string }} config
 * @returns {{ element: HTMLElement, getSelected: () => number[], setDisabled: Function,
 *             mark: Function, reset: Function }}
 */
export function createChoiceList({ options, multi = false, format = 'text', legend }) {
  const name = `choice-${(groupCounter += 1)}`;

  const items = options.map((option, index) => {
    const input = h('input', {
      type: multi ? 'checkbox' : 'radio',
      name,
      value: index,
      class: 'choice__input',
    });
    const content =
      format === 'code'
        ? h('pre', { class: 'choice__code', html: `<code>${escapeHtml(option)}</code>` })
        : h('span', { class: 'choice__text', html: renderInline(option) });
    const label = h('label', { class: 'choice' }, input, content);
    return { input, label };
  });

  const element = h(
    'fieldset',
    { class: 'choice-list' },
    h('legend', { class: 'visually-hidden' }, legend ?? 'Opciones'),
    multi && h('p', { class: 'choice-list__note' }, 'Puede haber varias respuestas correctas.'),
    items.map((item) => item.label),
  );

  return {
    element,
    getSelected: () => items.flatMap((item, index) => (item.input.checked ? [index] : [])),
    setDisabled(disabled) {
      items.forEach((item) => {
        item.input.disabled = disabled;
      });
    },
    /** Highlight the selected options as right or wrong, and optionally the answer. */
    mark(correctIndexes, { revealAnswer = false } = {}) {
      items.forEach((item, index) => {
        const isCorrect = correctIndexes.includes(index);
        item.label.classList.toggle('choice--right', item.input.checked && isCorrect);
        item.label.classList.toggle('choice--wrong', item.input.checked && !isCorrect);
        item.label.classList.toggle('choice--answer', revealAnswer && isCorrect);
      });
    },
    reset() {
      items.forEach((item) => {
        item.input.checked = false;
        item.input.disabled = false;
        item.label.classList.remove('choice--right', 'choice--wrong', 'choice--answer');
      });
    },
  };
}
