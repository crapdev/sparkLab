import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  PROGRESS_EVENT,
  STORAGE_KEYS,
  _resetMemoryForTests,
  computeModuleStatus,
  exportProgress,
  getLastVisited,
  getModuleProgress,
  getProgress,
  getTheme,
  importProgress,
  isStorageAvailable,
  resetProgress,
  saveExerciseResult,
  saveQuizResult,
  setLabDone,
  setLastVisited,
  setModuleCompleted,
  setTheme,
  setTheoryRead,
} from '../src/services/storage.js';

const MODULE = '01-fundamentos';

beforeEach(() => {
  localStorage.clear();
  _resetMemoryForTests();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('keys', () => {
  it('are namespaced and versioned', () => {
    expect(STORAGE_KEYS.progress).toBe('pyspark-labs:v1:progress');
    expect(STORAGE_KEYS.settings).toBe('pyspark-labs:v1:settings');
  });

  it('match the inline theme script in index.html', () => {
    const html = readFileSync(resolve(process.cwd(), 'index.html'), 'utf8');
    expect(html).toContain(`'${STORAGE_KEYS.settings}'`);
  });
});

describe('progress', () => {
  it('starts empty', () => {
    expect(getProgress().modules).toEqual({});
    expect(getLastVisited()).toBeNull();
    expect(getModuleProgress(MODULE).theoryRead).toBe(false);
  });

  it('records exercise attempts and keeps a solved exercise solved', () => {
    saveExerciseResult(MODULE, 'ex-1', false);
    saveExerciseResult(MODULE, 'ex-1', true);
    saveExerciseResult(MODULE, 'ex-1', false);
    expect(getModuleProgress(MODULE).exercises['ex-1']).toEqual({ correct: true, attempts: 3 });
  });

  it('keeps the best quiz score', () => {
    saveQuizResult(MODULE, 6, 8);
    saveQuizResult(MODULE, 4, 8);
    expect(getModuleProgress(MODULE).quiz).toEqual({
      bestScore: 6,
      lastScore: 4,
      total: 8,
      attempts: 2,
    });
  });

  it('drops old quiz scores when the quiz changes size', () => {
    saveQuizResult(MODULE, 5, 5);
    saveQuizResult(MODULE, 3, 8);
    expect(getModuleProgress(MODULE).quiz).toMatchObject({ bestScore: 3, total: 8, attempts: 1 });
  });

  it('stores theory, lab and last visited module', () => {
    setTheoryRead(MODULE, true);
    setLabDone(MODULE, true);
    setLastVisited(MODULE, 'quiz');
    expect(getModuleProgress(MODULE)).toMatchObject({ theoryRead: true, labDone: true });
    expect(getLastVisited()).toEqual({ moduleId: MODULE, tab: 'quiz' });
  });

  it('stamps and clears the completion date only when it changes', () => {
    expect(setModuleCompleted(MODULE, true)).toBe(true);
    expect(setModuleCompleted(MODULE, true)).toBe(false);
    expect(getModuleProgress(MODULE).completedAt).toEqual(expect.any(String));
    expect(setModuleCompleted(MODULE, false)).toBe(true);
    expect(getModuleProgress(MODULE).completedAt).toBeNull();
  });

  it('persists to localStorage under the versioned key', () => {
    setLabDone(MODULE, true);
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEYS.progress));
    expect(raw.schemaVersion).toBe(1);
    expect(raw.modules[MODULE].labDone).toBe(true);
  });

  it('notifies listeners when progress changes', () => {
    const listener = vi.fn();
    window.addEventListener(PROGRESS_EVENT, listener);
    setTheoryRead(MODULE, true);
    window.removeEventListener(PROGRESS_EVENT, listener);
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('resets progress but keeps the theme', () => {
    setTheme('dark');
    setLabDone(MODULE, true);
    resetProgress();
    expect(getProgress().modules).toEqual({});
    expect(getTheme()).toBe('dark');
  });
});

describe('resilience', () => {
  it('ignores corrupted JSON', () => {
    localStorage.setItem(STORAGE_KEYS.progress, '{not json');
    expect(getProgress().modules).toEqual({});
  });

  it('ignores data from another schema version', () => {
    localStorage.setItem(
      STORAGE_KEYS.progress,
      JSON.stringify({ schemaVersion: 99, modules: { [MODULE]: { labDone: true } } }),
    );
    expect(getProgress().modules).toEqual({});
  });

  it('sanitizes malformed module entries', () => {
    localStorage.setItem(
      STORAGE_KEYS.progress,
      JSON.stringify({
        schemaVersion: 1,
        modules: {
          [MODULE]: {
            theoryRead: 'yes',
            labDone: true,
            exercises: { ok: { correct: true, attempts: 2 }, bad: 'nope', neg: { attempts: -4 } },
            quiz: { bestScore: 99, total: 8 },
          },
        },
      }),
    );
    const module = getModuleProgress(MODULE);
    expect(module.theoryRead).toBe(false);
    expect(module.labDone).toBe(true);
    expect(module.exercises).toEqual({
      ok: { correct: true, attempts: 2 },
      neg: { correct: false, attempts: 0 },
    });
    expect(module.quiz.bestScore).toBe(8);
  });

  it('keeps working in memory when localStorage throws on write', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('quota', 'QuotaExceededError');
    });
    expect(isStorageAvailable()).toBe(false);
    expect(setLabDone(MODULE, true)).toBe(false);
    expect(getModuleProgress(MODULE).labDone).toBe(true);
    saveExerciseResult(MODULE, 'ex-1', true);
    expect(getModuleProgress(MODULE)).toMatchObject({ labDone: true });
    expect(getModuleProgress(MODULE).exercises['ex-1'].correct).toBe(true);
  });

  it('keeps working when localStorage throws on read', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('denied', 'SecurityError');
    });
    expect(() => getProgress()).not.toThrow();
    expect(getTheme()).toBe('system');
  });
});

describe('theme', () => {
  it('defaults to system and rejects unknown values', () => {
    expect(getTheme()).toBe('system');
    expect(setTheme('neon')).toBe(false);
    expect(setTheme('dark')).toBe(true);
    expect(getTheme()).toBe('dark');
  });
});

describe('export and import', () => {
  it('round-trips progress and theme', () => {
    setTheme('dark');
    setLabDone(MODULE, true);
    saveQuizResult(MODULE, 7, 8);
    const file = exportProgress();

    resetProgress();
    setTheme('light');
    const result = importProgress(file, { knownModuleIds: [MODULE] });

    expect(result).toEqual({ ok: true, modules: 1, skipped: [] });
    expect(getModuleProgress(MODULE)).toMatchObject({ labDone: true });
    expect(getModuleProgress(MODULE).quiz.bestScore).toBe(7);
    expect(getTheme()).toBe('dark');
  });

  it('skips modules that no longer exist', () => {
    setLabDone('99-gone', true);
    setLabDone(MODULE, true);
    const result = importProgress(exportProgress(), { knownModuleIds: [MODULE] });
    expect(result).toMatchObject({ ok: true, modules: 1, skipped: ['99-gone'] });
  });

  it.each([
    ['not json at all', 'invalid-json'],
    [JSON.stringify({ hello: 'world' }), 'not-an-export'],
    [
      JSON.stringify({ app: 'pyspark-labs', schemaVersion: 2, progress: {} }),
      'unsupported-version',
    ],
    [JSON.stringify({ app: 'pyspark-labs', schemaVersion: 1, progress: [] }), 'invalid-progress'],
  ])('rejects invalid files without touching current progress', (file, error) => {
    setLabDone(MODULE, true);
    expect(importProgress(file)).toEqual({ ok: false, error });
    expect(getModuleProgress(MODULE).labDone).toBe(true);
  });
});

describe('computeModuleStatus', () => {
  const shape = { exerciseIds: ['a', 'b'], quizTotal: 8, hasLab: true };

  it('is 0% and not started for an untouched module', () => {
    expect(computeModuleStatus(undefined, shape)).toMatchObject({
      percent: 0,
      completed: false,
      started: false,
    });
  });

  it('averages theory, exercises, quiz and lab', () => {
    const progress = {
      theoryRead: true,
      exercises: { a: { correct: true, attempts: 1 } },
      quiz: null,
      labDone: false,
    };
    // theory 1 + exercises 0.5 + quiz 0 + lab 0 = 1.5 of 4
    expect(computeModuleStatus(progress, shape).percent).toBe(38);
  });

  it('completes a module with a passed quiz and a finished lab', () => {
    const progress = {
      theoryRead: false,
      exercises: {},
      quiz: { bestScore: 6, total: 8, attempts: 1 },
      labDone: true,
    };
    expect(computeModuleStatus(progress, shape, 0.7).completed).toBe(true);
  });

  it('does not complete with a failed quiz', () => {
    const progress = {
      theoryRead: true,
      exercises: {},
      quiz: { bestScore: 5, total: 8, attempts: 1 },
      labDone: true,
    };
    expect(computeModuleStatus(progress, shape, 0.7).completed).toBe(false);
  });

  it('ignores quiz scores recorded for a different quiz size', () => {
    const progress = {
      theoryRead: true,
      exercises: {},
      quiz: { bestScore: 5, total: 5, attempts: 1 },
      labDone: true,
    };
    expect(computeModuleStatus(progress, shape).parts.quiz).toMatchObject({
      passed: false,
      bestScore: null,
    });
  });
});
