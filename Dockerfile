FROM python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN python -m pip install --no-cache-dir --upgrade pip

COPY ./requirements.txt /app/
RUN python -m pip install --no-cache-dir --upgrade -r requirements.txt

RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app
USER app

COPY . /app/
CMD ["python3.11", "bot.py"]
