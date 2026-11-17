import { describe, expect, it } from 'vitest';
import {
  checkBlank,
  checkBlanks,
  checkChoice,
  checkTextAnswer,
  normalizeCode,
  scoreQuiz,
} from '../src/services/checkers.js';

describe('normalizeCode', () => {
  it('ignores spacing and quote style', () => {
    expect(normalizeCode(" F.col( 'id' ) ")).toBe(normalizeCode('F.col("id")'));
  });

  it('stays case sensitive, like Python', () => {
    expect(normalizeCode('True')).not.toBe(normalizeCode('true'));
  });
});

describe('checkBlank', () => {
  it('accepts any of the listed answers', () => {
    expect(checkBlank('where', ['filter', 'where'])).toBe(true);
    expect(checkBlank(' filter ', ['filter', 'where'])).toBe(true);
  });

  it('rejects wrong and empty answers', () => {
    expect(checkBlank('select', ['filter'])).toBe(false);
    expect(checkBlank('   ', ['filter'])).toBe(false);
    expect(checkBlank('Filter', ['filter'])).toBe(false);
  });

  it('checks every blank independently', () => {
    const blanks = [{ answers: ['master'] }, { answers: ['getOrCreate'] }];
    expect(checkBlanks(['master', 'getorcreate'], blanks)).toEqual([true, false]);
  });
});

describe('checkTextAnswer', () => {
  it('ignores case, accents and extra spaces', () => {
    expect(checkTextAnswer('  CERO ', ['0', 'cero'])).toBe(true);
    expect(checkTextAnswer('Ningúno', ['ninguno'])).toBe(true);
  });

  it('rejects wrong and empty answers', () => {
    expect(checkTextAnswer('1', ['0', 'cero'])).toBe(false);
    expect(checkTextAnswer('', ['0'])).toBe(false);
  });
});

describe('checkChoice', () => {
  it('checks single answers', () => {
    expect(checkChoice([2], 2)).toBe(true);
    expect(checkChoice([1], 2)).toBe(false);
    expect(checkChoice([], 2)).toBe(false);
  });

  it('requires exactly the right set for multiple answers', () => {
    expect(checkChoice([4, 1, 3], [1, 3, 4])).toBe(true);
    expect(checkChoice([1, 3], [1, 3, 4])).toBe(false);
    expect(checkChoice([0, 1, 3, 4], [1, 3, 4])).toBe(false);
  });
});

describe('scoreQuiz', () => {
  const questions = [
    { id: 'a', answer: 0 },
    { id: 'b', answer: [1, 2] },
    { id: 'c', answer: 3 },
  ];

  it('counts correct answers and reports each question', () => {
    const result = scoreQuiz(questions, { a: [0], b: [2, 1], c: [0] });
    expect(result.score).toBe(2);
    expect(result.total).toBe(3);
    expect(result.results.map((item) => item.correct)).toEqual([true, true, false]);
  });

  it('treats unanswered questions as wrong', () => {
    expect(scoreQuiz(questions, {}).score).toBe(0);
  });
});
