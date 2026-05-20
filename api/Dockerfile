FROM python:3.11-slim

WORKDIR /app

# Make /app importable for the FinSkillOS domain layer (same pattern
# as the Streamlit Dockerfile — `python -m` does not auto-prepend the
# working directory).
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
