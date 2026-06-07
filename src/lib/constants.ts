// Site-wide constants and configuration
// SITE and SOCIAL_LINKS are sourced from src/content/site/site.json so the
// Sveltia CMS admin can edit them without touching code.

import siteData from '../content/site/site.json';

export const SITE = {
  name: siteData.name,
  title: siteData.title,
  description: siteData.description,
  url: siteData.url,
  author: siteData.author,
  email: siteData.email,
} as const;

export const SOCIAL_LINKS = {
  github: siteData.social.github,
  linkedin: siteData.social.linkedin,
} as const;

export const NAV_ITEMS = [
  { href: '/#home', label: 'Home' },
  { href: '/#about', label: 'About' },
  { href: '/#projects', label: 'Projects' },
  { href: '/#experience', label: 'Work Experience' },
  { href: '/#lab', label: 'Lab' },
  { href: '/#contact', label: 'Contact' },
] as const;
