FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IN_DOCKER=1

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -U pip \
    && pip3 install --no-cache-dir -U -r requirements.txt

WORKDIR /fwdbot
COPY . /fwdbot
CMD ["/bin/bash", "/fwdbot/start.sh"]
