# Project Agent Rules

Do not read, open, inspect, summarize, quote, print, or expose secret-bearing files.

Treat at least the following as restricted:
- .env
- .env.local
- .env.*.local
- .secrets
- credentials*
- *.pem
- *.key
- *.pfx
- *.p12
- id_rsa
- id_ed25519
- auth.json

If configuration is needed:
- use `.env.example` when available
- infer variable names from source code
- ask only for missing variable names or formats
- never request or reveal secret values unless the user explicitly asks for secret debugging

Allowed work:
- development
- refactoring
- debugging
- testing
- documentation
- workflow creation

Deployment packaging rules:
- Create and maintain a local deployment folder structure with:
	- deployment/full_deployment/
	- deployment/delta_deployment/
- Only include files that are actually hosted productively on the web server.
- Exclude non-productive repository artifacts such as README files, notes, plans, and local helper docs.
- full_deployment must contain the complete current production upload set.
- delta_deployment must contain only the files changed in the latest change set to upload as delta.
- Before preparing a new deployment package, clear both deployment folders and repopulate them from scratch.
- These deployment folders are local FTP handover folders and must never be committed to GitHub.
