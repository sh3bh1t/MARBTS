FROM python:3.12-slim

WORKDIR /workspace

COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

COPY . .

ENV PYTHONPATH=src

CMD ["python", "scripts/run_phase5_ablation_smoke.py"]
