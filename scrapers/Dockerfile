# ---------- Base Image ----------
FROM python:3.11-slim

# ---------- Environment Setup ----------
WORKDIR /app

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ---------- System Dependencies ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---------- Install Python Dependencies ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Copy Source Code ----------
COPY . .

# ---------- Expose Port ----------
EXPOSE 8000

# ---------- Start Server ----------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
