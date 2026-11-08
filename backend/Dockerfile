FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first, so code edits do not re-install them.
COPY pyproject.toml constraints.txt ./
COPY app ./app
RUN pip install -c constraints.txt .

COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
COPY rag_eval ./rag_eval

RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:5000/api/health', timeout=4)"

# corpus/ is mounted at /app/corpus (see docker-compose.yml); it is not baked into the image.
# No `alembic upgrade head` here: the DB is a shared Supabase instance, so migrations run by hand.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
