# Use an official, lightweight Python base image
FROM python:3.11-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED: Prevents Python from buffering stdout/stderr (crucial for clean Docker logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Set the working directory inside the container
WORKDIR /app

# Install system-level dependencies (if any are needed in slim images)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker's build cache
COPY requirements.txt /app/

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files to the working directory
COPY . /app/

# Create runtime directories in case they are needed
RUN mkdir -p data database charts reports

# Expose the API and Dashboard port
EXPOSE 8000

# Start the FastAPI web server using uvicorn
CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000"]
