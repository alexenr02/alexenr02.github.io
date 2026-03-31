# Portfolio Website

**Modern portfolio website for embedded systems and software engineer**

[![Deploy to GitHub Pages](https://github.com/alexenr02/alexenr02.github.io/actions/workflows/deploy.yml/badge.svg)](https://github.com/alexenr02/alexenr02.github.io/actions/workflows/deploy.yml)

---

## Quick Links

- **Documentation:** [docs/INDEX.md](docs/INDEX.md)
- **Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Progress:** [docs/PROGRESS_TRACKER.md](docs/PROGRESS_TRACKER.md)

---

## Project Overview

This is a high-performance, accessible portfolio website built with modern web technologies. The site showcases embedded systems projects, software engineering work, and interactive demonstrations.

**Key Features:**

- Dark/Light theme with system preference detection
- Accessible (WCAG AA compliant)
- Performance-optimized (Lighthouse 90+ target)
- SEO-ready with structured data
- Privacy-focused (no analytics, no tracking)
- Responsive and mobile-first design

---

## Tech Stack

### Core Framework

- **Astro 5.x** - Static site generator with island architecture
- **Svelte 5.x** - Interactive components with small bundles (required by Astro 5)
- **TypeScript 5.x** - Type safety with strict mode
- **Tailwind CSS 3.x** - Utility-first styling

### Content & Styling

- **MDX** - Markdown with interactive components
- **Shiki** - Syntax highlighting (built into Astro)
- **Geist Fonts** - Variable fonts (Sans + Mono)
- **Lucide Svelte** - Icon library

### Development Tools

- **ESLint** - Code quality
- **Prettier** - Code formatting
- **Vite** - Build tool (bundled with Astro)

### Deployment & Services

- **GitHub Pages** - Hosting and deployment
- **GitHub Actions** - CI/CD pipeline
- **Cloudflare Turnstile** - Spam protection (contact form)
- **Sentry** - Error tracking

### Future Enhancements (Phase 4+)

- **@threlte/core** - Three.js wrapper for Svelte
- **GSAP** - Advanced animations
- Interactive lab experiments and games

---

## Project Structure

```
portfolio/
├── docs/                      # Complete documentation
│   ├── INDEX.md              # Documentation navigation
│   ├── ARCHITECTURE.md       # Technical architecture (2,465 lines)
│   ├── PROGRESS_TRACKER.md   # Progress and decisions
│   ├── FILE_GUIDE.md         # Documentation guide
│   └── PLAN_UPDATE_SUMMARY.md # Architecture audit
├── src/
│   ├── pages/                # Page routes
│   │   └── index.astro      # Homepage
│   ├── styles/              # Global styles
│   │   ├── global.css       # Base styles + fonts
│   │   └── themes.css       # Theme variables
│   ├── layouts/             # Layout components (Phase 1)
│   ├── components/          # Reusable components (Phase 1+)
│   ├── content/             # MDX content collections (Phase 3)
│   └── lib/                 # Utilities and helpers (Phase 1+)
├── public/
│   ├── fonts/               # Geist Sans + Geist Mono
│   └── favicon.svg
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI
├── astro.config.mjs         # Astro configuration
├── tailwind.config.mjs      # Tailwind configuration
├── tsconfig.json            # TypeScript config (strict mode)
├── .eslintrc.cjs            # ESLint rules
├── .prettierrc              # Prettier config
└── .browserslistrc          # Browser targets
```

---

## Getting Started

### Prerequisites

- **Node.js:** 20.x or higher
- **npm:** 10.x or higher
- **Git:** For version control

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/alexenr02/alexenr02.github.io.git
   cd alexenr02.github.io
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

4. **Start development server:**

   ```bash
   npm run dev
   ```

   The site will be available at `http://localhost:4321`

### Available Commands

| Command            | Description                       |
| ------------------ | --------------------------------- |
| `npm run dev`      | Start development server          |
| `npm run build`    | Build for production              |
| `npm run preview`  | Preview production build locally  |
| `npm run lint`     | Run ESLint and Prettier checks    |
| `npm run lint:fix` | Fix linting and formatting issues |
| `npm run format`   | Format code with Prettier         |

---

## Development Workflow

### Branch Strategy: GitHub Flow

```
main (production)
  ├── feature/hero-section
  ├── feature/projects
  └── feature/contact-form
```

**Workflow:**

1. Create feature branch from `main`
2. Develop and test locally
3. Push branch and create pull request
4. Review and merge to `main`
5. GitHub Actions automatically builds and deploys to GitHub Pages

### Making Changes

1. **Create a feature branch:**

   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes and test:**

   ```bash
   npm run dev
   # Test your changes
   npm run lint
   ```

3. **Commit your changes:**

   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub
   ```

---

## Implementation Phases

The project follows a 10-phase implementation plan. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed requirements.

### Current Status

- ✅ **Phase 0:** Project Setup & Tooling (Complete)
- 🔵 **Phase 1:** Foundation & Theme System (Ready to start)
- ⬜ **Phase 2:** Static Sections
- ⬜ **Phase 3:** Projects Section
- ⬜ **Phase 4:** Interactive Lab (Measurement-first)
- ⬜ **Phase 5:** Enhanced SEO & Accessibility
- ⬜ **Phase 6:** Performance Optimization
- ⬜ **Phase 7:** Testing & Quality Assurance
- ⬜ **Phase 8:** Analytics & Monitoring
- ⬜ **Phase 9:** Documentation & Deployment
- ⬜ **Phase 10:** Post-Launch Enhancements (Optional)

---

## Environment Variables

Create a `.env` file in the project root with these values:

```bash
# Cloudflare Turnstile (for contact form spam protection)
PUBLIC_TURNSTILE_SITE_KEY=your_site_key_here

# Sentry Error Tracking
PUBLIC_SENTRY_DSN=your_sentry_dsn_here
SENTRY_AUTH_TOKEN=your_auth_token_here
SENTRY_ORG=your_org
SENTRY_PROJECT=your_project

# Site Configuration
PUBLIC_SITE_URL=https://alexenr02.github.io
```

**Where to get API keys:**

- **Turnstile:** [Cloudflare Turnstile](https://www.cloudflare.com/products/turnstile/)
- **Sentry:** [Sentry.io](https://sentry.io/)

---

## Key Architecture Decisions

### Why Astro 5.x + Svelte 5.x?

While the original plan specified Astro 4.x + Svelte 4.x, we're using the latest versions for:

**Astro 5.x Benefits:**

- Improved performance and build times
- Better content collection caching (enabled by default)
- Enhanced type safety
- Latest features and bug fixes
- Active maintenance and support

**Svelte 5.x Benefits:**

- Required by Astro 5.x (compiler API compatibility)
- Improved reactivity with runes system
- Better TypeScript support
- Smaller bundle sizes
- More intuitive component logic

**Compatibility Note:** Astro 5.x requires Svelte 5.x due to changes in the Svelte compiler API. Using both latest versions ensures full compatibility and best performance.

### Performance First

Heavy features (Three.js, GSAP, interactive labs) are deferred to Phase 4+ with a measurement-first approach:

1. Build core site (Phases 1-3)
2. Measure baseline performance
3. Add features incrementally
4. Measure impact before merging

**Performance Targets:**

- Lighthouse Score: 90+
- Initial Bundle: < 200KB gzipped
- Total JS: < 300KB gzipped
- LCP: < 2.5s
- CLS: < 0.1

### Privacy & Security

- **No analytics** - zero tracking, no cookies, fully GDPR-compliant
- **Spam protection** with honeypot + Cloudflare Turnstile
- **Privacy policy page** documenting all data collection
- **No unnecessary tracking** or third-party scripts

---

## Browser Support

```
> 0.5%
last 2 versions
not dead
Firefox ESR
iOS >= 12
Android >= 6
```

**No IE11 support** - EOL 2022, significant bundle savings

---

## Accessibility Commitment

This site aims for **WCAG AA compliance** with:

- Semantic HTML structure
- Skip to main content link
- Keyboard navigation support
- ARIA labels and live regions
- Color contrast 4.5:1 minimum
- Focus indicators (3px minimum)
- Touch targets 44x44px minimum
- `prefers-reduced-motion` support
- `prefers-contrast: high` support
- Screen reader compatibility

---

## Testing Strategy

### Phase 0-3: Manual + Linting

- ESLint for code quality
- Prettier for formatting
- Manual browser testing
- Manual accessibility checks

### Phase 7: Unit Tests (Vitest)

- Utility functions
- Component logic
- Validation helpers

### Phase 8: E2E Tests (Playwright)

- Critical user flows
- Form submissions
- Navigation
- Theme switching

### Phase 10: Automated Testing (Optional)

- Lighthouse CI (warnings only)
- Accessibility automation
- Performance monitoring

---

## Deployment

### GitHub Pages + GitHub Actions

The site deploys automatically via GitHub Actions on every push to `main`:

- **Live URL:** [alexenr02.github.io](https://alexenr02.github.io)
- **Workflow:** `.github/workflows/deploy.yml`
- **Build command:** `npm run build`
- **Publish directory:** `dist`

The workflow installs dependencies, runs `npm run build`, and uploads the
`dist/` output directly to GitHub Pages — no Jekyll involved.

### Contact Form

Contact is handled via direct email (`mailto:`) link.
A form with spam protection (Cloudflare Turnstile) will be added in Phase 2.

---

## Documentation

### Complete Documentation in `docs/` Folder

| File                       | Size | Purpose                      |
| -------------------------- | ---- | ---------------------------- |
| **INDEX.md**               | 11KB | Documentation navigation     |
| **ARCHITECTURE.md**        | 65KB | Complete technical guide     |
| **PROGRESS_TRACKER.md**    | 14KB | Track progress and decisions |
| **FILE_GUIDE.md**          | 12KB | Documentation usage guide    |
| **PLAN_UPDATE_SUMMARY.md** | 8KB  | Architecture audit summary   |

**Start with:** [docs/INDEX.md](docs/INDEX.md)

---

## Contributing

This is a personal portfolio project. If you notice bugs or have suggestions:

1. Check existing issues
2. Open a new issue with details
3. Submit a pull request (if applicable)

---

## License

See [LICENSE](LICENSE) file for details.

---

## Contact

**Email:** aelejandro9@proton.me

**Social Links:**

- GitHub: [alexenr02](https://github.com/alexenr02)
- LinkedIn: [alexenr](https://linkedin.com/in/alexenr)

---

## Maintenance

### Dependency Updates

Dependencies are updated manually on a quarterly basis to avoid unnecessary churn and ensure stability.

**Update schedule:**

- January, April, July, October

**Update process:**

1. Review changelogs for breaking changes
2. Update dependencies incrementally
3. Test thoroughly
4. Deploy to preview
5. Monitor for issues

### Performance Monitoring

- **Sentry:** Error tracking and performance monitoring
- **Lighthouse CI:** Performance regression detection (Phase 10)

---

## Acknowledgments

- **Fonts:** [Geist](https://vercel.com/font) by Vercel
- **Icons:** [Lucide](https://lucide.dev/)
- **Framework:** [Astro](https://astro.build/)
- **UI Library:** [Svelte](https://svelte.dev/)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/)

---

## Project Status

**Current Phase:** Phase 1 - Foundation & Theme System  
**Last Updated:** 2026-01-20  
**Status:** Active Development

For detailed progress tracking, see [docs/PROGRESS_TRACKER.md](docs/PROGRESS_TRACKER.md)

---

**Ready to build something amazing! 🚀**
