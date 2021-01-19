# first stage
FROM python:3.7 AS builder


RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
# install dependencies to the local user directory (eg. /root/.local)
RUN pip install -r requirements.txt

# second unnamed stage
FROM python:3.7-slim
WORKDIR /code

# copy only the dependencies installation from the 1st stage image
COPY --from=builder /opt/venv /opt/venv

COPY ./main.py .

# update PATH environment variable
ENV PATH="/opt/venv/bin:$PATH"

CMD [ "python", "./main.py" ]

