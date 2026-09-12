FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (ffmpeg is essential for audio conversions)
RUN apt-get update && apt-get install -y ffmpeg curl git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "run_app.py"]
