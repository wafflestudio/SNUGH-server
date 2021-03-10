FROM python:3.6.7

ENV PYTHONUNBUFFERED 1

RUN apt-get -y update
RUN apt-get -y install vim

RUN mkdir /srv/SNUGH-server
ADD . /srv/SNUGH-server

WORKDIR /srv/SNUGH-server

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python manage.py migrate

#EXPOSE 8000
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
