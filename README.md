# lv_img_conv_api

A simple Flask API for converting images to LVGL format with optional resizing.

## Prerequisites

- Python 3.12+
- pip
- Docker (for containerized deployment)

## Installation

```bash
# Clone this repository
git clone https://github.com/gonesurfing/lv_img_conv_api.git
cd lv_img_conv_api

# Install dependencies
pip install -r requirements.txt
```

## Run Locally (Development)

```bash
python app.py
```

The API will start on port `8080` by default (use `PORT` env var to override).

## Docker

Build the Docker image:
```bash
docker build -t lv_img_conv_api .
```

Run the container:
```bash
docker run -p 8080:8080 lv_img_conv_api
```

Inside the container, the service listens on port `8080` (configurable via `PORT` env var).

## API Usage

The API supports converting images to various LVGL formats with optional resizing. 

### Convert via URL

```bash
curl -X POST http://localhost:8080/convert \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/image.png",
    "cf": "RGB565A8",
    "output": "BIN",
    "maxSize": "100x100"
  }' \
  --output converted.bin
```

### Convert via File Upload

Upload a file with JSON parameters:

```bash
curl -X POST http://localhost:8080/convert \
  -F 'image=@/path/to/image.png' \
  -F 'params={"cf":"RGB565A8","output":"BIN","maxSize":"100x100"}' \
  --output converted.bin
```

### Parameters

- `cf`: Color format (RGB565A8, ARGB8888, RGB565, I8, etc.)
- `output`: Output format (BIN, C, PNG)
- `maxSize` (optional): Target dimensions for resizing in "widthxheight" format (e.g., "100x100")
- `compress` (optional): Compression method (NONE, RLE, LZ4)

**Note:** When uploading files, JSON parameters must be passed in a `params` form field as a JSON string.

## Environment Variables

- `PORT` – port to listen on (default `8080`)

## Build and deploy in Google Cloud
```bash
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-east1

gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/lv-img-conv-api

gcloud run deploy lv-img-conv-api \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/lv-img-conv-api \
  --platform managed \
  --allow-unauthenticated \
  --port 8080

# (add --max-instances to limit the number of container instances)
# e.g. limit to 3 instances:
gcloud run deploy lv-img-conv-api \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/lv-img-conv-api \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --max-instances 1
```