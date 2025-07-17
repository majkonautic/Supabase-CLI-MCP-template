FROM debian:bullseye-slim

WORKDIR /app

# Install dependencies including git (required by supabase CLI)
RUN apt-get update && \
    apt-get install -y curl unzip python3-pip git && \
    curl -sL https://github.com/supabase/cli/releases/latest/download/supabase_linux_amd64.tar.gz | tar -xz && \
    mv supabase /usr/local/bin/supabase && \
    chmod +x /usr/local/bin/supabase && \
    pip3 install fastapi uvicorn && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY main.py /app/
COPY .env /app/

# Create the expected directory structure
RUN mkdir -p /app/supabase /app/functions

EXPOSE 5001

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
