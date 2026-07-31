FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OPENPATROL_HOST=0.0.0.0 OPENPATROL_DATA=/data
WORKDIR /app
COPY . /app
RUN useradd --system --uid 10001 --create-home openpatrol && mkdir -p /data && chown openpatrol:openpatrol /data
USER 10001
EXPOSE 8765
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/v1/health',timeout=2)"
CMD ["python", "-m", "openpatrol.server"]
