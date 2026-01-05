FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY ../requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY . /app/src
WORKDIR /app/src

EXPOSE 8000
CMD ["python", "run_auth.py"]
