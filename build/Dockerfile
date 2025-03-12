# syntax=docker/dockerfile:1

ARG PYTHON_VERSION="3.12"
ARG DEBIAN_VERSION="bookworm"

FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION}

LABEL maintainer="Alexandre GIRARD <alexandre@zoreole.com>"
LABEL version="1.0.1"

ARG BOTO3_VERSION="1.37.11"
ARG EXABGP_VERSION="4.2.22"

RUN apt-get update \
    && apt-get install --yes \
    dumb-init \
    && apt-get clean

RUN pip3 install --upgrade \
    pip \
    wheel \
    setuptools

RUN pip3 install \
    boto3==${BOTO3_VERSION} \
    exabgp==${EXABGP_VERSION}

RUN adduser --system --uid ${UID:-999} exabgp

RUN mkdir /etc/exabgp

COPY tvfilter.py /etc/exabgp/tvfilter.py

RUN mkfifo /run/exabgp.in \
    && mkfifo /run/exabgp.out \
    && chown exabgp /etc/exabgp/tvfilter.py \
    && chown exabgp /run/exabgp.in \
    && chown exabgp /run/exabgp.out \
    && chmod 755 /etc/exabgp/tvfilter.py \
    && chmod 600 /run/exabgp.in \
    && chmod 600 /run/exabgp.out

WORKDIR /etc/exabgp

ENV exabgp.daemon.user="exabgp"
ENV exabgp.daemon.bind="0.0.0.0"

ENV AWS_REGION="eu-west-1"
ENV MAX_PREFIXES="2000"
ENV BLACKHOLE_COMMUNITY="65535:666"
ENV POLLING_INTERVAL="30"

EXPOSE 179/tcp

CMD ["/usr/bin/dumb-init", "--", "/usr/local/bin/exabgp", "/etc/exabgp/exabgp.conf"]
