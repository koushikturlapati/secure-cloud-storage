FROM python:3.11-slim


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


RUN mkdir -p /app/database /app/storage /data \
    && chown -R 10001:10001 /app /data


COPY --chown=10001:10001 api ./api
COPY --chown=10001:10001 backend ./backend
COPY --chown=10001:10001 crypto ./crypto
COPY --chown=10001:10001 frontend ./frontend


USER 10001:10001


EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=3)"


CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
