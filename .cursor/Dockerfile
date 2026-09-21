FROM ubuntu:24.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        build-essential \
        python3 \
        python3-pip \
        python3.12-venv \
    && rm -rf /var/lib/apt/lists/*
