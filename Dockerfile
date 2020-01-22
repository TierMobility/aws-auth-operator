FROM python:3.7-slim-stretch
ENV BASEDIR /srv/app/

WORKDIR ${BASEDIR}
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
 
COPY . .

CMD kopf run --standalone ./aws_auth.py
