FROM python:3.13.0b2-slim

COPY requirements.txt ./

RUN apt-get update \
    # Can't find wheels for asyncpg for some reason :(
    && apt-get install -y libpq-dev gcc \
    && pip install -r requirements.txt \
    && apt remove -y libpq-dev gcc \
    && apt -y autoremove \
    && rm -rf /var/lib/apt/lists/*

COPY app/ /example/app/
COPY main.py /example

EXPOSE 9000

CMD [ "python", "/example/main.py" ]
