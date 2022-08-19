FROM python:3.10-slim-buster

ENV AFK_CHANNEL "$AFK_CHANNEL"
ENV SERVER "$SERVER"
ENV PORT "$PORT"
ENV NICK "$NICK"
ENV CERTIFICATE "$CERTIFICATE"
ENV IDLE_TIME "$IDLE_TIME"
ENV PASSWORD "$PASSWORD"

RUN mkdir /app

ADD . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["/bin/bash", "start.sh"]
