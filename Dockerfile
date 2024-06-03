# Use an official Python runtime as a parent image
FROM python:latest

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements.txt file (to be created in the next step)
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the containers
COPY app.py ./

# Run the Python script when the container launches
CMD ["python3", "./app.py"]
