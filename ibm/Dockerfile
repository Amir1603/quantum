# Dockerfile
FROM python:3.12-slim

# Helpful defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Create a virtualenv (you said you use venv)
RUN pip install --upgrade pip

# Workdir & app files
WORKDIR /app

# Copy the code
COPY . /app

RUN pip install -r requirements.txt

# Artifacts folder (make it a volume so you can mount or copy easily)
RUN mkdir -p /app/artifacts
VOLUME ["/app/artifacts"]

# Tiny entrypoint so you can run:
#   docker run <image> my_file.py --arg1 x ...
COPY docker/run.sh /usr/local/bin/run-in-docker
RUN chmod +x /usr/local/bin/run-in-docker

ENTRYPOINT ["run-in-docker"]
