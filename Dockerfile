from python:3.9-slim-bullseye

WORKDIR app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY *.py ./
COPY async_http/*.py async_http/
ENTRYPOINT /bin/bash
