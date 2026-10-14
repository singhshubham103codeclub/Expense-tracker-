---
name: create-feature-spec
description: Create a detailed feature specification document from a feature idea before implementation.
---

# Create Feature Specification

When `/create-feature-spec` is invoked, take the feature idea provided by the user as input and create a detailed, project-specific specification document for implementing that feature.

## Input

The user may provide:
- A short feature name
- A feature description

Example:
`/create-feature-spec Add monthly expense reports with category-wise charts and date filters.`

If no feature idea is provided, ask the user what feature they want to build. If essential requirements are unclear, ask focused follow-up questions before finalizing the specification.
folder structure:   
expense-tracker/
├── .agents/
│        
└── specs/
    ├── monthly-expense-reports.md
    ├── user-profile-editing.md
    └── monthly-budget-alerts.md

## Workflow

1. Inspect the project structure and relevant existing files before writing the specification.
2. Understand the current architecture, framework, routes, templates, frontend assets, database models, authentication, and testing setup where applicable.
3. Identify existing patterns and reusable components relevant to the requested feature.
4. Clearly distinguish verified existing functionality from assumptions and proposed changes.
5. Analyze the feature's purpose, target users, problem statement, scope, dependencies, and expected behavior.
6. Identify relevant UI changes, backend logic, API or route changes, data-model changes, validation, authorization, security, error handling, and edge cases as applicable.
7. Define acceptance criteria that can be tested objectively.
8. Identify required tests, implementation steps, risks, dependencies, and unresolved questions.
9. Avoid proposing unnecessary technologies, dependencies, or architectural changes.
10. Generate the specification document without implementing the feature or modifying application code.

## Specification Document

Create a Markdown document in the project root's `specs/` directory.

Use a descriptive, filesystem-safe filename based on the feature name, such as:

`specs/monthly-expense-reports.md`

Include these sections where relevant:

1. Feature title and summary
2. Problem statement
3. Goals and expected outcomes
4. Target users and user stories
5. Functional requirements
6. Non-functional requirements
7. UI/UX behavior and user flows
8. Backend, routes, and API requirements
9. Database and data-model changes
10. Validation, authorization, and security
11. Error states and edge cases
12. Acceptance criteria
13. Testing and verification plan
14. Implementation plan broken into small, ordered tasks
15. Relevant existing files and proposed file changes
16. Dependencies, risks, assumptions, and open questions

Adapt the document to the feature. Omit irrelevant sections rather than inventing requirements.

## File and Safety Rules

- Create the `specs/` directory if it does not exist.
- Inspect existing specifications before creating a new one.
- Never overwrite an existing specification. If a filename conflicts, choose a distinct filename or ask the user.
- Do not modify application code, database data, environment files, or unrelated documentation.
- Do not install dependencies or implement the feature.
- Never invent existing files, model fields, routes, or capabilities. Verify them first.
- Clearly label assumptions and unresolved decisions.
- Keep the specification practical, actionable, and consistent with the current project.

## Completion Report

After creating the document, report:
- The exact specification file path
- A short summary of the feature requirements
- Important assumptions or open questions
- The recommended first implementation task

Do not start implementation unless the user explicitly requests it.