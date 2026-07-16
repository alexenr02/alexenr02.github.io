# Hi, I'm Alex

I'm an Embedded Software Engineer based in Nuevo León, México.

What I love most about this job is owning embedded problems end-to-end.
I like the messy parts: squinting at oscilloscope traces during hardware
bring-up, chasing CAN bugs across a multi-ECU bus, building the testbench
before the testbench exists, redesigning a watchdog because v1 was throwing
false alarms, and walking the production line to figure out why a board that
worked yesterday is suddenly bricking units today.

A lot of my work happens in CAN-based systems for industrial,
automotive, and refrigeration platforms — but really, the domain matters less
to me than the chance to take a problem from "the prototype arrived dead in a
shipping container" to "it ships on Monday."

This repo is the source code for my portfolio site.

## Around the web

- Site: [alexenr02.github.io](https://alexenr02.github.io)
- Email: [aelejandro9@proton.me](mailto:aelejandro9@proton.me)
- LinkedIn: [linkedin.com/in/alexenr](https://linkedin.com/in/alexenr)
- Resume: [PDF](public/resume/Resume_AlexE_v1.5.0.pdf)

## Security notes

- No `.env` secrets are used or committed; env files are gitignored.
- `/admin/` is the Sveltia CMS UI. The CMS script is vendored under
  `public/admin/vendor/` with Subresource Integrity. Prefer the OAuth
  authenticator (`base_url` in `config.yml`) over pasting a GitHub PAT.
  Edits use `editorial_workflow` (pull requests) instead of direct commits
  to `main`.
- Security headers: meta CSP/referrer in the site layout (works on GitHub
  Pages). `public/_headers` is also present for Cloudflare Pages / Netlify.
