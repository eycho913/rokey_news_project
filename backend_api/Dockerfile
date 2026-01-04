# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any dependencies
COPY ./backend_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install pytest \
    && pip list \
    && echo $PATH

# Add a diagnostic script
COPY ./backend_api/debug_versions.py /app/debug_versions.py
RUN python /app/debug_versions.py

# Copy the current directory contents into the container at /app
COPY ./backend_api /app

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
