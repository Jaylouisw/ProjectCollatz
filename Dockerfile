# Collatz Distributed Network - Docker Image with Auto-Update
# Multi-stage build for minimal image size

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    tar \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install IPFS
RUN wget https://dist.ipfs.tech/kubo/v0.31.0/kubo_v0.31.0_linux-amd64.tar.gz \
    && tar -xvzf kubo_v0.31.0_linux-amd64.tar.gz \
    && mv kubo/ipfs /usr/local/bin/ \
    && rm -rf kubo kubo_v0.31.0_linux-amd64.tar.gz

# Final stage
FROM python:3.11-slim

# Install runtime dependencies (including git for auto-update)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy IPFS binary from builder
COPY --from=builder /usr/local/bin/ipfs /usr/local/bin/ipfs

# Create app user (non-root)
RUN useradd -m -u 1000 collatz && \
    mkdir -p /home/collatz/.ipfs /app && \
    chown -R collatz:collatz /home/collatz /app

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements_distributed.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_distributed.txt

# Copy application code
COPY *.py .
COPY *.md .
COPY *.txt .
COPY *.json .

# Copy auto-update script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to app user
USER collatz

# Initialize IPFS
RUN ipfs init

# Expose IPFS ports
EXPOSE 4001 5001 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV IPFS_PATH=/home/collatz/.ipfs
ENV AUTO_UPDATE=true
ENV UPDATE_BRANCH=master
ENV UPDATE_INTERVAL=86400

# Create entrypoint script
COPY --chown=collatz:collatz docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "network_launcher.py"]
