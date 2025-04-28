FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the application code
COPY . /app/

# Expose the necessary port
EXPOSE 8080

# Command to run the app
CMD ["python", "app.py"]