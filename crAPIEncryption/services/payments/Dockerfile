FROM python:3.8-alpine3.15 AS builder
WORKDIR /build
COPY requirements.txt .
RUN apk add --no-cache build-base libffi-dev postgresql-dev \
 && pip install --no-cache-dir wheel \
 && pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.8-alpine3.15
WORKDIR /opt/crapi-payments
RUN apk add --no-cache libpq curl
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt
COPY . .
RUN chmod +x runner.sh
EXPOSE 8001
CMD ["/bin/sh", "runner.sh"]
