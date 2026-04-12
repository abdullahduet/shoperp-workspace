FROM python:3.12-slim

WORKDIR /app

# Install system dependencies.
# libatomic1 is required by the Node.js binary that Prisma bundles for its
# query engine — python:*-slim strips it, causing `prisma generate` to fail
# with "libatomic.so.1: cannot open shared object file".
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Generate the Prisma client from schema
RUN prisma generate

EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "prisma db push --skip-generate && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
