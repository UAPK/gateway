# Security Policy

## Supported Versions

UAPK Gateway is currently in active development (v0.1.x). We provide security updates for the latest release.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

---

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues via:

1. **GitHub Security Advisories** (preferred)
   - Navigate to: https://github.com/UAPK/core/security/advisories
   - Click "Report a vulnerability"
   - Provide details of the vulnerability

2. **Email** (if you prefer private disclosure)
   - Email: `security@uapk.dev` (monitored)
   - PGP key available on request
   - Include "SECURITY" in the subject line

### What to Include

Please provide:
- Description of the vulnerability
- Steps to reproduce the issue
- Affected versions
- Potential impact assessment
- Suggested fix (if available)

### Response Timeline

- **Initial response:** Within 48 hours
- **Triage and assessment:** Within 5 business days
- **Fix timeline:** Depends on severity (critical issues prioritized)
- **Disclosure:** Coordinated with reporter after fix is available

### Disclosure Policy

We follow **coordinated disclosure**:
1. You report the issue privately
2. We confirm and develop a fix
3. We release the fix and publish a security advisory
4. You receive credit (if desired)

---

## Security Features

UAPK Gateway is designed for high-stakes environments and includes:

### Authentication & Authorization
- **JWT tokens** for human users (HS256, configurable expiration)
- **API keys** for machine clients (hashed with bcrypt)
- **Capability tokens** for scoped delegation (signed JWTs)
- **Role-based access control** (RBAC) for organizations

### Data Protection
- **Secrets encryption** - Fernet (AES-128) encryption for stored secrets
- **Password hashing** - bcrypt with configurable work factor
- **API key hashing** - One-way hash, full key shown only at creation
- **Environment-based secrets** - All sensitive config in `.env` (gitignored)

### Audit & Integrity
- **Tamper-evident logs** - Hash-chained interaction records
- **Gateway signatures** - Ed25519 signatures on log entries
- **Chain verification** - Standalone verification scripts
- **Immutable records** - No deletion, only archival

### Network Security
- **CORS controls** - Configurable allowed origins
- **Connector allowlists** - Restrict webhook/HTTP destinations
- **TLS/HTTPS** - Required in production (via Caddy or reverse proxy)
- **Rate limiting** - Planned (coming soon)

### Operational Security
- **Safe defaults** - Mock AI provider, sensitive data disabled
- **Security headers** - Helmet-style headers (coming soon)
- **Input validation** - Pydantic schemas for all inputs
- **SQL injection protection** - SQLAlchemy ORM (parameterized queries)

---

## Security Best Practices

### For Operators

1. **Change default credentials immediately**
   ```bash
   # After bootstrap, change admin password
   curl -X POST http://localhost:8000/api/v1/auth/change-password \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"old_password": "changeme123", "new_password": "..."}'
   ```

2. **Use strong SECRET_KEY**
   ```bash
   # Generate new secret
   openssl rand -hex 32
   # Update .env
   ```

3. **Rotate API keys regularly**
   - Revoke old keys: `POST /api/v1/api-keys/{id}/revoke`
   - Create new keys with minimal scopes

4. **Enable HTTPS in production**
   - Use Caddy (included in `docker-compose.prod.yml`)
   - Or use a reverse proxy (nginx, Traefik, etc.)

5. **Backup encryption keys**
   - `SECRET_KEY` (JWT signing)
   - `GATEWAY_FERNET_KEY` (secrets encryption)
   - Store securely (vault, KMS, encrypted backup)

6. **Monitor logs**
   - Review interaction records regularly
   - Export audit bundles for compliance
   - Verify chain integrity: `python scripts/verify_log_chain.py`

7. **Limit connector destinations**
   ```env
   # In .env
   GATEWAY_ALLOWED_WEBHOOK_DOMAINS=["example.com", "api.trusted.com"]
   ```

8. **Review manifests before activation**
   - Validate manifest schemas
   - Audit action allowlists
   - Verify budget limits

### For Developers

1. **Never commit secrets**
   - `.env` is in `.gitignore` - keep it there
   - Use `.env.example` for templates

2. **Run security checks**
   ```bash
   make typecheck  # Type safety
   make lint       # Security linters
   make test       # Security test cases
   ```

3. **Review dependencies**
   ```bash
   pip install safety
   safety check --json
   ```

4. **Follow secure coding practices**
   - Validate all inputs (use Pydantic)
   - Avoid eval/exec
   - Use parameterized queries (SQLAlchemy)
   - No shell injection (careful with subprocess)

5. **Test authentication/authorization**
   - Write tests for permission checks
   - Verify API key scoping
   - Test capability token validation

---

## Threat Model

See `docs/security/threat-model.md` for detailed threat analysis.

### In Scope
- API authentication bypass
- Authorization violations (privilege escalation)
- SQL injection
- XSS in operator UI
- Log tampering or deletion
- Secret exposure
- Denial of service (application-level)

### Out of Scope (for vulnerability reports)
- Physical access to servers
- Social engineering
- DDoS (network-level)
- Vulnerabilities in third-party dependencies (report to upstream)
- Theoretical attacks requiring impractical resources

---

## Security Contacts

### Primary Contact
- **Email:** `security@uapk.dev`
- **Response SLA:** 48 hours

### Commercial/Enterprise Security
For customers with support contracts:
- Priority response channel (see your contract)
- Dedicated security contact

### Open Source Community
- GitHub Security Advisories: https://github.com/UAPK/core/security/advisories
- Discussions: https://github.com/UAPK/core/discussions

---

## Security Advisories

Published security advisories will be listed here:
- [GitHub Security Advisories](https://github.com/UAPK/core/security/advisories)

**Subscribe:** Watch this repository and enable "Security alerts" notifications.

---

## Compliance & Certifications

### Current Status
- **SOC2:** Planned (target: 2025 Q2)
- **ISO 27001:** Under consideration
- **GDPR:** Self-hosted deployment supports GDPR compliance (data residency)

### Compliance Documentation
See `docs/security/` for:
- Data handling policies
- Key management procedures
- Audit log retention
- Incident response runbooks

---

## Bug Bounty Program

**Status:** Not yet active

We're evaluating a bug bounty program for 2025. If you find a vulnerability, we'll:
- Acknowledge your contribution publicly (if desired)
- Provide credit in security advisories
- Consider financial rewards for critical findings (case-by-case)

---

## Acknowledgments

We thank the security researchers who responsibly disclose vulnerabilities:

- *No vulnerabilities reported yet*

---

## Legal Disclaimer

This software is provided "as is" without warranty of any kind. See `LICENSE` for full terms.

You are responsible for:
- Securing your deployment
- Compliance with applicable laws and regulations
- Data protection and privacy
- Incident response

UAPK Gateway is a tool for governance and audit, but **you** own the compliance outcomes.

---

**Last updated:** 2025-12-15
