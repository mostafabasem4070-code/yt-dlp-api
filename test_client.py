"""
أداة اختبار سريعة للـ API (محلياً أو على Railway).
الاستخدام:
  python test_client.py
أو:
  python test_client.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
"""
import sys
import json
import urllib.request
import urllib.parse

# يمكنك تغيير هذا الرابط إلى رابط Railway بعد الرفع:
# مثال: API_BASE_URL = "https://your-app-name.up.railway.app"
API_BASE_URL = "http://127.0.0.1:8000"

def test_api(target_video_url: str):
    endpoint = f"{API_BASE_URL}/api/extract"
    payload = json.dumps({"url": target_video_url}).encode("utf-8")
    
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"[*] جاري إرسال الطلب إلى: {endpoint}")
    print(f"[*] رابط الفيديو: {target_video_url}\n")

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            video_info = result.get("video_info", {})
            streams = result.get("streams", {})

            print("=" * 60)
            print(f"[✓] تم جلب بيانات الفيديو بنجاح:")
            print(f"    - العنوان: {video_info.get('title')}")
            print(f"    - القناة: {video_info.get('uploader')}")
            print(f"    - المدة: {video_info.get('duration_readable')}")
            print(f"    - المشاهدات: {video_info.get('view_count'):,}")
            print("=" * 60)

            print(f"\n1. فيديوهات مدمجة بالصوت (جاهزة للتشغيل والتحميل المباشر):")
            for item in streams.get("video_with_audio", []):
                print(f"   • [{item['ext']}] {item['quality_note']} ({item['resolution']}) - الحجم: {item['filesize_readable'] or 'غير محدد'}")
                print(f"     رابط البث السريع (Proxy): {item['url'][:80]}...")
                if 'direct_url' in item:
                    print(f"     رابط يوتيوب المباشر: {item['direct_url'][:80]}...\n")
                else:
                    print("")

            print(f"\n2. فيديوهات بجودة عالية (فيديو فقط بدون صوت - 1080p, 4K):")
            for item in streams.get("video_only", [])[:5]:  # عرض أول 5 جودات
                print(f"   • [{item['ext']}] {item['quality_note']} ({item['resolution']}) - الحجم: {item['filesize_readable'] or 'غير محدد'}")
                print(f"     رابط البث السريع (Proxy): {item['url'][:80]}...")
                if 'direct_url' in item:
                    print(f"     رابط يوتيوب المباشر: {item['direct_url'][:80]}...\n")
                else:
                    print("")

            print(f"\n3. مسارات صوتية فقط (Audio Streams):")
            for item in streams.get("audio_only", [])[:3]:
                print(f"   • [{item['ext']}] {item['abr_kbps']} kbps - الحجم: {item['filesize_readable'] or 'غير محدد'}")
                print(f"     رابط البث السريع (Proxy): {item['url'][:80]}...")
                if 'direct_url' in item:
                    print(f"     رابط يوتيوب المباشر: {item['direct_url'][:80]}...\n")
                else:
                    print("")

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"[X] خطأ من السيرفر ({e.code}): {error_body}")
    except Exception as e:
        print(f"[X] حدث خطأ أثناء الاتصال: {e}")

if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_api(test_url)
