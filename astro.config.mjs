// @ts-check
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import compress from 'astro-compress';

// https://astro.build/config
export default defineConfig({
  site: 'https://alexenr02.github.io',
  output: 'static',

  integrations: [
    svelte(),
    tailwind({
      // Use custom global styles instead of Tailwind's base
      applyBaseStyles: false,
    }),
    mdx({
      shikiConfig: {
        theme: 'github-dark',
        wrap: true,
      },
    }),
    sitemap(),
    compress({
      css: true,
      html: {
        removeAttributeQuotes: false,
      },
      // Handle images separately with Astro's image optimization
      img: false,
      js: true,
      svg: true,
    }),
  ],

  vite: {
    build: {
      rollupOptions: {
        output: {
          // Manual chunking for better code splitting
          manualChunks: (id) => {
            // Three.js and Threlte (Phase 4+)
            if (id.includes('three') || id.includes('@threlte')) {
              return 'three';
            }
            // GSAP animations
            if (id.includes('gsap')) {
              return 'gsap';
            }
            // Vendor chunks for node_modules
            if (id.includes('node_modules')) {
              return 'vendor';
            }
          },
        },
      },
    },
    optimizeDeps: {
      exclude: ['@sentry/astro'],
    },
  },

  markdown: {
    shikiConfig: {
      theme: 'github-dark',
      wrap: true,
    },
  },

  // Note: contentCollectionCache is now enabled by default in Astro 5.x
});
