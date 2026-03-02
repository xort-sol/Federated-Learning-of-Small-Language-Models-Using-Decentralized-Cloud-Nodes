FROM python:3.10

WORKDIR /app

COPY server.py .

RUN pip install fastapi uvicorn numpy

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]