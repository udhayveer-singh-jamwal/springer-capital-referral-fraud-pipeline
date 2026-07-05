# Use official Python slim image for a small, fast build
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first (leverages Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY profile_data.py .
COPY referral_pipeline.py .

# Input CSVs are expected under /app/data (mount a host folder here)
# Output reports are written to /app/output (mount a host folder here
# so the report is available outside the container)
CMD ["sh", "-c", "python profile_data.py && python referral_pipeline.py"]
