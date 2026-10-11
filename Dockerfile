# استخدام صورة بايثون رسمية خفيفة
FROM python:3.11-slim

# منع بايثون من كتابة ملفات pyc وضمان إخراج السجلات فوراً
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تثبيت الأدوات الأساسية ومكتبة ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# تثبيت Node.js 20 LTS الحديث (اللازم لـ yt-dlp لدعم --permission وحل تحديات n-challenge)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# تثبيت Deno (المحرك الافتراضي والمفضل رسمياً من yt-dlp لحل تحديات التشفير والبوت)
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

WORKDIR /app

# تثبيت مكتبات بايثون أولاً للاستفادة من Docker Cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# تحميل وتخزين مكتبة فك التحديات مسبقاً لضمان عملها فورياً دون الحاجة لتنزيلها أثناء تشغيل السيرفر
RUN mkdir -p /root/.cache/yt-dlp/challenge-solver \
    && (curl -fsSL -o /root/.cache/yt-dlp/challenge-solver/lib.json https://github.com/yt-dlp/ejs/releases/latest/download/yt.solver.lib.min.js || true)

# نسخ كود المشروع بالكامل
COPY . .

# منفذ التشغيل الافتراضي (Railway يقوم بتمرير متغير PORT تلقائياً)
ENV PORT=8000
EXPOSE ${PORT}

# تشغيل خادم Uvicorn وربطه بالمنفذ المخصص مع دعم البروكسي العكسي لـ Railway
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
