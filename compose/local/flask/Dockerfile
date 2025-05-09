FROM python:3.11-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV INSTALL_PATH /fermo_gui

RUN mkdir -p $INSTALL_PATH
WORKDIR $INSTALL_PATH

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && apt-get install -y netcat-openbsd \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY ./fermo_gui .

RUN pip install .

COPY ./compose/local/flask/entrypoint /entrypoint
COPY ./compose/local/flask/start /start
COPY ./compose/local/flask/celery/worker/start /start-celeryworker
COPY ./compose/local/flask/celery/beat/start /start-celerybeat
COPY ./compose/local/flask/celery/flower/start /start-flower
RUN chmod +x /start-flower /start-celerybeat /start-celeryworker /start /entrypoint

RUN chown -R appuser:appuser $INSTALL_PATH

USER appuser

EXPOSE 8001
ENTRYPOINT ["/entrypoint"]