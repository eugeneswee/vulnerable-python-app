FROM python:3.8-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY test_app.py .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
