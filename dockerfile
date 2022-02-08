FROM python:3.9-slim as builder
RUN apt-get update && apt-get install libgomp1 -y

FROM python:3.9-slim
MAINTAINER fragarie 'fragarie@yandex.com'

COPY --from=builder /usr/lib/x86_64-linux-gnu/libgomp.so* /usr/lib/x86_64-linux-gnu/
COPY . /alice_predict/
WORKDIR /alice_predict

RUN python3 -m venv /alice_predict/venv
RUN /alice_predict/venv/bin/pip3 install -r requirements.txt

ENTRYPOINT ["/alice_predict/venv/bin/python3", "service.py"]
