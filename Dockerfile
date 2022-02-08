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

USER ${user}
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/

