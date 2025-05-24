# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP run.py
ENV FLASK_ENV production # Default to production

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by some Python packages
# Example: RUN apt-get update && apt-get install -y some-package

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container at /app
COPY . .

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose the port the app runs on (Gunicorn default is 8000)
EXPOSE 8000

# Define the command to run the application
# Gunicorn will look for the 'app' callable in 'run.py' (or 'app:create_app()' if run.py creates the app instance)
# Make sure your run.py or app/__init__.py provides the Flask 'app' instance correctly.
# The number of workers can be adjusted based on your server's resources.
# A common recommendation is (2 * number_of_cores) + 1.

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
