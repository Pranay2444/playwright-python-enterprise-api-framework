FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-dev.txt pyproject.toml README.md /app/
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY src /app/src
COPY scripts/start_lab.py /app/start_lab.py
RUN pip install --no-deps --no-cache-dir . && useradd --uid 10001 --create-home labuser
EXPOSE 8000
# Bootstrap needs root only to read the 0600 secret mount; start_lab drops UID/GID before exec.
CMD ["python", "/app/start_lab.py"]
