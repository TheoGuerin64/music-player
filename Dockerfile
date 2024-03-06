FROM python:3.10

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN python -m pip install --no-cache-dir --upgrade pip

WORKDIR /bot
COPY requirements.txt /bot

RUN python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /bot

CMD ["python3.10", "bot.py"]
