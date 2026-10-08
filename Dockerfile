# استخدام صورة بايثون رسمية خفيفة
FROM python:3.11-slim

# منع بايثون من كتابة ملفات pyc وضمان إخراج السجلات فورا
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تثبيت الأدوات الأساسية ومكتبة ffmpeg و nodejs لتشغيل اكواد الجافاسكريبت لـ yt-dlp
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت مكتبات بايثون أولاً للاستفادة من Docker Cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود المشروع بالكامل
COPY . .

# منفذ التشغيل الافتراضي (Railway يقوم بتمرير متغير PORT تلقائياً)
ENV PORT=8000
EXPOSE ${PORT}

# تشغيل خادم Uvicorn وربطه بالمنفذ المخصص
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
