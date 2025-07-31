FROM python:3.11-slim

# Install system dependencies (including SDL2 for pygame)
RUN apt-get update && apt-get install -y \
    libsdl2-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev \
    libsmpeg-dev libsdl1.2-dev libportmidi-dev libswscale-dev \
    libavformat-dev libavcodec-dev libfreetype6-dev \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy files into the container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run the bot
CMD ["python", "TeamLegendBOT.py"]
