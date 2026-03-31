// Site-wide constants and configuration

export const SITE = {
  name: 'Alejandro Enriquez',
  title: 'Alejandro Enriquez - Embedded Software Engineer',
  description:
    'Embedded Software Engineer with experience across industrial, automotive, and refrigeration systems. Skilled in C++ development, RTOS (embOS, MQX), and CAN/J1939 communication.',
  url: 'https://yourdomain.com', // Update with actual domain when available
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
