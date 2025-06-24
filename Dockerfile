FROM python:3.10-slim

# Install OS packages Qt/PySide6 needs
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libx11-6 \
    libxcb1 \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    libglu1-mesa \
    libgl1-mesa-glx \
 && rm -rf /var/lib/apt/lists/*

# set a working directory
WORKDIR "/app"

# copy your code
COPY . .

# install any deps (if you have requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# default command to start your app
CMD ["python", "main.py"]