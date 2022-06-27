FROM python:3.7-alpine
ENV BASEDIR /srv/app/

WORKDIR ${BASEDIR}
ADD requirements.txt requirements.txt
RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
    && pip install -r requirements.txt \
    && apk del .build-deps gcc musl-dev
    
COPY . .

RUN addgroup -S app && adduser -S -G app app 
USER app
CMD kopf run --standalone --log-format=json --liveness=http://0.0.0.0:$PORT/healthz -n kube-system ./aws_auth.py
