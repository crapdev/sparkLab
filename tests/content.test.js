import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  getBlocks,
  getCheatsheet,
  getDiagramNames,
  getModules,
  hasTheory,
  isPublished,
  loadTheory,
} from '../src/services/content.js';
import { findDiagramReferences, validateModule } from '../src/services/content-schema.js';
import { renderMarkdown } from '../src/services/markdown.js';

// Vitest runs from the repository root.
const repoPath = (relative) => resolve(process.cwd(), relative);
const modules = getModules();
const blockIds = getBlocks().map((block) => block.id);

describe('modules', () => {
  it('exist', () => {
    expect(modules.length).toBeGreaterThan(0);
    expect(modules.filter(isPublished).length).toBeGreaterThan(0);
  });

  it('have unique ids and consecutive order', () => {
    expect(new Set(modules.map((module) => module.id)).size).toBe(modules.length);
    expect(modules.map((module) => module.order)).toEqual(modules.map((_, index) => index + 1));
  });

  it.each(modules.map((module) => [module.folder, module]))('%s is valid', (folder, module) => {
    const errors = validateModule(module, { folder, blockIds, hasTheory: hasTheory(folder) });
    expect(errors).toEqual([]);
  });

  it('every block has at least one module', () => {
    for (const blockId of blockIds) {
      expect(modules.some((module) => module.block === blockId)).toBe(true);
    }
  });
});

describe.each(modules.filter(isPublished).map((module) => [module.id, module]))(
  'published module %s',
  (id, module) => {
    it('has theory that renders and only references existing diagrams', async () => {
      const theory = await loadTheory(id);
      expect(theory.length).toBeGreaterThan(500);
      const diagrams = getDiagramNames();
      for (const name of findDiagramReferences(theory)) {
        expect(diagrams, `diagram "${name}"`).toContain(name);
      }
      const html = renderMarkdown(theory);
      expect(html).not.toContain('diagram--missing');
      expect(html).not.toContain('[!');
    });

    it('has its lab notebooks generated', () => {
      for (const file of ['source.py', 'lab.ipynb', 'solution.ipynb']) {
        expect(existsSync(repoPath(`${module.lab.path}/${file}`)), file).toBe(true);
      }
    });

    it('only uses datasets that exist in public/data', () => {
      for (const dataset of module.lab.datasets ?? []) {
        expect(existsSync(repoPath(`public/data/${dataset}`)), dataset).toBe(true);
      }
    });
  },
);

describe('cheatsheet', () => {
  const entries = getCheatsheet();
  const moduleIds = modules.map((module) => module.id);

  it('has unique names', () => {
    expect(new Set(entries.map((entry) => entry.name)).size).toBe(entries.length);
  });

  it.each(entries.map((entry) => [entry.name, entry]))('%s is complete', (_name, entry) => {
    for (const field of ['name', 'category', 'signature', 'description', 'example']) {
      expect(entry[field], field).toEqual(expect.any(String));
      expect(entry[field].trim(), field).not.toBe('');
    }
    expect(moduleIds).toContain(entry.module);
  });
});
