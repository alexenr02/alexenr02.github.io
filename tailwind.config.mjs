/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],

  // Enable dark mode via data-theme attribute
  darkMode: ['selector', '[data-theme="dark"]'],

  theme: {
    extend: {
      // DM Sans (Rokid-like) + mono for technical labels
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'monospace'],
        cursive: ['Tangerine', 'cursive'],
      },

      // Custom colors using CSS variables for theme support
      colors: {
        background: 'var(--color-bg)',
        foreground: 'var(--color-text)',
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
        border: 'var(--color-border)',
        card: 'var(--color-card-bg)',
        navy: 'var(--color-navy)',
        slate: 'var(--color-slate)',
        mist: 'var(--color-mist)',
        signal: 'var(--color-signal)',
      },

      // Typography scale using clamp for responsive sizing
      fontSize: {
        base: 'clamp(1rem, 0.95rem + 0.25vw, 1.125rem)',
        lg: 'clamp(1.125rem, 1rem + 0.5vw, 1.5rem)',
        xl: 'clamp(1.5rem, 1.25rem + 1vw, 2.5rem)',
        '2xl': 'clamp(1.875rem, 1.5rem + 1.5vw, 3rem)',
        '3xl': 'clamp(2.25rem, 1.75rem + 2vw, 4rem)',
      },

      // Animation durations
      transitionDuration: {
        theme: '200ms',
      },

      // Custom spacing for common patterns
      spacing: {
        section: 'clamp(4rem, 8vw, 8rem)',
      },
    },
  },

  plugins: [
    // Typography plugin for prose content (MDX, blog posts, etc.)
    require('@tailwindcss/typography'),
    // Forms plugin for styled form elements
    require('@tailwindcss/forms'),
  ],
};
