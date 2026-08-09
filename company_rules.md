# Corporate Engineering Guidelines & Security Policy

## Rule 101: Database Queries
- Direct string concatenation or formatted f-strings in SQL queries are strictly forbidden.
- Always use parameterized queries or an ORM like SQLAlchemy to prevent SQL injection.

## Rule 102: Credential & Secret Management
- API keys, passwords, and private tokens must never be hardcoded into source files.
- All secrets must be loaded dynamically using environment variables or Secret Managers (`os.getenv`).

## Rule 103: Resource Management
- All database connections and file descriptors must use context managers (`with` blocks) to guarantee proper cleanup.