/**
 * Pure functions that decide whether an answer is right.
 * Nothing here executes code: answers are compared against accepted values.
 */

/** Make two code fragments comparable: ignore spacing and quote style. */
export function normalizeCode(value) {
  return String(value ?? '')
    .replace(/['`]/g, '"')
    .replace(/\s+/g, '');
}

/** Make two free-text answers comparable: ignore case, spacing and accents. */
export function normalizeText(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ');
}

/** Check one blank of a fill-code exercise. */
export function checkBlank(value, answers) {
  const given = normalizeCode(value);
  return given !== '' && answers.some((answer) => normalizeCode(answer) === given);
}

/** Check every blank. Returns one boolean per blank. */
export function checkBlanks(values, blanks) {
  return blanks.map((blank, index) => checkBlank(values[index], blank.answers));
}

/** Check a typed answer (numbers or short text). */
export function checkTextAnswer(value, answers) {
  const given = normalizeText(value);
  return given !== '' && answers.some((answer) => normalizeText(answer) === given);
}

/**
 * Check a choice answer.
 * @param {number[]} selected - indexes picked by the user
 * @param {number | number[]} answer - correct index, or indexes for multi-choice
 */
export function checkChoice(selected, answer) {
  const expected = [...(Array.isArray(answer) ? answer : [answer])].sort((a, b) => a - b);
  const given = [...new Set(selected)].sort((a, b) => a - b);
  return (
    expected.length === given.length && expected.every((value, index) => value === given[index])
  );
}

/** True when a choice question accepts several answers. */
export const isMultiChoice = (question) => Array.isArray(question.answer);

/**
 * Score a quiz.
 * @param {object[]} questions - quiz questions
 * @param {Record<string, number[]>} responses - selected indexes by question id
 */
export function scoreQuiz(questions, responses) {
  const results = questions.map((question) => ({
    id: question.id,
    correct: checkChoice(responses[question.id] ?? [], question.answer),
  }));
  const score = results.filter((result) => result.correct).length;
  return { score, total: questions.length, results };
}
