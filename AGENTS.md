# FinSkillOS Agent Instructions

Before making code changes in this repository, read the local project memory:

1. `.devmd/workflow_and_memory/MEMORY.md`
2. Any linked memory file relevant to the task, especially:
   - `.devmd/workflow_and_memory/feedback_slice_workflow.md`
   - `.devmd/workflow_and_memory/project_descriptive_only_rule.md`
   - `.devmd/workflow_and_memory/feedback_offline_test_data.md`
   - `.devmd/workflow_and_memory/feedback_docker_migration_workflow.md`
   - `.devmd/workflow_and_memory/reference_slice_docs.md`
   - `.devmd/workflow_and_memory/user_context.md`

## Development And Validation

This project is developed and tested in Docker only.

- Do not debug or depend on WSL-local Python, Node, npm, `.venv`, or PATH setup.
- Use the `api` Docker image/container for backend lint, tests, scripts, and Alembic work.
- Use the `web` Docker image/container for frontend build/type validation.
- Rebuild Docker images after source edits before validating, because compose runs use image contents rather than a live source bind mount.
- Prefer explicit timeouts for Docker test runs so slow runs fail clearly.

Common commands:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api python -m ruff check <paths>
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest <tests> -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker exec finskillos-api alembic upgrade head
```

## Slice Workflow

- Treat `.devmd/<NN>_*.md` as the executable slice instruction.
- Read the active slice file before coding.
- Respect the slice's scope and "Out of Scope" / "Do not implement" boundaries.
- Do not advance to the next slice unless explicitly asked.
- Keep completion notes factual: exact files changed, Docker commands run, pass/fail result, known issues.

## Product Safety

FinSkillOS is descriptive and interpretive only.

- Do not add buy/sell/order/execution recommendations.
- Use operational, evidence, status, interpretation, risk, and watchpoint wording.
- Worker, refresh, and System Ops features must not imply trading action.
