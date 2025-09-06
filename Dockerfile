FROM python:3.9-slim

# Security Issue: Running as root
WORKDIR /app

# Security Issue: Copy all files without filtering
COPY . .

# Security Issue: Outdated packages, no version pinning
RUN pip install --no-cache-dir -r requirements.txt

# Security Issue: Expose unnecessary ports
EXPOSE 5000 22 3306

# Security Issue: No health checks
CMD ["python", "app.py"]
