# Security Standard

Version: 2.0.0

## Minimum sections for SECURITY.md

- Supported Versions
- Vulnerability Reporting
- Secret Handling
- Production Hardening
- Backup Strategy
- Installer Policy
- Disclosure Policy
- Response Targets

## Secret handling

- no secrets in repository
- runtime secrets only via environment or secret store
- GitHub workflows use only secrets context

## Production hardening

- HTTPS enforced
- secure headers enabled
- debug output disabled in production

## Security contact path

Recommended for public web projects:

- /.well-known/security.txt
