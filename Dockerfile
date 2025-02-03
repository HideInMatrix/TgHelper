
FROM python:3.12.0-slim AS builder

LABEL authors="davidmorgan"


WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . /app


RUN pip install --upgrade pip
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12.0-slim

LABEL authors="davidmorgan"


WORKDIR /app


COPY --from=builder /app /app


COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages


ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV TZ=Asia/Shanghai


RUN touch app.log && chmod -R 777 /app


CMD ["python", "bot.py"]
