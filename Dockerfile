FROM python:3.11-slim

WORKDIR /app

# Make /app importable for any ``python script.py`` invocation inside
# the container. Streamlit + alembic find the package without it, but
# helper scripts (scripts/seed_sample_data.py, refresh_market_data.py,
# …) ran as plain files do not — Python prepends the script's own
# directory, not the working directory, to ``sys.path``. Setting
# PYTHONPATH explicitly avoids "ModuleNotFoundError: No module named
# 'finskillos'" when the user runs those scripts via
# ``docker compose run --rm app python scripts/...``.
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
