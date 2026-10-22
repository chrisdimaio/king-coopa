FROM python:3.12-slim
WORKDIR /app
COPY server.py ptz.py ./
COPY static ./static
# Where reconfigure goes. Defaults to a fake .invalid host so the dashboard can't rewrite the
# Pi's config; override at build time (--build-arg) or at run time (-e KC_RECONFIGURE_URL=...).
# Open/close/restart go to KC_CONTROL_URL, which defaults to KC_INFO_URL (the real controller).
ARG KC_RECONFIGURE_URL=http://fake-king-coopa.invalid:8080
ENV PORT=8090 \
    KC_RECONFIGURE_URL=${KC_RECONFIGURE_URL} \
    PYTHONUNBUFFERED=1
EXPOSE 8090
USER nobody
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/status' % os.environ.get('PORT', '8090'), timeout=4)"
CMD ["python", "server.py"]
