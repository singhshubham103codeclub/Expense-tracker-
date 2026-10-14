
---
name: seed-expense
description: Seed the Spendly development database with realistic sample expense data.
---

# Seed Expense Data

When `/seed-expense` is invoked:

1. Inspect `@app.py`, the existing database models, and configuration.
2. Identify the existing database initialization and seeding patterns.
3. Create a minimal, reusable seed script or extend the existing seeder to insert sample expenses.
4. Use the existing `Expense` and `User` models. Follow their actual schemas and relationships.
5. Include realistic expense titles, categories, amounts, dates, and notes where supported by the schema.
6. Associate seeded expenses with an appropriate existing test/development user. Create a user only if the existing setup requires it.
7. Make the operation idempotent so rerunning the command does not create duplicate sample expenses.
8. Never delete, overwrite, or modify existing user expenses.
9. Never seed production data. Require an explicit development/test environment and fail safely if the environment is unknown.
10. Use existing dependencies and coding conventions. Avoid unnecessary changes.
11. Run relevant tests or verification checks and report how many records were created or skipped.

## Constraints

- Do not modify unrelated application code.
- Inspect the project before making changes.
- Do not assume model fields, database configuration, or environment variables; verify them first.
- If the database setup is incomplete, explain what is missing instead of inventing a schema.
- Summarize the files changed and verification results.---
---
