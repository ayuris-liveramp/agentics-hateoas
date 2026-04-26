FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY tests/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy test suite
COPY tests /app/tests

# Set entry point
ENTRYPOINT ["pytest"]
