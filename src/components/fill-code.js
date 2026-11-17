import { h } from '../utils/dom.js';
import { highlight } from '../services/markdown.js';
import { checkBlanks } from '../services/checkers.js';
import { BLANK_TOKEN } from '../services/content-schema.js';

/**
 * Code fragment with blanks the user fills in.
 * Answers are compared with the accepted values; nothing is executed.
 */
export function createFillCode(exercise) {
  const language = exercise.language ?? 'python';
  const segments = exercise.code.split(BLANK_TOKEN);

  const inputs = exercise.blanks.map((blank, index) => {
    const longest = Math.max(...blank.answers.map((answer) => answer.length));
    return h('input', {
      type: 'text',
      class: 'blank',
      size: Math.max(longest + 1, 4),
      autocomplete: 'off',
      autocapitalize: 'off',
      spellcheck: 'false',
      'aria-label': `Hueco ${index + 1}`,
    });
  });

  const code = h('code', { class: 'hljs' });
  segments.forEach((segment, index) => {
    code.append(h('span', { html: highlight(segment, language) }));
    if (index < inputs.length) code.append(inputs[index]);
  });

  const hints = h('ul', { class: 'fill-code__hints' });
  const element = h(
    'div',
    { class: 'fill-code' },
    h('pre', { class: 'fill-code__code' }, code),
    hints,
  );

  function showResults(results) {
    hints.replaceChildren();
    results.forEach((correct, index) => {
      inputs[index].classList.toggle('blank--right', correct);
      inputs[index].classList.toggle('blank--wrong', !correct);
      const hint = exercise.blanks[index].hint;
      if (!correct && hint) hints.append(h('li', {}, `Hueco ${index + 1}: ${hint}`));
    });
  }

  return {
    element,
    isAnswered: () => inputs.every((input) => input.value.trim() !== ''),
    emptyMessage: 'Rellena todos los huecos antes de comprobar.',
    check() {
      const results = checkBlanks(
        inputs.map((input) => input.value),
        exercise.blanks,
      );
      showResults(results);
      return results.every(Boolean);
    },
    reveal() {
      inputs.forEach((input, index) => {
        input.value = exercise.blanks[index].answers[0];
      });
      showResults(inputs.map(() => true));
    },
    setDisabled(disabled) {
      inputs.forEach((input) => {
        input.readOnly = disabled;
      });
    },
  };
}
