# syntax=docker/dockerfile:1
FROM python:3

ENV user jeff
RUN useradd -m -d /home/${user} ${user} \
&& chown -R ${user} /home/${user} 
USER ${user}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
USER root
RUN chown -R ${user} /code

RUN curl -fsSL https://deb.nodesource.com/setup_17.x | bash -
RUN apt-get install -y nodejs
RUN npm install --save react-draft-wysiwyg draft-js

USER ${user}
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/

# start install npm 
