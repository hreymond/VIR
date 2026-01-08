# Get base image 
FROM python:3.14-slim

WORKDIR /app

COPY . .

# Add instructions to build the CustomDB binary

RUN pip install -r requirements.txt

ENV FLASK_APP=flask_minimal.py

CMD ["flask", "run", "--host=0.0.0.0"]
