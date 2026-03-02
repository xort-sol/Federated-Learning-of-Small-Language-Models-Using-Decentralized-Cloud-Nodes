FROM python:3.10

WORKDIR /app

COPY client.py .

RUN pip install requests numpy

CMD ["python", "client.py"]