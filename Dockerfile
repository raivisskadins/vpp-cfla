FROM jupyter/base-notebook:python-3.11

# Set working directory inside the container
WORKDIR /home/jovyan/work

# Copy requirements file first
COPY requirements.txt ./

# Install Python dependencies
RUN pip install -r requirements.txt

# --- Playwright system dependencies ---
USER root
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libxss1 \
    libxtst6 \
    libx11-xcb1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER jovyan

# Install browsers for playwright
RUN playwright install

# Copy the rest of your project
COPY . .

# Add all folders to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/home/jovyan/work"

EXPOSE 8888
