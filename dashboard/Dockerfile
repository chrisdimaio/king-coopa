FROM python:3.12-slim
WORKDIR /app
COPY server.py .
COPY static ./static
ENV PORT=8090 \
    KC_CONTROL_URL=http://fake-king-coopa.invalid:8080 \
    PYTHONUNBUFFERED=1
EXPOSE 8090
USER nobody
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/status' % os.environ.get('PORT', '8090'), timeout=4)"
CMD ["python", "server.py"]
