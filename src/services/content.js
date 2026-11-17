/**
 * Content access. Modules are discovered from the file system: adding a
 * folder under src/content/modules/ is enough to add a module to the site.
 */
import blocks from '../content/blocks.json';
import cheatsheet from '../content/cheatsheet.json';

const moduleFiles = import.meta.glob('../content/modules/*/module.json', {
  eager: true,
  import: 'default',
});
const theoryLoaders = import.meta.glob('../content/modules/*/theory.md', {
  query: '?raw',
  import: 'default',
});
const diagramFiles = import.meta.glob('../content/diagrams/*.svg', {
  eager: true,
  query: '?raw',
  import: 'default',
});

const folderOf = (path) => path.split('/').at(-2);
const fileNameOf = (path) =>
  path
    .split('/')
    .at(-1)
    .replace(/\.\w+$/, '');

const modules = Object.entries(moduleFiles)
  .map(([path, module]) => ({ ...module, folder: folderOf(path) }))
  .sort((a, b) => a.order - b.order);

const modulesById = new Map(modules.map((module) => [module.id, module]));
const theoryByFolder = new Map(
  Object.entries(theoryLoaders).map(([path, loader]) => [folderOf(path), loader]),
);
const diagrams = new Map(
  Object.entries(diagramFiles).map(([path, svg]) => [fileNameOf(path), svg]),
);

export const getBlocks = () => blocks;
export const getModules = () => modules;
export const getModule = (id) => modulesById.get(id) ?? null;
export const getModuleIds = () => modules.map((module) => module.id);
export const getCheatsheet = () => cheatsheet;
export const getDiagram = (name) => diagrams.get(name) ?? null;
export const getDiagramNames = () => [...diagrams.keys()];
export const hasTheory = (id) => theoryByFolder.has(id);

/** A module the user can open (planned modules are listed but not built yet). */
export const isPublished = (module) => module.status === 'published';

/** Markdown source of a module's theory, loaded on demand. */
export async function loadTheory(id) {
  const loader = theoryByFolder.get(id);
  return loader ? loader() : null;
}

/** Published modules right before and after the given one. */
export function getAdjacentModules(id) {
  const published = modules.filter(isPublished);
  const index = published.findIndex((module) => module.id === id);
  return {
    previous: index > 0 ? published[index - 1] : null,
    next: index >= 0 && index < published.length - 1 ? published[index + 1] : null,
  };
}

/** What counts towards a module's progress (see storage.computeModuleStatus). */
export function getModuleShape(module) {
  return {
    exerciseIds: (module.exercises ?? []).map((exercise) => exercise.id),
    quizTotal: (module.quiz ?? []).length,
    hasLab: Boolean(module.lab),
  };
}
