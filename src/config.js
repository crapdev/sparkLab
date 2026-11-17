import siteConfig from '../site.config.json';

/** Site-wide settings. Deployment values live in site.config.json. */
export const SITE = Object.freeze({
  ...siteConfig,
  quizPassRatio: 0.7,
});

/** False while site.config.json still has the placeholder repository. */
export const isRepoConfigured = !SITE.githubRepo.includes('YOUR_');

/** Link that opens a notebook from the GitHub repository in Google Colab. */
export function colabUrl(labPath, file = 'lab.ipynb') {
  return `https://colab.research.google.com/github/${SITE.githubRepo}/blob/${SITE.githubBranch}/${labPath}/${file}`;
}

/** Link to a file or folder of the repository on GitHub. */
export function githubUrl(path = '') {
  const base = `https://github.com/${SITE.githubRepo}`;
  return path ? `${base}/blob/${SITE.githubBranch}/${path}` : base;
}
