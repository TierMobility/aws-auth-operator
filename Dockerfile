FROM python:3.7-alpine
ENV BASEDIR /srv/app/

WORKDIR ${BASEDIR}
RUN apk add --no-cache --virtual .build-deps gcc musl-dev
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
 
COPY . .

CMD kopf run --standalone --liveness=http://0.0.0.0:$PORT/healthz ./aws_auth.py
