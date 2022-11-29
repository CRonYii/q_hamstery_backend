FROM python:3.8.13-buster

COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt --no-cache-dir
RUN pip3 install gunicorn

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "q_hamstery_backend.wsgi"]
