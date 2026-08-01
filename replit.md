# Daymark

Daymark is a local-first Streamlit task tracker for organizing open work, due dates, priorities, and completed tasks.

## Run & Operate

- `streamlit run main.py --server.port 5000` — run the Python task tracker
- `pnpm --filter @workspace/api-server run dev` — run the API server
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Python dependencies are managed with `pyproject.toml` and `uv.lock`.

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `main.py` — Streamlit UI, task operations, filtering, and local persistence
- `tasks.json` — created on first use; stores the user's task list

## Architecture decisions

- Tasks are stored in a small readable JSON file so the starter app works without a database.
- Streamlit's built-in components are used to keep the Python app easy to extend and run.

## Product

- Add tasks with notes, priority, category, and due date.
- Complete, search, filter, and delete tasks.
- See open, completed, overdue, and completion-rate summaries.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

_Populate as you build — sharp edges, "always run X before Y" rules._

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
