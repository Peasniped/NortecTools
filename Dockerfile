FROM python:3.10
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
RUN apt update 
RUN apt install tzdata -y
COPY . .
CMD python -u main.py