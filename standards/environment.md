# Environment Standard

Version: 2.0.0

## Core rules

- .env.example is required when environment variables are used
- every variable must be documented
- no real secrets in .env.example
- placeholder values only

## Variable documentation

Each variable should define:

- name
- purpose
- expected format
- placeholder example
- required or optional

## Python dependencies

- Python dependencies must be listed in requirements.txt
- minimum versions are recommended
