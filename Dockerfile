FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files and build scripts
COPY . .

# Allow Cloud Run to override the port
ENV PORT=8080
EXPOSE 8080

# Start the server
CMD ["python", "app.py"]
