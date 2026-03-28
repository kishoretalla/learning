FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home appuser

# Install backend dependencies from pyproject without building a wheel.
# The source tree is copied afterward and imported directly as backend.*.
COPY backend/pyproject.toml ./backend/pyproject.toml

RUN pip install --no-cache-dir --upgrade pip \
    && python - <<'PY' > /tmp/requirements.txt
import tomllib

with open('/app/backend/pyproject.toml', 'rb') as f:
    data = tomllib.load(f)

for dep in data['project']['dependencies']:
    print(dep)
PY
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/ ./backend/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
