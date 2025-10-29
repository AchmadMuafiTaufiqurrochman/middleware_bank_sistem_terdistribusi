# 🔐 Security Guidelines

## Environment Variables

**NEVER commit sensitive data to the repository!**

### Protected Files (in .gitignore)

- `.env` - Contains actual credentials and secrets
- `*.key` - Private keys
- `*.pem` - Certificates
- `credentials.json` - Credential files

### Safe to Commit

- `.env.example` - Template with placeholder values
- Code files without hardcoded secrets

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual credentials (NEVER commit this file!)

3. Use strong SECRET_KEY in production:
   ```python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## Best Practices

✅ Use environment variables for all secrets  
✅ Keep `.env` in `.gitignore`  
✅ Use different secrets for dev/staging/production  
✅ Rotate secrets regularly  
✅ Use HTTPS in production  

❌ Never hardcode secrets in code  
❌ Never commit `.env` file  
❌ Never share secrets in chat/email  
❌ Never log sensitive data  

## Checklist Before Commit

- [ ] No `.env` file in staged changes
- [ ] No hardcoded passwords/API keys in code
- [ ] `.env.example` only has placeholder values
- [ ] Sensitive data is in environment variables
- [ ] `.gitignore` includes all sensitive file patterns
