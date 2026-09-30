FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

ARG QUARTO_VERSION=1.8.25

COPY --from=ghcr.io/astral-sh/uv:0.12.0 /uv /uvx /usr/local/bin/

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates curl \
    && curl --fail --show-error --location \
      --output /tmp/quarto.deb \
      "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-$(dpkg --print-architecture).deb" \
    && apt-get install --yes /tmp/quarto.deb \
    && rm --force /tmp/quarto.deb \
    && rm --recursive --force /var/lib/apt/lists/*
