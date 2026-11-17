import { h, formatMinutes } from '../utils/dom.js';
import { getBlocks, getModule, getModules, isPublished } from '../services/content.js';
import { getModuleStatus, getOverallStatus } from '../services/progress.js';
import { getLastVisited, getProgress } from '../services/storage.js';
import { createProgressBar } from '../components/progress-bar.js';

const TAB_LABELS = {
  teoria: 'Teoría',
  ejercicios: 'Ejercicios',
  quiz: 'Quiz',
  laboratorio: 'Laboratorio',
};

function continueCard() {
  const last = getLastVisited();
  const module = last && getModule(last.moduleId);
  if (!module || !isPublished(module)) return null;
  const tab = TAB_LABELS[last.tab] ? last.tab : 'teoria';

  return h(
    'a',
    { class: 'continue-card', href: `#/modulo/${module.id}/${tab}` },
    h('span', { class: 'continue-card__label' }, 'Continuar donde quedaste'),
    h('span', { class: 'continue-card__title' }, `Módulo ${module.order} · ${module.title}`),
    h('span', { class: 'continue-card__tab' }, `${TAB_LABELS[tab]} →`),
  );
}

function moduleCard(module, progress) {
  const number = h('span', { class: 'module-card__number' }, String(module.order).padStart(2, '0'));
  const badges = [!isPublished(module) && h('span', { class: 'badge' }, 'Próximamente')];
  const heading = h('h3', { class: 'module-card__title' }, module.title, badges);
  const summary = h('p', { class: 'module-card__summary' }, module.summary);

  if (!isPublished(module)) {
    return h(
      'li',
      { class: 'module-card module-card--planned' },
      number,
      h('div', { class: 'module-card__body' }, heading, summary),
    );
  }

  const status = getModuleStatus(module, progress);
  const state = status.completed
    ? 'Completado'
    : status.started
      ? `${status.percent} %`
      : 'Sin empezar';
  return h(
    'li',
    { class: `module-card${status.completed ? ' module-card--done' : ''}` },
    number,
    h(
      'div',
      { class: 'module-card__body' },
      heading,
      summary,
      h(
        'div',
        { class: 'module-card__meta' },
        h('span', {}, formatMinutes(module.estimatedMinutes)),
        h('span', { class: 'module-card__state' }, state),
      ),
      createProgressBar(status.percent, `Progreso del módulo ${module.order}`),
    ),
    h('a', { class: 'module-card__link', href: `#/modulo/${module.id}` }, `Abrir ${module.title}`),
  );
}

export function homeView() {
  const progress = getProgress();
  const overall = getOverallStatus();
  const modules = getModules();

  const blocks = getBlocks().map((block) => {
    const blockModules = modules.filter((module) => module.block === block.id);
    return h(
      'section',
      { class: 'block' },
      h(
        'header',
        { class: 'block__header' },
        h('h2', { class: 'block__title' }, block.title),
        h('p', { class: 'block__description' }, block.description),
      ),
      h(
        'ol',
        { class: 'module-list' },
        blockModules.map((module) => moduleCard(module, progress)),
      ),
    );
  });

  return h(
    'div',
    { class: 'home' },
    h(
      'section',
      { class: 'hero' },
      h('p', { class: 'hero__eyebrow' }, 'Estudia · Practica · Repite'),
      h('h1', { class: 'hero__title' }, 'Aprende PySpark practicando'),
      h(
        'p',
        { class: 'hero__lead' },
        'Teoría corta, ejercicios en el navegador y laboratorios en Google Colab con tests automáticos.',
      ),
      h(
        'div',
        { class: 'hero__progress' },
        h(
          'p',
          { class: 'hero__progress-text' },
          `${overall.completed} de ${overall.total} módulos completados`,
          overall.planned > overall.total &&
            h(
              'span',
              { class: 'hero__progress-note' },
              ` · ${overall.planned - overall.total} en preparación`,
            ),
        ),
        createProgressBar(overall.percent, 'Progreso global'),
      ),
      continueCard(),
    ),
    blocks,
  );
}
