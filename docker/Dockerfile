FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/workspace/MARBTS/src

WORKDIR /workspace/MARBTS

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
COPY scripts ./scripts
COPY scenarios ./scenarios
COPY configs ./configs

RUN python -m pip install --upgrade pip \
    && python -m pip install -e .

ENTRYPOINT ["marbts"]
CMD ["--help"]
