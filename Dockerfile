# --- Stage 1: Base Image ---
# Use an official Python runtime as a parent image.
# 'python:3.11-slim' is a good choice: '3.11' is your Python version,
# and '-slim' means it's a smaller version of the image, good for production.
FROM python:3.11-slim

# --- Stage 2: Set Working Directory ---
# Sets the working directory for any subsequent RUN, CMD, ENTRYPOINT, COPY, ADD instructions.
# If the directory doesn't exist, it will be created.
# It's common practice to use /app or /usr/src/app.
WORKDIR /app

# --- Stage 3: Copy Requirements and Install Dependencies ---
# Copy the requirements file first. This is a Docker best practice for caching.
# If requirements.txt doesn't change, Docker can reuse this layer from a previous build, speeding things up.
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt.
# --no-cache-dir: Reduces the image size by not storing the pip download cache.
# --upgrade pip: Ensures you have the latest pip.
# -r requirements.txt: Tells pip to install from the requirements file.
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 4: Copy Application Files and Artifacts ---
# Copy your application code and necessary artifacts into the container's /app directory.

# Copy the streamlit dashboard script
# COPY streamlit_app_v2.py .

# Copy the utils functions script
# COPY utils.py .

# Copy the rest of the application's code into the container.
# The '.' source means the current directory on the host, and the '.' destination
# means the current WORKDIR inside the container (/app). COPY . . copiera tous les fichiers du répertoire de votre projet (sauf ceux ignorés par un fichier .dockerignore)
COPY . .

# Exposer le port sur lequel Streamlit va tourner
EXPOSE 8501

# CMD ["streamlit", "run", "streamlit_app_v2.py", "--server.port=8501", "--server.address=0.0.0.0"]
CMD ["streamlit", "run", "streamlit_app_debugging.py", "--server.port=8501", "--server.address=0.0.0.0"]