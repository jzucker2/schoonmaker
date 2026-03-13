FROM python:3.13-slim-bookworm

WORKDIR /app

# Install runtime deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application and default sample(s)
COPY schoonmaker/ schoonmaker/
COPY cli.py test.py ./
COPY samples/ samples/

# Default: parse default sample and print summary
CMD ["python", "cli.py", "run"]
