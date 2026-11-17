/**
 * Single access point to localStorage.
 *
 * No other module may read or write localStorage. The only exception is the
 * tiny inline script in index.html that applies the saved theme before first
 * paint; tests/storage.test.js checks that it uses the same key.
 *
 * Every read and write is wrapped in try/catch: when the browser blocks
 * storage (private mode, full quota, disabled cookies) the site keeps working
 * with an in-memory copy for the current session.
 */

const NAMESPACE = 'pyspark-labs';
export const SCHEMA_VERSION = 1;

export const STORAGE_KEYS = Object.freeze({
  progress: `${NAMESPACE}:v${SCHEMA_VERSION}:progress`,
  settings: `${NAMESPACE}:v${SCHEMA_VERSION}:settings`,
});

export const THEMES = Object.freeze(['system', 'light', 'dark']);
export const PROGRESS_EVENT = `${NAMESPACE}:progress-changed`;
export const DEFAULT_PASS_RATIO = 0.7;

/** Session fallback used when localStorage cannot be written. */
const memory = new Map();
let degraded = false;

// ---------------------------------------------------------------------------
// Low-level access
// ---------------------------------------------------------------------------

function getStore() {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null;
  }
}

/** True when localStorage accepts writes right now. */
export function isStorageAvailable() {
  const store = getStore();
  if (!store) return false;
  try {
    const probe = `${NAMESPACE}:probe`;
    store.setItem(probe, '1');
    store.removeItem(probe);
    return true;
  } catch {
    return false;
  }
}

function readJson(key) {
  if (degraded && memory.has(key)) return memory.get(key);
  try {
    const raw = getStore()?.getItem(key);
    if (raw === null || raw === undefined) return memory.get(key) ?? null;
    return JSON.parse(raw);
  } catch {
    // Blocked storage or corrupted JSON: fall back to what we have in memory.
    return memory.get(key) ?? null;
  }
}

function writeJson(key, value) {
  memory.set(key, value);
  try {
    const store = getStore();
    if (!store) throw new Error('localStorage is not available');
    store.setItem(key, JSON.stringify(value));
    degraded = false;
    return true;
  } catch {
    degraded = true;
    return false;
  }
}

function removeKey(key) {
  memory.delete(key);
  try {
    getStore()?.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

function notifyChange() {
  try {
    globalThis.dispatchEvent?.(new CustomEvent(PROGRESS_EVENT));
  } catch {
    // Non-browser environments: nothing to notify.
  }
}

// ---------------------------------------------------------------------------
// Shape helpers
// ---------------------------------------------------------------------------

const isPlainObject = (value) =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const toCount = (value) => (Number.isInteger(value) && value >= 0 ? value : 0);

const toIsoOrNull = (value) =>
  typeof value === 'string' && !Number.isNaN(Date.parse(value)) ? value : null;

function emptyProgress() {
  return { schemaVersion: SCHEMA_VERSION, updatedAt: null, lastVisited: null, modules: {} };
}

function emptyModule() {
  return { theoryRead: false, exercises: {}, quiz: null, labDone: false, completedAt: null };
}

function sanitizeModule(raw) {
  const clean = emptyModule();
  if (!isPlainObject(raw)) return clean;

  clean.theoryRead = raw.theoryRead === true;
  clean.labDone = raw.labDone === true;
  clean.completedAt = toIsoOrNull(raw.completedAt);

  if (isPlainObject(raw.exercises)) {
    for (const [exerciseId, entry] of Object.entries(raw.exercises)) {
      if (!isPlainObject(entry)) continue;
      clean.exercises[exerciseId] = {
        correct: entry.correct === true,
        attempts: toCount(entry.attempts),
      };
    }
  }

  if (isPlainObject(raw.quiz) && Number.isInteger(raw.quiz.total) && raw.quiz.total > 0) {
    const total = raw.quiz.total;
    clean.quiz = {
      bestScore: Math.min(toCount(raw.quiz.bestScore), total),
      lastScore: Math.min(toCount(raw.quiz.lastScore), total),
      total,
      attempts: toCount(raw.quiz.attempts),
    };
  }
  return clean;
}

/**
 * Normalize untrusted data into a valid progress object.
 * Returns null when the data is not a progress object of this schema version.
 */
function sanitizeProgress(raw, knownModuleIds = null) {
  if (!isPlainObject(raw) || raw.schemaVersion !== SCHEMA_VERSION) return null;
  if (!isPlainObject(raw.modules)) return null;

  const clean = emptyProgress();
  clean.updatedAt = toIsoOrNull(raw.updatedAt);
  const skipped = [];

  for (const [moduleId, moduleData] of Object.entries(raw.modules)) {
    if (knownModuleIds && !knownModuleIds.includes(moduleId)) {
      skipped.push(moduleId);
      continue;
    }
    clean.modules[moduleId] = sanitizeModule(moduleData);
  }

  const last = raw.lastVisited;
  if (isPlainObject(last) && typeof last.moduleId === 'string') {
    const known = !knownModuleIds || knownModuleIds.includes(last.moduleId);
    if (known) {
      clean.lastVisited = {
        moduleId: last.moduleId,
        tab: typeof last.tab === 'string' ? last.tab : null,
      };
    }
  }
  return { progress: clean, skipped };
}

// ---------------------------------------------------------------------------
// Progress
// ---------------------------------------------------------------------------

/** Current progress. Never throws; returns an empty progress when unreadable. */
export function getProgress() {
  return sanitizeProgress(readJson(STORAGE_KEYS.progress))?.progress ?? emptyProgress();
}

/** Progress of one module, with defaults when the user has not started it. */
export function getModuleProgress(moduleId) {
  return getProgress().modules[moduleId] ?? emptyModule();
}

function updateProgress(mutate) {
  const progress = getProgress();
  mutate(progress);
  progress.updatedAt = new Date().toISOString();
  const persisted = writeJson(STORAGE_KEYS.progress, progress);
  notifyChange();
  return persisted;
}

function updateModule(moduleId, mutate) {
  return updateProgress((progress) => {
    progress.modules[moduleId] ??= emptyModule();
    mutate(progress.modules[moduleId]);
  });
}

/** Record one attempt at an exercise. A solved exercise stays solved. */
export function saveExerciseResult(moduleId, exerciseId, correct) {
  return updateModule(moduleId, (module) => {
    const entry = module.exercises[exerciseId] ?? { correct: false, attempts: 0 };
    module.exercises[exerciseId] = {
      correct: entry.correct || correct === true,
      attempts: entry.attempts + 1,
    };
  });
}

/** Record a quiz attempt, keeping the best score. */
export function saveQuizResult(moduleId, score, total) {
  return updateModule(moduleId, (module) => {
    // If the quiz changed size, older scores are no longer comparable.
    const previous = module.quiz?.total === total ? module.quiz : null;
    module.quiz = {
      bestScore: Math.max(previous?.bestScore ?? 0, score),
      lastScore: score,
      total,
      attempts: (previous?.attempts ?? 0) + 1,
    };
  });
}

export function setTheoryRead(moduleId, value) {
  return updateModule(moduleId, (module) => {
    module.theoryRead = value === true;
  });
}

export function setLabDone(moduleId, value) {
  return updateModule(moduleId, (module) => {
    module.labDone = value === true;
  });
}

/** Stamp (or clear) the completion date. Returns false when nothing changed. */
export function setModuleCompleted(moduleId, completed) {
  const current = getModuleProgress(moduleId);
  if (Boolean(current.completedAt) === completed) return false;
  updateModule(moduleId, (module) => {
    module.completedAt = completed ? new Date().toISOString() : null;
  });
  return true;
}

export function setLastVisited(moduleId, tab = null) {
  return updateProgress((progress) => {
    progress.lastVisited = { moduleId, tab };
  });
}

export function getLastVisited() {
  return getProgress().lastVisited;
}

/**
 * Compute how far a module is.
 *
 * @param {object} moduleProgress - one entry of progress.modules
 * @param {{ exerciseIds: string[], quizTotal: number, hasLab: boolean }} shape
 * @returns {{ percent: number, completed: boolean, started: boolean, parts: object }}
 */
export function computeModuleStatus(moduleProgress, shape, passRatio = DEFAULT_PASS_RATIO) {
  const data = moduleProgress ?? emptyModule();
  const { exerciseIds = [], quizTotal = 0, hasLab = false } = shape;

  const solved = exerciseIds.filter((id) => data.exercises[id]?.correct).length;
  const quizValid = quizTotal > 0 && data.quiz?.total === quizTotal;
  const quizPassed = quizValid && data.quiz.bestScore / quizTotal >= passRatio;

  const parts = {
    theory: { done: data.theoryRead, ratio: data.theoryRead ? 1 : 0 },
    exercises: {
      applies: exerciseIds.length > 0,
      solved,
      total: exerciseIds.length,
      ratio: exerciseIds.length > 0 ? solved / exerciseIds.length : 0,
    },
    quiz: {
      applies: quizTotal > 0,
      passed: quizPassed,
      bestScore: quizValid ? data.quiz.bestScore : null,
      total: quizTotal,
      ratio: quizPassed ? 1 : 0,
    },
    lab: { applies: hasLab, done: data.labDone, ratio: data.labDone ? 1 : 0 },
  };

  const ratios = [parts.theory.ratio];
  if (parts.exercises.applies) ratios.push(parts.exercises.ratio);
  if (parts.quiz.applies) ratios.push(parts.quiz.ratio);
  if (parts.lab.applies) ratios.push(parts.lab.ratio);
  const percent = Math.round((ratios.reduce((sum, ratio) => sum + ratio, 0) / ratios.length) * 100);

  const completed =
    (parts.quiz.applies || parts.lab.applies) &&
    (!parts.quiz.applies || quizPassed) &&
    (!parts.lab.applies || data.labDone);

  return { percent, completed, started: percent > 0 || Boolean(data.quiz), parts };
}

/** Delete all progress. Settings (theme) are kept. */
export function resetProgress() {
  const removed = removeKey(STORAGE_KEYS.progress);
  notifyChange();
  return removed;
}

/** Subscribe to progress changes. Returns an unsubscribe function. */
export function onProgressChange(callback) {
  globalThis.addEventListener?.(PROGRESS_EVENT, callback);
  return () => globalThis.removeEventListener?.(PROGRESS_EVENT, callback);
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export function getTheme() {
  const settings = readJson(STORAGE_KEYS.settings);
  return isPlainObject(settings) && THEMES.includes(settings.theme) ? settings.theme : 'system';
}

export function setTheme(theme) {
  if (!THEMES.includes(theme)) return false;
  return writeJson(STORAGE_KEYS.settings, { theme });
}

// ---------------------------------------------------------------------------
// Export / import
// ---------------------------------------------------------------------------

/** Serialize progress and settings as a JSON string the user can download. */
export function exportProgress() {
  return JSON.stringify(
    {
      app: NAMESPACE,
      schemaVersion: SCHEMA_VERSION,
      exportedAt: new Date().toISOString(),
      progress: getProgress(),
      settings: { theme: getTheme() },
    },
    null,
    2,
  );
}

/**
 * Replace the current progress with an exported file.
 * Nothing is written unless the whole file is valid.
 *
 * @param {string} json - file content
 * @param {{ knownModuleIds?: string[] }} options - module ids that exist in the site
 * @returns {{ ok: true, modules: number, skipped: string[] } | { ok: false, error: string }}
 */
export function importProgress(json, { knownModuleIds = null } = {}) {
  let data;
  try {
    data = JSON.parse(json);
  } catch {
    return { ok: false, error: 'invalid-json' };
  }
  if (!isPlainObject(data) || data.app !== NAMESPACE) return { ok: false, error: 'not-an-export' };
  if (data.schemaVersion !== SCHEMA_VERSION) return { ok: false, error: 'unsupported-version' };

  const result = sanitizeProgress(data.progress, knownModuleIds);
  if (!result) return { ok: false, error: 'invalid-progress' };

  result.progress.updatedAt = new Date().toISOString();
  writeJson(STORAGE_KEYS.progress, result.progress);
  if (isPlainObject(data.settings) && THEMES.includes(data.settings.theme)) {
    setTheme(data.settings.theme);
  }
  notifyChange();
  return {
    ok: true,
    modules: Object.keys(result.progress.modules).length,
    skipped: result.skipped,
  };
}

/** Test helper: forget the in-memory fallback. */
export function _resetMemoryForTests() {
  memory.clear();
  degraded = false;
}
