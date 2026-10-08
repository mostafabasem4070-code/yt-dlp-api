import logging
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from extractor import extract_youtube_info

# إعداد السجلات (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Direct Links Extractor API",
    description="API بسيط وسريع لاستخراج الروابط المباشرة المؤقتة لجميع جودات وصيغ فيديو اليوتيوب باستخدام yt-dlp.",
    version="1.0.0"
)

# تفعيل الـ CORS للسماح لموقعك بالاتصال بالـ API بدون مشاكل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    url: str = Field(..., description="رابط فيديو اليوتيوب (مثال: https://www.youtube.com/watch?v=dQw4w9WgXcQ)")

@app.get("/", tags=["Health"])
def health_check():
    """فحص حالة السيرفر ودليل استخدام الـ API"""
    return {
        "status": "online",
        "service": "YouTube Direct Links Extractor API",
        "documentation": "/docs",
        "endpoints": {
            "POST /api/extract": "إرسال رابط الفيديو عبر JSON body: {'url': '...'}",
            "GET /api/extract": "إرسال رابط الفيديو عبر Query param: /api/extract?url=..."
        }
    }

def handle_extraction(url: str):
    url = url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رابط الفيديو مطلوب.")

    try:
        logger.info(f"Extracting info for URL: {url}")
        return extract_youtube_info(url)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error extracting video: {error_msg}")
        if "Sign in to confirm you're not a bot" in error_msg or "Please sign in" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="يوتيوب يطلب تسجيل الدخول لتأكيد عدم وجود روبوت. قم بإضافة متغير البيئة YOUTUBE_COOKIES على Railway أو وضع ملف cookies.txt."
            )
        elif "Private video" in error_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="هذا الفيديو خاص (Private) ولا يمكن الوصول إليه.")
        elif "Video unavailable" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="هذا الفيديو غير متوفر أو تم حذفه.")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"فشل استخراج الروابط: {error_msg}"
            )

@app.post("/api/extract", tags=["Extractor"])
def extract_post(request_data: ExtractRequest):
    """
    استخراج الروابط المباشرة المؤقتة لجميع الجودات عبر طلب POST.
    """
    return handle_extraction(request_data.url)

@app.get("/api/extract", tags=["Extractor"])
def extract_get(url: str = Query(..., description="رابط فيديو اليوتيوب")):
    """
    استخراج الروابط المباشرة المؤقتة لجميع الجودات عبر طلب GET (مناسب للتجربة السريعة في المتصفح).
    """
    return handle_extraction(url)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
