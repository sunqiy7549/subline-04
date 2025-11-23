# Use the official Playwright Python image
# This includes Python, Playwright, and necessary browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with system dependencies
# This ensures all required system libraries are installed
RUN playwright install --with-deps chromium

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Define environment variable to ensure output is flushed immediately
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5001", "app:app"]
