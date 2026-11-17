import { h, formatMinutes, replaceChildren } from '../utils/dom.js';
import { SITE } from '../config.js';
import {
  getAdjacentModules,
  getBlocks,
  getModule,
  isPublished,
  loadTheory,
} from '../services/content.js';
import { renderMarkdown } from '../services/markdown.js';
import { syncModuleCompletion } from '../services/progress.js';
import {
  getModuleProgress,
  saveExerciseResult,
  saveQuizResult,
  setLabDone,
  setLastVisited,
  setTheoryRead,
} from '../services/storage.js';
import { createExerciseCard } from '../components/exercise-card.js';
import { createLabCard } from '../components/lab-card.js';
import { createProgressBar } from '../components/progress-bar.js';
import { createQuiz } from '../components/quiz.js';
import { notFoundView } from './not-found.js';

const TABS = [
  { id: 'teoria', label: 'Teoría' },
  { id: 'ejercicios', label: 'Ejercicios' },
  { id: 'quiz', label: 'Quiz' },
  { id: 'laboratorio', label: 'Laboratorio' },
];

async function theoryTab(module, refresh) {
  const source = await loadTheory(module.id);
  const read = getModuleProgress(module.id).theoryRead;
  const toggle = h(
    'button',
    { type: 'button', class: `btn ${read ? 'btn--ghost' : 'btn--primary'}` },
    read ? 'Marcar como no leída' : 'Marcar teoría como leída',
  );
  toggle.addEventListener('click', () => {
    setTheoryRead(module.id, !read);
    refresh();
  });

  return h(
    'div',
    { class: 'tab-panel' },
    module.objectives &&
      h(
        'section',
        { class: 'objectives' },
        h('h2', { class: 'objectives__title' }, 'Al terminar podrás'),
        h(
          'ul',
          {},
          module.objectives.map((objective) => h('li', {}, objective)),
        ),
      ),
    h('article', { class: 'prose', html: renderMarkdown(source ?? '') }),
    h(
      'div',
      { class: 'tab-panel__footer' },
      toggle,
      h(
        'a',
        { class: 'btn btn--ghost', href: `#/modulo/${module.id}/ejercicios` },
        'Ir a los ejercicios →',
      ),
    ),
  );
}

function exercisesTab(module, onChange) {
  const stored = getModuleProgress(module.id).exercises;
  return h(
    'div',
    { class: 'tab-panel' },
    h(
      'p',
      { class: 'tab-panel__intro' },
      'Responde y comprueba. Aquí no se ejecuta código: se compara tu respuesta con la correcta. El código de verdad lo ejecutas en el laboratorio.',
    ),
    module.exercises.map((exercise, index) =>
      createExerciseCard(exercise, {
        number: index + 1,
        solved: stored[exercise.id]?.correct === true,
        onResult: (correct) => {
          saveExerciseResult(module.id, exercise.id, correct);
          onChange();
        },
      }),
    ),
    h(
      'div',
      { class: 'tab-panel__footer' },
      h('a', { class: 'btn btn--ghost', href: `#/modulo/${module.id}/quiz` }, 'Ir al quiz →'),
    ),
  );
}

function quizTab(module, onChange) {
  if (!module.quiz?.length) {
    return h('div', { class: 'tab-panel' }, h('p', {}, 'Este módulo no tiene quiz.'));
  }
  return h(
    'div',
    { class: 'tab-panel' },
    createQuiz(module.quiz, {
      passRatio: SITE.quizPassRatio,
      best: getModuleProgress(module.id).quiz,
      onSubmit: (score, total) => {
        saveQuizResult(module.id, score, total);
        onChange();
        return getModuleProgress(module.id).quiz;
      },
    }),
  );
}

function labTab(module, onChange) {
  return h(
    'div',
    { class: 'tab-panel' },
    createLabCard(module.lab, {
      done: getModuleProgress(module.id).labDone,
      onToggleDone: (done) => {
        setLabDone(module.id, done);
        onChange();
      },
    }),
  );
}

function statusSummary(status) {
  const { parts } = status;
  const items = [
    ['Teoría', parts.theory.done ? 'leída' : 'pendiente', parts.theory.done],
    parts.exercises.applies && [
      'Ejercicios',
      `${parts.exercises.solved}/${parts.exercises.total}`,
      parts.exercises.solved === parts.exercises.total,
    ],
    parts.quiz.applies && [
      'Quiz',
      parts.quiz.bestScore === null ? 'pendiente' : `${parts.quiz.bestScore}/${parts.quiz.total}`,
      parts.quiz.passed,
    ],
    parts.lab.applies && ['Lab', parts.lab.done ? 'hecho' : 'pendiente', parts.lab.done],
  ].filter(Boolean);

  return h(
    'ul',
    { class: 'module__checklist' },
    items.map(([label, value, done]) =>
      h(
        'li',
        { class: done ? 'is-done' : '' },
        h('span', {}, done ? '✓' : '○'),
        ` ${label}: ${value}`,
      ),
    ),
  );
}

export async function moduleView({ id, tab }) {
  const module = getModule(id);
  if (!module || !isPublished(module)) return notFoundView();

  const activeTab = TABS.some((item) => item.id === tab) ? tab : 'teoria';
  setLastVisited(module.id, activeTab);

  const block = getBlocks().find((item) => item.id === module.block);
  const { previous, next } = getAdjacentModules(module.id);
  const statusBox = h('div', { class: 'module__status' });
  const panel = h('div', { class: 'module__panel' });

  function renderStatus() {
    const status = syncModuleCompletion(module);
    replaceChildren(
      statusBox,
      h(
        'div',
        { class: 'module__progress' },
        createProgressBar(status.percent, 'Progreso del módulo'),
        h(
          'span',
          { class: 'module__percent' },
          status.completed && status.percent < 100
            ? `Completado · ${status.percent} %`
            : status.completed
              ? 'Completado'
              : `${status.percent} %`,
        ),
      ),
      statusSummary(status),
    );
  }

  async function renderPanel() {
    const content = {
      teoria: () => theoryTab(module, renderAll),
      ejercicios: () => exercisesTab(module, renderStatus),
      quiz: () => quizTab(module, renderStatus),
      laboratorio: () => labTab(module, renderStatus),
    }[activeTab];
    replaceChildren(panel, await content());
  }

  async function renderAll() {
    renderStatus();
    await renderPanel();
  }

  const view = h(
    'div',
    { class: 'module' },
    h(
      'header',
      { class: 'module__header' },
      h('p', { class: 'module__eyebrow' }, `${block?.title ?? ''} · Módulo ${module.order}`),
      h('h1', { class: 'module__title' }, module.title),
      h('p', { class: 'module__summary' }, module.summary),
      h(
        'p',
        { class: 'module__time' },
        `Tiempo estimado: ${formatMinutes(module.estimatedMinutes)}`,
      ),
      statusBox,
    ),
    h(
      'nav',
      { class: 'tabs', 'aria-label': 'Secciones del módulo' },
      TABS.map((item) =>
        h(
          'a',
          {
            class: `tabs__tab${item.id === activeTab ? ' is-active' : ''}`,
            href: `#/modulo/${module.id}/${item.id}`,
            'aria-current': item.id === activeTab ? 'page' : null,
          },
          item.label,
        ),
      ),
    ),
    panel,
    h(
      'nav',
      { class: 'module__pager', 'aria-label': 'Otros módulos' },
      previous
        ? h('a', { class: 'pager__link', href: `#/modulo/${previous.id}` }, `← ${previous.title}`)
        : h('span', {}),
      next
        ? h(
            'a',
            { class: 'pager__link pager__link--next', href: `#/modulo/${next.id}` },
            `${next.title} →`,
          )
        : h('a', { class: 'pager__link pager__link--next', href: '#/' }, 'Volver al inicio →'),
    ),
  );

  await renderAll();
  return view;
}
