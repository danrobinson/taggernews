FROM python:3.4

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./refresh /usr/src/app/refresh

ENTRYPOINT ["python", "./refresh.py"]