FROM python:3.12-trixie

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR
ARG POETRY_VERSION=2.1.3

RUN apt-get update && \
    apt-get -y install nano && \
    pip install --upgrade pip "poetry==${POETRY_VERSION}"

RUN adduser \
    --system \
    --gecos \
    --disabled-login \
    --disabled-password \
    --home ${SANDBOX_DIR} \
    --uid ${SANDBOX_USER_UID} \
    sandbox && \
    chown root:root ${SANDBOX_DIR}

COPY ./src/pyproject.toml ./src/poetry.lock /tmp/
COPY ./src/prologd /usr/local/bin/
RUN cd /tmp && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-ansi

WORKDIR ${SANDBOX_DIR}
