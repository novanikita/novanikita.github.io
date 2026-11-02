// @ts-check
import { defineConfig } from 'astro/config';

import mdx from '@astrojs/mdx';

export default defineConfig({
  site: 'https://novanikita.github.io',

  // The same addresses as the old site: /wibes.html, /en/wibes.html, /en/ (en/index.html)
  build: { format: 'preserve' },

  integrations: [mdx()],
});