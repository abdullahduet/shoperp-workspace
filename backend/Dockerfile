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

# Run migrations, seed accounts, then start the server.
#
# prisma migrate deploy  — uses DIRECT_URL (bypasses PgBouncer) for DDL.
#                          Safe to run on every deploy; only applies pending migrations.
# python prisma/seed.py  — idempotent upsert of the 13 chart-of-accounts rows.
# uvicorn                — uses DATABASE_URL (pooled) for all runtime queries.
CMD ["sh", "-c", "prisma migrate deploy && python prisma/seed.py && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
