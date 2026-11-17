import { h } from '../utils/dom.js';
import { renderInline } from '../services/markdown.js';
import { createFillCode } from './fill-code.js';
import { createChoiceExercise, createPredictOutput } from './predict-output.js';

const TYPES = {
  choice: { label: 'Elige la respuesta', create: createChoiceExercise },
  'predict-output': { label: 'Predice la salida', create: createPredictOutput },
  'fill-code': { label: 'Completa el código', create: createFillCode },
};

/** Failed attempts after which the user may reveal the answer. */
const ATTEMPTS_BEFORE_REVEAL = 2;

/**
 * Card that wraps one exercise: prompt, interactive body, feedback.
 *
 * @param {object} exercise - exercise definition from module.json
 * @param {{ number: number, solved: boolean, onResult: (correct: boolean) => void }} options
 */
export function createExerciseCard(exercise, { number, solved, onResult }) {
  const type = TYPES[exercise.type];
  const body = type.create(exercise);
  let failures = 0;

  const status = h('span', { class: 'exercise__status' }, solved ? 'Resuelto' : '');
  const feedback = h('div', { class: 'exercise__feedback', 'aria-live': 'polite' });
  const checkButton = h('button', { type: 'button', class: 'btn btn--primary' }, 'Comprobar');
  const revealButton = h(
    'button',
    { type: 'button', class: 'btn btn--ghost', hidden: true },
    'Ver la respuesta',
  );

  const card = h(
    'article',
    { class: `exercise${solved ? ' exercise--solved' : ''}`, id: `ejercicio-${exercise.id}` },
    h(
      'header',
      { class: 'exercise__header' },
      h('span', { class: 'exercise__number' }, `Ejercicio ${number}`),
      h('span', { class: 'exercise__type' }, type.label),
      status,
    ),
    h('p', { class: 'exercise__prompt', html: renderInline(exercise.prompt) }),
    body.element,
    h('div', { class: 'exercise__actions' }, checkButton, revealButton),
    feedback,
  );

  function showFeedback(kind, title, withExplanation) {
    feedback.replaceChildren(
      h(
        'div',
        { class: `feedback feedback--${kind}` },
        h('p', { class: 'feedback__title' }, title),
        withExplanation &&
          h('p', { class: 'feedback__text', html: renderInline(exercise.explanation) }),
      ),
    );
  }

  checkButton.addEventListener('click', () => {
    if (!body.isAnswered()) {
      showFeedback('info', body.emptyMessage, false);
      return;
    }
    const correct = body.check();
    onResult(correct);

    if (correct) {
      card.classList.add('exercise--solved');
      status.textContent = 'Resuelto';
      revealButton.hidden = true;
      showFeedback('right', '¡Correcto!', true);
      return;
    }
    failures += 1;
    revealButton.hidden = failures < ATTEMPTS_BEFORE_REVEAL;
    const hint = exercise.hint ? ` Pista: ${exercise.hint}` : '';
    showFeedback('wrong', `Todavía no. Vuelve a intentarlo.${hint}`, false);
  });

  revealButton.addEventListener('click', () => {
    body.reveal();
    revealButton.hidden = true;
    showFeedback('info', 'Esta es la respuesta:', true);
  });

  return card;
}
