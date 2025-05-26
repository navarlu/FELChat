# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN apt update && apt install -y netcat-openbsd gcc graphviz libgraphviz-dev pkg-config
RUN pip install --no-cache-dir -r requirements.txt


# Copy app code
COPY backend/ .

# Set entrypoint (manage.py is in backend/)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh
