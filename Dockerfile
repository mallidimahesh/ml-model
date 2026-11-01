FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code including prebuilt frontend/dist
COPY . .

ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

CMD ["python", "run.py"]
