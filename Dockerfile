FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED 1

ENV INSTALL_PATH /fermo_gui
RUN mkdir -p $INSTALL_PATH
WORKDIR $INSTALL_PATH

RUN apt-get update && apt-get install -y redis-server

COPY ./fermo_gui .

RUN pip install uv
RUN uv sync

RUN chmod +x ./entrypoint_docker.sh

EXPOSE 8001

CMD ["./entrypoint_docker.sh"]