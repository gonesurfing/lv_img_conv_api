# lv_img_conv_api

A simple Express.js API for converting images using the `lv_img_conv` library.

## Prerequisites

- Node.js v22+
- npm
- Docker (for containerized deployment)

## Installation

```bash
# Clone this repository
git clone https://github.com/gonesurfing/lv_img_conv_api.git
cd lv_img_conv_api

# Install dependencies
npm install
```

## Build

Bundle source with esbuild:
```bash
npm run build
```

## Run Locally (Development)

Run directly from source (no build):
```bash
node src/index.js
```

Or after building:
```bash
npm start
```

The API listens on port `3000` by default (use `PORT` env var to override).

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

### Convert via URL

```bash
curl -X POST http://localhost:8080/convert \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/image.png",
    "cf": "CF_INDEXED",
    "output": "c_array"
  }' \
  --output converted.bin
```

### Convert via File Upload

```bash
curl -X POST http://localhost:8080/convert \
  -F 'image=@/path/to/image.png' \
  -F 'cf=CF_INDEXED' \
  -F 'output=c_array' \
  --output converted.bin
```

## Environment Variables

- `PORT` – port to listen on (default `3000` locally, `8080` in Docker)