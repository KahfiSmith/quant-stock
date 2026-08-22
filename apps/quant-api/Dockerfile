FROM python:3.12.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system quantlens && adduser --system --ingroup quantlens quantlens

COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip==25.1.1 && pip install -r requirements.txt

COPY . .
RUN chown -R quantlens:quantlens /app

USER quantlens

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
