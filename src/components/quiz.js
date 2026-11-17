import { h } from '../utils/dom.js';
import { renderInline } from '../services/markdown.js';
import { isMultiChoice, scoreQuiz } from '../services/checkers.js';
import { createChoiceList } from './choice-list.js';

/**
 * Quiz: every question is answered first, then the whole quiz is graded.
 *
 * @param {object[]} questions - quiz questions from module.json
 * @param {{ passRatio: number, best: { bestScore: number, total: number } | null,
 *           onSubmit: (score: number, total: number) => void }} options
 */
export function createQuiz(questions, { passRatio, best, onSubmit }) {
  const passScore = Math.ceil(questions.length * passRatio);

  const items = questions.map((question, index) => {
    const list = createChoiceList({
      options: question.options,
      multi: isMultiChoice(question),
      legend: `Pregunta ${index + 1}`,
    });
    const explanation = h('div', { class: 'quiz__explanation', hidden: true });
    const element = h(
      'article',
      { class: 'quiz__question' },
      h(
        'h3',
        { class: 'quiz__title' },
        h('span', { class: 'quiz__index' }, `${index + 1}.`),
        h('span', { html: renderInline(question.question) }),
      ),
      list.element,
      explanation,
    );
    return { question, list, explanation, element };
  });

  const bestNote = h('p', { class: 'quiz__best' });
  const result = h('div', { class: 'quiz__result', 'aria-live': 'polite', tabindex: '-1' });
  const submitButton = h('button', { type: 'button', class: 'btn btn--primary' }, 'Corregir quiz');
  const retryButton = h(
    'button',
    { type: 'button', class: 'btn btn--ghost', hidden: true },
    'Volver a intentarlo',
  );

  function showBest(record) {
    bestNote.textContent =
      record && record.total === questions.length
        ? `Tu mejor nota: ${record.bestScore} de ${record.total}. Se aprueba con ${passScore}.`
        : `${questions.length} preguntas. Se aprueba con ${passScore} aciertos.`;
  }
  showBest(best);

  submitButton.addEventListener('click', () => {
    const responses = Object.fromEntries(
      items.map((item) => [item.question.id, item.list.getSelected()]),
    );
    const unanswered = items.filter((item) => responses[item.question.id].length === 0).length;
    if (unanswered > 0) {
      result.replaceChildren(
        h(
          'div',
          { class: 'feedback feedback--info' },
          h('p', { class: 'feedback__title' }, `Te faltan ${unanswered} preguntas por responder.`),
        ),
      );
      return;
    }

    const { score, total, results } = scoreQuiz(questions, responses);
    items.forEach((item, index) => {
      const correctIndexes = [item.question.answer].flat();
      item.list.mark(correctIndexes, { revealAnswer: true });
      item.list.setDisabled(true);
      item.element.classList.toggle('quiz__question--right', results[index].correct);
      item.element.classList.toggle('quiz__question--wrong', !results[index].correct);
      item.explanation.hidden = false;
      item.explanation.replaceChildren(
        h('p', { class: 'feedback__title' }, results[index].correct ? 'Correcto' : 'Incorrecto'),
        h('p', { html: renderInline(item.question.explanation) }),
      );
    });

    const passed = score >= passScore;
    result.replaceChildren(
      h(
        'div',
        { class: `feedback feedback--${passed ? 'right' : 'wrong'}` },
        h('p', { class: 'feedback__title' }, `Resultado: ${score} de ${total}`),
        h(
          'p',
          { class: 'feedback__text' },
          passed
            ? '¡Quiz aprobado! Revisa las explicaciones y pasa al laboratorio.'
            : `Necesitas ${passScore} aciertos. Repasa las explicaciones y vuelve a intentarlo.`,
        ),
      ),
    );
    submitButton.hidden = true;
    retryButton.hidden = false;
    const updatedBest = onSubmit(score, total);
    showBest(updatedBest);
    result.focus();
  });

  retryButton.addEventListener('click', () => {
    items.forEach((item) => {
      item.list.reset();
      item.explanation.hidden = true;
      item.element.classList.remove('quiz__question--right', 'quiz__question--wrong');
    });
    result.replaceChildren();
    submitButton.hidden = false;
    retryButton.hidden = true;
    items[0].element.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  return h(
    'section',
    { class: 'quiz' },
    bestNote,
    items.map((item) => item.element),
    h('div', { class: 'quiz__actions' }, submitButton, retryButton),
    result,
  );
}
