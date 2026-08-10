FROM python:3.14-slim-bookworm

WORKDIR /app

COPY pyproject.toml README.md ./
COPY schoonmaker/ ./schoonmaker/
RUN pip install --no-cache-dir .

COPY samples/ ./samples/

CMD ["schoonmaker", "run"]
