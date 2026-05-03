// Site-wide constants and configuration

export const SITE = {
  name: 'Alejandro Enriquez',
  title: 'Alejandro Enriquez - Embedded Software Engineer',
  description:
    'Embedded Software Engineer with 4 years developing safety-critical firmware on CAN-based multi-ECU architectures. Proven ability to own problems end-to-end, from hardware bring-up to manufacturing support. Experienced in V-model, HIL, and cross-site collaboration.',
  url: 'https://alexenr02.github.io',
  author: 'Alejandro Enriquez',
  email: 'aelejandro9@proton.me',
} as const;

export const SOCIAL_LINKS = {
  github: 'https://github.com/alexenr02',
  linkedin: 'https://www.linkedin.com/in/alexenr/',
} as const;

export const NAV_ITEMS = [
  { href: '/', label: 'Home' },
  { href: '/#about', label: 'About' },
  { href: '/#projects', label: 'Projects' },
  { href: '/#experience', label: 'Work Experience' },
  { href: '/#lab', label: 'Lab' },
  { href: '/#contact', label: 'Contact' },
] as const;
