FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirement.txt /app/
RUN pip install --no-cache-dir -r requirement.txt

# Create logs and BureauReports directories if they don't exist
RUN mkdir -p /app/logs /app/BureauReports

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose the port gunicorn will listen on
EXPOSE 5000

# Run Gunicorn
CMD ["gunicorn", "--workers=5", "--bind", "0.0.0.0:5001", "wsgi:app"]