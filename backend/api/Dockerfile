FROM python:3.10.13-slim
WORKDIR /usr/src/backend/api

# "wait-for-it.sh" copy + /bin
# https://docs.docker.com/compose/startup-order/
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Install linux packages
RUN apt-get update
RUN apt-get install \
  # --- for mp3 conversions by pydub
  ffmpeg libavcodec-extra \
  -y

# Install python packages for app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy src
COPY . .

# Env
# --- Secrets
ARG AWS_REGION
ENV AWS_REGION=$AWS_REGION
ARG AWS_ACCESS_KEY_ID
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
ARG TARGET_ENV
ENV TARGET_ENV=$TARGET_ENV
ARG TARGET_SERVICE
ENV TARGET_SERVICE=$TARGET_SERVICE
# --- Configs (pytorch num_threads, logging, etc.)
ENV PYTHONUNBUFFERED=1

# Start
EXPOSE 3000
CMD ["python", "-u", "src/start.py"]
