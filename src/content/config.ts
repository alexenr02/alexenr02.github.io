// Content collections schema configuration
// Defines TypeScript schemas for MDX content

import { defineCollection, z } from 'astro:content';

// Projects collection schema
const projects = defineCollection({
  type: 'content',
  schema: ({ image }) =>
    z.object({
      // Basic information
      title: z.string(),
      description: z.string(),
      category: z.enum(['Software', 'Embedded', 'Full-Stack']),

      // Technical details
      techStack: z.array(z.string()),
      tags: z.array(z.string()).optional(),

      // Media
      thumbnail: image(),
      ogImage: z.string().optional(), // Manual OG image path per project

      // Links
      githubUrl: z.string().url().optional(),
      liveUrl: z.string().url().optional(),
      youtubeUrl: z.string().url().optional(),

      // Dates and status
      date: z.date(),
      lastUpdated: z.date().optional(),

      // Organization
      featured: z.boolean().default(false),
      draft: z.boolean().default(false),
      archived: z.boolean().default(false),
      order: z.number().optional(), // Manual ordering
    }),
});

// Work experience collection schema
const experience = defineCollection({
  type: 'content',
  schema: z.object({
    // Company information
    company: z.string(),
    position: z.string(),
    location: z.string().optional(),

    // Dates
    startDate: z.date(),
    endDate: z.date().optional(), // Optional for current position

    // Description
    description: z.string(),
    responsibilities: z.array(z.string()).optional(),
    achievements: z.array(z.string()).optional(),

    // Technical details
    technologies: z.array(z.string()).optional(),

    // Organization
    order: z.number().optional(),
    featured: z.boolean().default(false),
  }),
});

// Static pages collection schema (privacy policy, etc.)
const pages = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    lastUpdated: z.date(),
  }),
});

// Export collections
export const collections = {
  projects,
  experience,
  pages,
};
