# Use official Python image from the DockerHub
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the dependencies file to the working directory 
COPY requirements.txt package.json /app/

# Install Node.js and make
RUN apt-get update && \
    apt-get install -y curl make && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install your JS dependencies
RUN npm install

# Copy the rest of the current directory contents into the container at /app
COPY . /app

# Run bash shell when the container launches to keep it running
CMD ["/bin/bash"]
