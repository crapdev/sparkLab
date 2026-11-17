/**
 * Markdown rendering for theory and exercise texts.
 *
 * Extensions on top of standard Markdown:
 * - ![alt](diagram:name "caption") inlines src/content/diagrams/name.svg
 * - > [!NOTE] / [!TIP] / [!WARNING] / [!EXTRA] blockquotes become callouts
 * - ```output fences render as program output instead of code
 */
import { Marked } from 'marked';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import sql from 'highlight.js/lib/languages/sql';
import bash from 'highlight.js/lib/languages/bash';
import { getDiagram } from './content.js';

hljs.registerLanguage('python', python);
hljs.registerLanguage('sql', sql);
hljs.registerLanguage('bash', bash);

const CALLOUT_TITLES = {
  NOTE: 'Nota',
  TIP: 'Consejo',
  WARNING: 'Cuidado',
  EXTRA: 'Para profundizar',
};
const OUTPUT_LANGUAGES = ['output', 'text', ''];
const DIAGRAM_PREFIX = 'diagram:';

export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Syntax-highlight a code fragment. Unknown languages are only escaped. */
export function highlight(code, language) {
  if (language && hljs.getLanguage(language)) {
    return hljs.highlight(code, { language, ignoreIllegals: true }).value;
  }
  return escapeHtml(code);
}

/** HTML for a code block with a copy button, or for a block of program output. */
export function codeBlockHtml(code, language = '') {
  const text = code.replace(/\n$/, '');
  if (OUTPUT_LANGUAGES.includes(language)) {
    return `<div class="code-block code-block--output"><span class="code-block__label">Salida</span><pre><code>${escapeHtml(text)}</code></pre></div>`;
  }
  return (
    `<div class="code-block" data-language="${escapeHtml(language)}">` +
    `<button type="button" class="code-block__copy" data-copy>Copiar</button>` +
    `<pre><code class="hljs">${highlight(text, language)}</code></pre></div>`
  );
}

const renderer = {
  code({ text, lang }) {
    return codeBlockHtml(text, (lang ?? '').trim());
  },

  image({ href, title, text }) {
    if (!href.startsWith(DIAGRAM_PREFIX)) return false;
    const name = href.slice(DIAGRAM_PREFIX.length);
    const svg = getDiagram(name);
    if (!svg)
      return `<p class="diagram diagram--missing">Falta el diagrama "${escapeHtml(name)}".</p>`;
    const caption = title ? `<figcaption>${escapeHtml(title)}</figcaption>` : '';
    return `<figure class="diagram"><div class="diagram__canvas" role="img" aria-label="${escapeHtml(text)}">${svg}</div>${caption}</figure>`;
  },

  blockquote({ tokens }) {
    const body = this.parser.parse(tokens);
    const match = body.match(/^<p>\[!(\w+)\]\s*/);
    const kind = match?.[1].toUpperCase();
    if (!kind || !CALLOUT_TITLES[kind]) return false;
    const content = body.replace(match[0], '<p>').replace(/^<p><\/p>\s*/, '');
    return `<aside class="callout callout--${kind.toLowerCase()}"><p class="callout__title">${CALLOUT_TITLES[kind]}</p>${content}</aside>`;
  },

  link({ href, title, tokens }) {
    const label = this.parser.parseInline(tokens);
    const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
    const external = /^https?:\/\//.test(href);
    const target = external ? ' target="_blank" rel="noopener noreferrer"' : '';
    return `<a href="${escapeHtml(href)}"${titleAttr}${target}>${label}</a>`;
  },
};

const marked = new Marked({ gfm: true, renderer });

/** Render a full Markdown document (module theory). */
export function renderMarkdown(source) {
  return marked
    .parse(source)
    .replace(/<table>/g, '<div class="table-wrap"><table>')
    .replace(/<\/table>/g, '</table></div>');
}

/** Render a short text with inline Markdown (prompts, options, explanations). */
export function renderInline(source) {
  return marked.parseInline(source);
}
