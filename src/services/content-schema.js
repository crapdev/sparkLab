/**
 * Validation of module files. Used by the test suite so a badly written
 * module fails in `npm test` instead of breaking the site.
 */

export const MODULE_STATUSES = ['published', 'planned'];
export const EXERCISE_TYPES = ['choice', 'predict-output', 'fill-code'];
export const BLANK_TOKEN = '___';

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

function validateAnswerIndexes(answer, options, where, errors) {
  const indexes = Array.isArray(answer) ? answer : [answer];
  if (indexes.length === 0) errors.push(`${where}: "answer" is empty`);
  for (const index of indexes) {
    if (!Number.isInteger(index) || index < 0 || index >= options.length) {
      errors.push(`${where}: answer ${index} does not point to an option`);
    }
  }
}

function validateOptions(item, where, errors) {
  if (!Array.isArray(item.options) || item.options.length < 2) {
    errors.push(`${where}: needs at least two options`);
    return;
  }
  if (!item.options.every(isNonEmptyString)) errors.push(`${where}: empty option`);
  validateAnswerIndexes(item.answer, item.options, where, errors);
}

function validateExercise(exercise, where, errors) {
  if (!EXERCISE_TYPES.includes(exercise.type)) {
    errors.push(`${where}: unknown type "${exercise.type}"`);
    return;
  }
  if (!isNonEmptyString(exercise.prompt)) errors.push(`${where}: missing prompt`);
  if (!isNonEmptyString(exercise.explanation)) errors.push(`${where}: missing explanation`);

  if (exercise.type === 'choice') validateOptions(exercise, where, errors);

  if (exercise.type === 'predict-output') {
    if (!isNonEmptyString(exercise.code)) errors.push(`${where}: missing code`);
    if (exercise.options) {
      validateOptions(exercise, where, errors);
    } else if (!Array.isArray(exercise.answers) || !exercise.answers.every(isNonEmptyString)) {
      errors.push(`${where}: needs "options" or a list of accepted "answers"`);
    }
  }

  if (exercise.type === 'fill-code') {
    if (!isNonEmptyString(exercise.code)) {
      errors.push(`${where}: missing code`);
      return;
    }
    const blanksInCode = exercise.code.split(BLANK_TOKEN).length - 1;
    const blanks = Array.isArray(exercise.blanks) ? exercise.blanks : [];
    if (blanksInCode === 0) errors.push(`${where}: code has no ${BLANK_TOKEN} blank`);
    if (blanksInCode !== blanks.length) {
      errors.push(`${where}: ${blanksInCode} blanks in code but ${blanks.length} defined`);
    }
    blanks.forEach((blank, index) => {
      if (!Array.isArray(blank.answers) || !blank.answers.every(isNonEmptyString)) {
        errors.push(`${where}: blank ${index + 1} has no accepted answers`);
      }
    });
  }
}

function validateUniqueIds(items, where, errors) {
  const seen = new Set();
  for (const item of items) {
    if (!isNonEmptyString(item.id)) errors.push(`${where}: item without id`);
    else if (seen.has(item.id)) errors.push(`${where}: duplicated id "${item.id}"`);
    seen.add(item.id);
  }
}

/**
 * Validate one module.
 * @param {object} module - parsed module.json
 * @param {{ folder: string, blockIds: string[], hasTheory: boolean, diagramNames?: string[] }} context
 * @returns {string[]} list of problems; empty when the module is valid
 */
export function validateModule(module, { folder, blockIds, hasTheory }) {
  const errors = [];
  const where = folder;

  if (module.id !== folder) errors.push(`${where}: "id" must match the folder name`);
  if (!Number.isInteger(module.order) || module.order < 1) errors.push(`${where}: invalid "order"`);
  if (!isNonEmptyString(module.title)) errors.push(`${where}: missing title`);
  if (!isNonEmptyString(module.summary)) errors.push(`${where}: missing summary`);
  if (!blockIds.includes(module.block)) errors.push(`${where}: unknown block "${module.block}"`);
  if (!MODULE_STATUSES.includes(module.status)) errors.push(`${where}: invalid "status"`);
  if (!Number.isInteger(module.estimatedMinutes)) errors.push(`${where}: invalid estimatedMinutes`);

  if (module.status !== 'published') return errors;

  // Published modules must be complete.
  if (!hasTheory) errors.push(`${where}: published module without theory.md`);
  if (!Array.isArray(module.objectives) || module.objectives.length === 0) {
    errors.push(`${where}: missing objectives`);
  }

  const exercises = module.exercises ?? [];
  const quiz = module.quiz ?? [];
  if (exercises.length === 0) errors.push(`${where}: published module without exercises`);
  validateUniqueIds(exercises, `${where} exercises`, errors);
  validateUniqueIds(quiz, `${where} quiz`, errors);
  exercises.forEach((exercise) => validateExercise(exercise, `${where}/${exercise.id}`, errors));
  quiz.forEach((question) => {
    const questionWhere = `${where}/quiz/${question.id}`;
    if (!isNonEmptyString(question.question)) errors.push(`${questionWhere}: missing question`);
    if (!isNonEmptyString(question.explanation))
      errors.push(`${questionWhere}: missing explanation`);
    validateOptions(question, questionWhere, errors);
  });

  if (!module.lab) {
    errors.push(`${where}: published module without lab`);
  } else {
    if (!isNonEmptyString(module.lab.path)) errors.push(`${where}: lab without path`);
    if (!isNonEmptyString(module.lab.summary)) errors.push(`${where}: lab without summary`);
    if (!Array.isArray(module.lab.tasks) || module.lab.tasks.length === 0) {
      errors.push(`${where}: lab without tasks`);
    }
  }
  return errors;
}

/** Names of the diagrams referenced from a theory file. */
export function findDiagramReferences(markdown) {
  return [...markdown.matchAll(/\]\(diagram:([a-z0-9-]+)/g)].map((match) => match[1]);
}
