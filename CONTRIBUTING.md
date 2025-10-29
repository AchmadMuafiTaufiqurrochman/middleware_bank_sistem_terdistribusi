# Contributing Guide

## Setup Development Environment

1. Clone repository
2. Create virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment template:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` with your local configuration

6. Create database:
   ```bash
   mysql -u root -p < scripts/create_database.sql
   ```

7. Run migrations:
   ```bash
   python scripts/migration.py
   ```

8. Run server:
   ```bash
   python run.py
   ```

## Testing

- Health check: http://localhost:8001/health
- API docs: http://localhost:8001/docs
- Test database: `python scripts/test_connection.py`
- Test service: `python scripts/test_service_connection.py`

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions small and focused

## Security

**NEVER commit sensitive data!** See [SECURITY.md](SECURITY.md)

## Pull Request

1. Create feature branch
2. Make changes
3. Test locally
4. Commit with clear message
5. Push and create PR
