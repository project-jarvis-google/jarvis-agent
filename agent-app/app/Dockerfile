## Use an official Python runtime as a parent image (optimized for FastAPI)
FROM python:3.12.7-alpine3.20

WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies, including Google Cloud libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose the port your FastAPI application runs on (default is 8000)
EXPOSE 8000

# Define the command to run your FastAPI application using Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "60"]