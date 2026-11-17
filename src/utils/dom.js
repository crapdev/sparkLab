/**
 * Tiny hyperscript helper to build DOM nodes without a framework.
 *
 * h('button', { class: 'btn', onClick: handler }, 'Text')
 *
 * Props:
 * - `class`, `id`, any attribute name: set as attributes (false/null are skipped)
 * - `onEvent`: registered with addEventListener('event', ...)
 * - `html`: trusted HTML string assigned to innerHTML (only for our own content)
 * - `dataset`: object merged into node.dataset
 */
export function h(tag, props = {}, ...children) {
  const node = document.createElement(tag);

  for (const [key, value] of Object.entries(props ?? {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === 'html') {
      node.innerHTML = value;
    } else if (key === 'dataset') {
      Object.assign(node.dataset, value);
    } else if (key.startsWith('on') && typeof value === 'function') {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value === true) {
      node.setAttribute(key, '');
    } else {
      node.setAttribute(key, String(value));
    }
  }

  append(node, children);
  return node;
}

function append(node, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

/** Remove every child of a node and optionally add new ones. */
export function replaceChildren(node, ...children) {
  node.replaceChildren();
  append(node, children);
  return node;
}

/** Format a number of minutes as "35 min" or "1 h 30 min". */
export function formatMinutes(minutes) {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}
