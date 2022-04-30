FROM python:3.8-slim-buster AS linux_base

# install deps
RUN apt-get update -y && apt-get install -y \
        git \
        xz-utils \
        libffi-dev \
        libssl-dev \
        curl \
        gcc \
        build-essential \
    && apt-get clean


FROM linux_base AS python_dependencies
COPY requirements.txt requirements.txt


RUN pip install -r requirements.txt

FROM python_dependencies AS source_code
COPY /schoonmaker /schoonmaker

WORKDIR /schoonmaker

FROM source_code AS run_server

# can use `run_dev.sh` or `run_prod.sh`
CMD ["python", "test.py"]
