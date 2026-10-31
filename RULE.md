# FreshLoop — Shared AI Coding Agent Rules

> Repository-wide development rules for all FreshLoop contributors and their AI coding agents. This file defines **how to work**, not **what tasks to do**. Current assignments, priorities, deadlines, and milestones are maintained separately.

## 1. Project Context

FreshLoop is a real-time predictive inventory grocery platform for a small group of mini-marts.

**Core technology stack**
- Frontend: Next.js, React, TypeScript, Tailwind CSS.
- Backend: Python, FastAPI, SQLAlchemy.
- Database: PostgreSQL, Alembic migrations.
- Cache: Redis.
- Recommendation: Python-based recommendation logic.
- Real-time updates: Server-Sent Events (SSE), where applicable.

Treat the repository's actual code and configuration as the source of truth for the current implementation. Do not assume a component exists, is complete, or is missing without checking. Follow the latest approved task assignment separately provided by the team; this document does not define deliverables.

## 2. Agent Session Initialization

Before changing code, the agent must:
1. Read this file and relevant repository documentation.
2. Ask for the current contributor's name, role, and task if not already provided.
3. Inspect the relevant files and existing implementation.
4. Explain the proposed approach and identify any cross-module impact.
5. Clarify ambiguous requirements instead of inventing business rules.

The contributor's role provides context; it is **not** a directory-level permission boundary.

## 3. Team Collaboration and Task-Based Ownership

- Hiếu: Team Leader & Full-Stack Developer.
- Tiến: Backend Developer.
- Thắng: Database Developer.
- Ân: Recommendation & Cache Developer.

All contributors may modify frontend, backend, database, recommendation, or shared configuration files **when necessary for their assigned work**.

- Keep changes focused on the current task; avoid unrelated refactoring.
- Read dependencies across modules as needed.
- Before changing a shared API contract, database schema, migration history, common configuration, or core architecture, explain the impact and obtain approval from the contributor; coordinate with affected teammates.
- Never overwrite or discard another contributor's unfinished work.
- If simultaneous changes to the same files are likely, flag the conflict risk before editing.
- Do not claim that role declarations enforce GitHub access permissions.

## 4. Git and GitHub Workflow

- `main` is the stable branch; `dev` is the team's shared development branch.
- Work on `dev` under the team's agreed workflow. Do not create feature branches unless explicitly requested.
- Check `git status` and synchronize with the remote before starting work; do not discard uncommitted changes.
- Stage only relevant files and use descriptive, scoped commit messages.
- Never force-push or rewrite shared branch history.
- Never commit secrets, local `.env` files, generated caches, or unrelated build artifacts.
- **AI agents must not commit, push, merge, reset, delete branches, or perform other destructive Git actions without explicit user approval.**
- Changes are promoted from `dev` to `main` only after team review and appropriate testing.

## 5. Architecture and Integration

- Prefer the existing project architecture, naming conventions, and folder structure.
- Reuse established modules and utilities before introducing new abstractions or dependencies.
- Keep frontend, API, data-access, recommendation, and caching responsibilities reasonably separated.
- Preserve backwards compatibility with existing consumers when possible.
- Document API request/response changes and coordinate dependent frontend/backend code.
- Do not assume how warehouse assignment, stock availability, reservation, pricing, or order states work; use agreed contracts or ask.
- Avoid overengineering and speculative features.

## 6. Frontend Standards

- Follow the repository's Next.js App Router, TypeScript, and Tailwind conventions.
- Prefer typed props and reusable components where reuse is justified.
- Handle loading, empty, and error states for data-dependent UI.
- Keep UI accessible, responsive, and consistent with the existing design system.
- Separate API calls and data models from presentation where practical.
- Do not silently replace working functionality with mock data or change approved branding.

## 7. Backend and API Standards

- Follow existing FastAPI routing, schema, service, and dependency patterns.
- Validate request data and return consistent HTTP errors.
- Avoid leaking internal exceptions, secrets, or sensitive data to API responses.
- Keep business logic out of route handlers when a service layer already exists.
- Use safe database sessions and transactions; avoid raw SQL string interpolation.
- Document endpoint and schema changes needed by other modules.

## 8. Database and Migration Standards

- Treat existing SQLAlchemy models and Alembic migration history carefully.
- Do not modify or replace committed migrations without discussing the impact.
- Use new migrations for approved schema changes, following project conventions.
- Preserve referential integrity and data consistency.
- Never drop tables, truncate data, reset databases, or run destructive migrations without explicit approval.
- Use reproducible, non-sensitive development seed data.

## 9. Recommendation, Redis, and Real-Time Standards

- Keep recommendation logic testable and separate from API transport code.
- Handle missing purchase history and cold-start cases gracefully.
- Use documented cache keys and configurable TTL values; consider invalidation when data changes.
- Treat Redis as a cache unless the approved architecture specifies otherwise.
- For SSE, handle client disconnects and resource cleanup; do not promise real-time guarantees without tests.
- Do not invent model accuracy, latency, or availability results.

## 10. Security and Privacy

- Never hardcode credentials, tokens, passwords, or connection secrets.
- Use environment variables and maintain safe example configuration files.
- Validate untrusted inputs and apply authorization where required.
- Avoid exposing personal data in logs, screenshots, test fixtures, or commits.
- Do not disable security checks or weaken access controls merely to make a feature work.
- Report suspected vulnerabilities and propose a safe fix.

## 11. Testing and Quality Gates

- Run relevant available tests, linting, and build checks after changes when feasible.
- Add or update tests for changed behavior where practical.
- Do not claim tests passed unless they actually ran and passed.
- If checks cannot run, explain why and provide reproducible verification steps.
- Preserve existing behavior unless a change is explicitly required.

## 12. Communication and Change Reporting

- Explain important assumptions, especially for cross-module changes.
- Prefer small, reviewable changes with clear reasoning.
- At the end of a task, summarize:
  1. Files changed and why.
  2. Functionality implemented or fixed.
  3. Tests/checks run and their results.
  4. Open issues, risks, and required teammate coordination.
  5. Any user action still needed (for example, reviewing or pushing changes).
- Do not mark a task complete based only on code generation.

## 13. Rule Scope and Precedence

- This file is a shared engineering policy, not a sprint plan or task list.
- Current work items, acceptance criteria, and deadlines belong in separate task assignments or GitHub Projects.
- If an assignment conflicts with these rules, explain the conflict and ask for clarification rather than silently overriding either source.
- Repository-specific conventions and the latest approved team decisions take precedence over outdated examples or assumptions.
- Changes to this shared rules file should be reviewed by the team.

