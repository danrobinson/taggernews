FROM python:3.4

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./tagger /usr/src/app

RUN apt-get update && apt-get install -y \
		gcc \
		gettext \
		mysql-client default-libmysqlclient-dev \
	--no-install-recommends && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
ENTRYPOINT ["gunicorn", "tagger.wsgi:application", "--bind=0.0.0.0:8000", "--workers=3"]