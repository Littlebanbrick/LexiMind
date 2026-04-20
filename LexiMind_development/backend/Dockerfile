FROM python:3.10-slim

WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY . .

# Create data directory (for mounting SQLite)
RUN mkdir -p /app/data

# Expose the port Flask will run on
EXPOSE 5000

# Start up
CMD ["python", "app.py"]
