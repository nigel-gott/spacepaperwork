FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  libpq-dev \
  gettext \
  postgresql-client \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==1.0.10"

# Requirements are installed here to ensure they will be cached.
COPY poetry.lock pyproject.toml /
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY ./compose/local/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

RUN mkdir -p /tmp/goosetools/static

WORKDIR /app

ADD . /app

ENTRYPOINT ["/entrypoint"]
