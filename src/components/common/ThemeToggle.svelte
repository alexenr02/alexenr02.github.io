<script lang="ts">
  /* eslint-env browser */
  // Theme toggle component using Svelte 5 runes
  // Handles dark/light mode switching with system preference detection and persistence

  import { onMount } from 'svelte';
  import { Sun, Moon } from 'lucide-svelte';

  // Svelte 5 reactive state
  let theme = $state('light');

  onMount(() => {
    // Check localStorage and system preference
    const stored = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Apply stored theme or system preference
    const initialTheme = stored || (prefersDark ? 'dark' : 'light');
    theme = initialTheme;
    applyTheme(initialTheme);

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('theme')) {
        // Only auto-switch if user hasn't set a preference
        const newTheme = e.matches ? 'dark' : 'light';
        theme = newTheme;
        applyTheme(newTheme);
      }
    };

    mediaQuery.addEventListener('change', handleChange);

    // Cleanup listener on component destroy
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  });

  function applyTheme(newTheme: string) {
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  }

  function toggleTheme() {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    theme = newTheme;
    applyTheme(newTheme);
  }
</script>

<button
  onclick={toggleTheme}
  aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
  class="theme-toggle rounded-lg p-2 transition-colors hover:bg-gray-200 dark:hover:bg-gray-800"
  title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
>
  {#if theme === 'light'}
    <Moon class="h-5 w-5" aria-hidden="true" />
  {:else}
    <Sun class="h-5 w-5" aria-hidden="true" />
  {/if}
</button>

<style>
  /* Additional styles for theme toggle button */
  .theme-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border: none;
    background: transparent;
    color: var(--color-text);
  }

  .theme-toggle:focus-visible {
    outline: 3px solid var(--color-focus);
    outline-offset: 2px;
  }
</style>
