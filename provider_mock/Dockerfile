# Define build args (used for all stages) here
# These args can be overridden during build by --build-args NAME=VAL
# see: https://docs.docker.com/engine/reference/builder/#arg

ARG PYTHON_VERSION=3.12.2-slim-bookworm

# PYTHON_WHEEL_PATH is used to store the built wheels
ARG PYTHON_WHEEL_PATH=/var/cache/python/wheels

# Virtualenv settings
ARG PYSETUP_PATH=/opt/python
ARG VENV_PATH=/opt/python/.venv

# Poetry settings
ARG POETRY_VERSION=2.2.1
ARG POETRY_VIRTUALENVS_IN_PROJECT=true
ARG POETRY_NO_INTERACTION=1
ARG POETRY_INSTALL_OPTS='--only main --no-root'

################################################################################
# Base stage
################################################################################
# base stage defines the base for other stages, to set defaults and define build args

FROM python:${PYTHON_VERSION} AS base-python

# python settings
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # pip settings
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

ARG PYTHON_WHEEL_PATH

ARG PYSETUP_PATH

ARG VENV_PATH
ENV VENV_PATH=${VENV_PATH}

ARG POETRY_VERSION
ENV POETRY_VERSION=${POETRY_VERSION}

ARG POETRY_VIRTUALENVS_IN_PROJECT
ENV POETRY_VIRTUALENVS_IN_PROJECT=${POETRY_VIRTUALENVS_IN_PROJECT}

ARG POETRY_NO_INTERACTION
ENV POETRY_NO_INTERACTION=${POETRY_NO_INTERACTION}

ARG POETRY_INSTALL_OPTS
ENV POETRY_INSTALL_OPTS=${POETRY_INSTALL_OPTS}

ENV WORKDIR=/app

ENV APP_PATH=${WORKDIR}/src
WORKDIR ${APP_PATH}

RUN mkdir -p ${PYTHON_WHEEL_PATH} \
    && mkdir -p ${PYSETUP_PATH} \
    && mkdir -p ${APP_PATH}


# prepend venv to path
ENV PATH="$VENV_PATH/bin:$PATH"

################################################################################
# Build stage
################################################################################

FROM base-python AS app-build-stage

# install all build dependencies to build wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential

# explicitly download base dependencies (poetry, etc.) wheels, then install them
# keep the wheels so they're available for the next stage
RUN pip wheel --wheel-dir ${PYTHON_WHEEL_PATH} poetry==${POETRY_VERSION} \
    && pip install --no-cache-dir --no-index --find-links=${PYTHON_WHEEL_PATH} ${PYTHON_WHEEL_PATH}/poetry* \
    && rm -rf ${PYTHON_WHEEL_PATH}

WORKDIR ${PYSETUP_PATH}

# copy application dependency specs
COPY poetry.lock pyproject.toml ./

# build and install the application dependencies in a virtualenv (cache-bust: 1)
# cleanup cached files as build is done, since these paths are copied into the next stage.
# no fail on cleanup.
RUN poetry install ${POETRY_INSTALL_OPTS} && \
    (poetry cache clear --all --no-interaction PyPI || true) && \
    (poetry cache clear --all --no-interaction _default_cache || true) &&\
    rm -rf poetry.lock pyproject.toml

################################################################################
# Run stage
################################################################################
FROM base-python AS app-run-stage

ENV SRC=src

# install required runtime dependencies, and cleanup cached files for a smaller layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# copy the application dependencies (pre-built virutalenv)
COPY --from=app-build-stage $PYSETUP_PATH $PYSETUP_PATH

# Copy application source code
COPY ${SRC} ${APP_PATH}

WORKDIR ${WORKDIR}

EXPOSE 80
