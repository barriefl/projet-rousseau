FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system rousseau && adduser --system --group rousseau

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=rousseau:rousseau . .

USER rousseau

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]