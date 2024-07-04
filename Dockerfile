# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install git and other necessary tools
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    libc-dev \
    libffi-dev \
    flac \
    && rm -rf /var/lib/apt/lists/*

# Clone the repository
RUN git clone https://github.com/m3dkata/Speech2Text.git .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8004

# Set the Python path to include the speech2text directory
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "speech2text.main:app", "--host", "0.0.0.0", "--port", "8004"]
