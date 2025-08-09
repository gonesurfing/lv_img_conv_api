FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files and build scripts
COPY . .

# Allow Cloud Run to override the port
ENV PORT=8080
EXPOSE 8080

# install gunicorn (if not already in requirements.txt)
RUN pip install --no-cache-dir gunicorn

# Start the app with gunicorn so stdout/stderr get captured by Cloud Run
CMD ["gunicorn", "app:app", \
  "--bind", "0.0.0.0:8080", \
  "--capture-output", \
  "--enable-stdio-inheritance"]
