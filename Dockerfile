FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN pip3 install --no-cache-dir --upgrade pip

COPY ./requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

WORKDIR /app

COPY . /app/

FROM base AS dev

CMD ["python3.12", "-m", "my_discord_bot"]

FROM base AS prod

CMD ["python3.12", "-O", "-m", "my_discord_bot"]
