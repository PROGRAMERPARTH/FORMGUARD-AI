FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR and PDF rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-mar \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set default port (Render will override PORT dynamically)
ENV PORT=8501

# Expose port
EXPOSE 8501

# Run Streamlit with dynamic PORT support for Render and Docker
CMD ["sh", "-c", "streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.headless true"]
