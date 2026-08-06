FROM python:3.12-slim

WORKDIR /app

COPY gms/requirements.txt gms/requirements.txt
RUN pip install --no-cache-dir -r gms/requirements.txt

COPY gms/ gms/
COPY fixtures/ fixtures/

ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "gms.main:app", "--host", "0.0.0.0", "--port", "8000"]
