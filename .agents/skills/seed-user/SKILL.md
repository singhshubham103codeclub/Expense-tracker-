---
name: seed-user
description: Create a sample development user for the Spendly application.
---

# Seed User

When `/seed-user` is invoked:

1. Inspect `@app.py`, the existing `User` model, database configuration, and any existing seed scripts.
2. Verify the actual user schema, required fields, authentication mechanism, and password-hashing implementation.
3. Use the existing `User` model and database initialization patterns. Do not invent fields or modify the schema unnecessarily.
4. Require an explicitly configured development or test environment. Never create seed users in production or when the environment is unknown.
5. Create one realistic sample development user using valid required fields.
6. Make the operation idempotent. Check whether the user already exists using the appropriate unique field before creating one.
7. Never overwrite, reset, or modify an existing user's details or password.
8. If authentication requires a password, use the project's existing secure password-hashing method. Never store plaintext passwords.
9. Avoid logging passwords, tokens, or other secrets. Do not hardcode production credentials.
10. Reuse existing dependencies and conventions. Avoid unrelated code changes.
11. Run relevant tests or verification checks.
12. Report whether the user was created or already existed, and list the files changed.

## Constraints

- Do not delete or modify existing users.
- Do not create duplicate users.
- Do not assume model fields or authentication requirements; inspect the project first.
- If the database or user model is not ready, explain what is missing instead of inventing a solution.