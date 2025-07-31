FROM node:22-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev \
  && rm -rf /var/lib/apt/lists/*

# Install all dependencies including devDependencies for build
COPY package.json ./
RUN npm install

# Copy source files and build scripts
COPY . .

# Build the project (esbuild)
RUN npm run build

# Allow Cloud Run to override the port
ENV PORT=8080
EXPOSE 8080

# Start the server
CMD ["node","dist/index.cjs"]
