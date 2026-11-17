import { h } from '../utils/dom.js';
import { codeBlockHtml } from '../services/markdown.js';
import { checkChoice, checkTextAnswer, isMultiChoice } from '../services/checkers.js';
import { createChoiceList } from './choice-list.js';

/**
 * Show a piece of code and ask what it produces.
 * Either pick one of several outputs, or type a short answer.
 */
export function createPredictOutput(exercise) {
  const code = h('div', { html: codeBlockHtml(exercise.code, exercise.language ?? 'python') });

  if (exercise.options) {
    const list = createChoiceList({
      options: exercise.options,
      multi: isMultiChoice(exercise),
      format: exercise.optionsFormat ?? 'text',
      legend: 'Posibles salidas',
    });
    const correctIndexes = [exercise.answer].flat();
    return {
      element: h('div', { class: 'predict-output' }, code, list.element),
      isAnswered: () => list.getSelected().length > 0,
      emptyMessage: 'Elige una opción antes de comprobar.',
      check() {
        const correct = checkChoice(list.getSelected(), exercise.answer);
        list.mark(correctIndexes);
        return correct;
      },
      reveal: () => list.mark(correctIndexes, { revealAnswer: true }),
      setDisabled: list.setDisabled,
    };
  }

  const input = h('input', {
    type: 'text',
    class: 'text-answer__input',
    autocomplete: 'off',
    inputmode: exercise.inputMode ?? 'text',
    'aria-label': exercise.inputLabel ?? 'Tu respuesta',
  });
  const field = h(
    'label',
    { class: 'text-answer' },
    h('span', { class: 'text-answer__label' }, exercise.inputLabel ?? 'Tu respuesta'),
    input,
  );

  return {
    element: h('div', { class: 'predict-output' }, code, field),
    isAnswered: () => input.value.trim() !== '',
    emptyMessage: 'Escribe tu respuesta antes de comprobar.',
    check() {
      const correct = checkTextAnswer(input.value, exercise.answers);
      input.classList.toggle('text-answer__input--right', correct);
      input.classList.toggle('text-answer__input--wrong', !correct);
      return correct;
    },
    reveal() {
      input.value = exercise.answers[0];
      input.classList.remove('text-answer__input--wrong');
      input.classList.add('text-answer__input--right');
    },
    setDisabled(disabled) {
      input.readOnly = disabled;
    },
  };
}

/** Plain multiple-choice exercise (no code to read). */
export function createChoiceExercise(exercise) {
  const list = createChoiceList({
    options: exercise.options,
    multi: isMultiChoice(exercise),
    format: exercise.optionsFormat ?? 'text',
  });
  const correctIndexes = [exercise.answer].flat();
  return {
    element: list.element,
    isAnswered: () => list.getSelected().length > 0,
    emptyMessage: 'Elige una opción antes de comprobar.',
    check() {
      const correct = checkChoice(list.getSelected(), exercise.answer);
      list.mark(correctIndexes);
      return correct;
    },
    reveal: () => list.mark(correctIndexes, { revealAnswer: true }),
    setDisabled: list.setDisabled,
  };
}
