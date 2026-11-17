/**
 * Minimal hash router: "#/modulo/01-fundamentos/quiz" -> view + params.
 * Hash routing needs no server rewrites, so the site works on any static host.
 */

/** Turn "/modulo/:id/:tab?" into a matcher function. */
function compile(pattern) {
  const names = [];
  const source = pattern
    .split('/')
    .filter(Boolean)
    .map((segment) => {
      if (!segment.startsWith(':')) return `/${segment}`;
      const optional = segment.endsWith('?');
      names.push(segment.slice(1, optional ? -1 : undefined));
      return optional ? '(?:/([^/]+))?' : '/([^/]+)';
    })
    .join('');
  const regex = new RegExp(`^${source || '/'}/?$`);

  return (path) => {
    const match = regex.exec(path);
    if (!match) return null;
    return Object.fromEntries(
      names.map((name, index) => [
        name,
        match[index + 1] ? decodeURIComponent(match[index + 1]) : null,
      ]),
    );
  };
}

/** Current path taken from the hash, always starting with "/". */
export function currentPath() {
  const path = globalThis.location.hash.replace(/^#/, '');
  return path.startsWith('/') ? path : '/';
}

/** Change the route. */
export function navigate(path) {
  globalThis.location.hash = path;
}

/**
 * @param {{ pattern: string, view: Function }[]} routes
 * @param {{ onRoute: (match: { view: Function, params: object, path: string }) => void, notFound: Function }} options
 */
export function createRouter(routes, { onRoute, notFound }) {
  const compiled = routes.map((route) => ({ ...route, match: compile(route.pattern) }));

  function resolve() {
    const path = currentPath();
    for (const route of compiled) {
      const params = route.match(path);
      if (params) return onRoute({ view: route.view, params, path });
    }
    return onRoute({ view: notFound, params: {}, path });
  }

  return {
    start() {
      globalThis.addEventListener('hashchange', resolve);
      resolve();
    },
    refresh: resolve,
  };
}
