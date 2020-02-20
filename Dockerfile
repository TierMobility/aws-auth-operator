FROM python:3.7-alpine
ENV BASEDIR /srv/app/

WORKDIR ${BASEDIR}
ADD requirements.txt requirements.txt
RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
    && pip install -r requirements.txt \
    && apk del .build-deps gcc musl-dev
    
COPY . .

CMD kopf run --standalone --liveness=http://0.0.0.0:$PORT/healthz -n kube-system ./aws_auth.py
