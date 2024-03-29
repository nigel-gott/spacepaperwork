FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # git for running pre-commit hooks inside the container
  && apt-get install -y git \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==1.0.10"

# Requirements are installed here to ensure they will be cached.
COPY poetry.lock pyproject.toml /
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

RUN mkdir -p /tmp/goosetools/static && mkdir -p /temp_repo

COPY .pre-commit-config.yaml /temp_repo/.pre-commit-config.yaml


WORKDIR /app

RUN cd /temp_repo/ && git init . && pre-commit install-hooks
