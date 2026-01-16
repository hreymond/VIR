# Get base image 
FROM python:3.14-slim

WORKDIR /app

RUN apt update

RUN apt install -y libpq-dev gcc iproute2 iputils-ping net-tools

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY flask_minimal.py .

ENV FLASK_APP=flask_minimal.py

CMD ["flask", "run", "--host=0.0.0.0"]
