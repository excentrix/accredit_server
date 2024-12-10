# Use an official Python runtime as a parent image
FROM python:3.12.3-slim

# Set the working directory in the container
WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy the requirements file to the working directory
COPY ./requirements.txt .

RUN ls

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

# Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt

COPY ./startup.sh .

# # Copy the rest of the application code to the working directory
COPY . .

# # Expose the port the app runs on
EXPOSE 8000

# # Define the command to run the app
RUN chmod +x ./startup.sh

ENTRYPOINT ["sh", "./startup.sh"]

