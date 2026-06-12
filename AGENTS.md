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
