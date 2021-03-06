FROM python:3.9-slim as builder
RUN apt-get update && apt-get install libgomp1 -y

RUN python3 -m venv /alice_predict/venv
COPY requirements.txt /alice_predict/
RUN /alice_predict/venv/bin/pip3 install -r /alice_predict/requirements.txt
COPY . /alice_predict/


FROM python:3.9-slim
MAINTAINER fragarie 'fragarie@yandex.com'

COPY --from=builder /usr/lib/x86_64-linux-gnu/libgomp.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /alice_predict/ /alice_predict/
WORKDIR /alice_predict

ENTRYPOINT ["/alice_predict/venv/bin/python3", "service.py"]
