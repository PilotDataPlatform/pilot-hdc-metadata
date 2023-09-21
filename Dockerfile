FROM python:3.9 AS production-environment

ENV PYTHONDONTWRITEBYTECODE=true \
    PYTHONIOENCODING=UTF-8 \
    POETRY_VERSION=1.3.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

ENV PATH="${POETRY_HOME}/bin:${PATH}"
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /usr/src/app
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-dev --no-root --no-interaction

FROM production-environment AS metadata-image
COPY app ./app
ENTRYPOINT ["python3", "-m", "app"]

FROM production-environment AS development-environment
RUN poetry install --no-root --no-interaction

FROM development-environment AS alembic-image
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
ENTRYPOINT ["python3", "-m", "alembic"]
CMD ["upgrade", "head"]
