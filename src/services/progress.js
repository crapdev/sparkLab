/**
 * Progress derived from stored data plus the content definition.
 * storage.js knows how data is stored; this module knows what a module contains.
 */
import { SITE } from '../config.js';
import { getModuleShape, getModules, isPublished } from './content.js';
import { computeModuleStatus, getProgress, setModuleCompleted } from './storage.js';

/** Status of one module for the current user. */
export function getModuleStatus(module, progress = getProgress()) {
  return computeModuleStatus(
    progress.modules[module.id],
    getModuleShape(module),
    SITE.quizPassRatio,
  );
}

/** Keep the stored completion date in sync after any change in a module. */
export function syncModuleCompletion(module) {
  const status = getModuleStatus(module);
  setModuleCompleted(module.id, status.completed);
  return status;
}

/** Totals across every published module. */
export function getOverallStatus() {
  const progress = getProgress();
  const published = getModules().filter(isPublished);
  const statuses = published.map((module) => getModuleStatus(module, progress));
  const completed = statuses.filter((status) => status.completed).length;
  const percent = statuses.length
    ? Math.round(statuses.reduce((sum, status) => sum + status.percent, 0) / statuses.length)
    : 0;
  return { completed, total: published.length, planned: getModules().length, percent };
}
