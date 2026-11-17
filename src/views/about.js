import { h } from '../utils/dom.js';
import { githubUrl, isRepoConfigured } from '../config.js';

const external = (href, text) =>
  h('a', { href, target: '_blank', rel: 'noopener noreferrer' }, text);

export function aboutView() {
  return h(
    'div',
    { class: 'page prose' },
    h('h1', {}, 'Acerca de PySpark Labs'),
    h(
      'p',
      { class: 'page__lead' },
      'Un recurso para estudiar y practicar PySpark, pensado para compartirlo entre compañeros de bootcamp.',
    ),

    h('h2', {}, 'Cómo usarlo'),
    h(
      'ol',
      {},
      h('li', {}, 'Lee la teoría del módulo.'),
      h('li', {}, 'Haz los ejercicios y el quiz en el navegador.'),
      h(
        'li',
        {},
        'Abre el laboratorio en Google Colab y resuélvelo hasta que pasen todos los tests.',
      ),
      h('li', {}, 'Marca el laboratorio como completado y sigue con el siguiente módulo.'),
    ),

    h('h2', {}, 'Por qué los laboratorios van en Colab'),
    h(
      'p',
      {},
      'Spark necesita la máquina virtual de Java, que no existe en el navegador. En lugar de imitarlo, los laboratorios usan Google Colab: PySpark de verdad, gratis y sin instalar nada. Solo necesitas una cuenta de Google.',
    ),

    h('h2', {}, 'Tu progreso'),
    h(
      'p',
      {},
      'No hay cuentas ni servidor. Tu progreso se guarda en este navegador y puedes exportarlo a un archivo desde la página ',
      h('a', { href: '#/progreso' }, 'Progreso'),
      '. Tus notebooks se guardan en tu propio Google Drive.',
    ),

    h('h2', {}, 'Datos'),
    h(
      'ul',
      {},
      h(
        'li',
        {},
        h('strong', {}, 'BigMart Sales: '),
        'ventas de productos por tienda, de un reto de práctica de Analytics Vidhya. Se usa aquí solo con fines educativos.',
      ),
      h(
        'li',
        {},
        h('strong', {}, 'Pilotos de Fórmula 1: '),
        'generado a partir de la API ',
        external('https://github.com/jolpica/jolpica-f1', 'Jolpica-F1'),
        ', sucesora de Ergast.',
      ),
    ),

    isRepoConfigured && h('h2', {}, 'Código'),
    isRepoConfigured &&
      h(
        'p',
        {},
        'El sitio es de código abierto. Si encuentras un error o quieres añadir un módulo, el repositorio está en ',
        external(githubUrl(), 'GitHub'),
        '.',
      ),
  );
}
