FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Note: For a demo, we'll mock the docker command since Cloud Run doesn't support Docker-in-Docker
# This modification will make the deployment work, but the MCP server functionality
# would need to be adapted for production use
RUN mkdir -p /usr/local/bin && \
    echo '#!/bin/bash\necho "Mock Docker: $@"\nexit 0' > /usr/local/bin/docker && \
    chmod +x /usr/local/bin/docker

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data/conversations

# Expose port (Cloud Run will use the PORT env variable)
EXPOSE 8080

# Create entrypoint script that uses the PORT environment variable
RUN echo '#!/bin/bash\nuvicorn app:app --host 0.0.0.0 --port "${PORT:-8080}"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Run the application with the PORT environment variable
CMD ["/entrypoint.sh"] 