FROM python:3.11

WORKDIR /code

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 3100

ENTRYPOINT ["gunicorn", "api:create_app()"]
