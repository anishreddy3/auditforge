FROM python:3.12-slim

# Install Node.js for Terminal 3 SDK bridge
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies for T3N scripts
COPY t3_scripts/package.json t3_scripts/
RUN cd t3_scripts && npm install --production

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output

EXPOSE 8000

CMD ["python", "main.py", "--serve"]
