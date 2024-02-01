FROM --platform=linux/arm64 python:3.12.1-alpine3.19 as build
WORKDIR /opt/keto
ADD . /opt/keto
RUN apk add --no-cache build-base python3-dev linux-headers musl-dev cmake
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]
