FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . /app

# Make sure the data dir exists and is writable (for SQLite)
RUN mkdir -p /app/data

EXPOSE 8080

# Use a startup script or inline command to initialize DB at runtime
CMD ["sh", "-c", "python manage.py init && gunicorn 'run:create_app()' -w 4 -b 0.0.0.0:8080 --log-file -"]