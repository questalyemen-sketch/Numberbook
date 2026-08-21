"""
ملف اختبار منفصل - لا يلمس main.py
"""

import asyncio
import html

# استيراد من ملف platform_enrichment
from platform_enrichment import enrich_account, enrich_multiple_accounts, format_enrichment_result


async def test_github():
    """
    اختبار GitHub فقط
    """
    print("
" + "=" * 60)
    print("🧪 اختبار GitHub Enrichment")
    print("=" * 60 + "
")
    
    username = input("👤 أدخل Username (أو اضغط Enter لـ 'torvalds'): ").strip()
    
    if not username:
        username = "torvalds"
    
    print(f"
🔎 جاري البحث عن: {username} ...
")
    
    result = await enrich_account("github", username, timeout=8)
    
    print("📊 النتيجة:
")
    
    if result["found"]:
        print(f"✅ Found: YES")
        print(f"👤 الاسم: {result['display_name']}")
        print(f"📝 النبذة: {result['bio']}")
        print(f"👥 المتابعون: {result['followers']}")
        print(f"📊 المشاريع: {result['posts']}")
        print(f"📍 الموقع: {result['location']}")
        print(f"🔗 الرابط: {result['url']}")
    else:
        print(f"❌ Found: NO")
        print(f"🔗 الرابط: {result['url']}")
    
    if result.get("extra", {}).get("error"):
        print(f"
⚠️ خطأ: {result['extra']['error']}")
    
    print("
" + "=" * 60 + "
")


async def test_reddit():
    """
    اختبار Reddit
    """
    print("
" + "=" * 60)
    print("🧪 اختبار Reddit Enrichment")
    print("=" * 60 + "
")
    
    username = input("👤 أدخل Username (أو اضغط Enter لـ 'spez'): ").strip()
    
    if not username:
        username = "spez"
    
    print(f"
🔎 جاري البحث عن: {username} ...
")
    
    result = await enrich_account("reddit", username, timeout=8)
    
    print("📊 النتيجة:
")
    
    if result["found"]:
        print(f"✅ Found: YES")
        print(f"👤 الاسم: {result['display_name']}")
        print(f"📊 Karma: {result['posts']}")
        print(f"🔗 الرابط: {result['url']}")
    else:
        print(f"❌ Found: NO")
        print(f"🔗 الرابط: {result['url']}")
    
    if result.get("extra", {}).get("error"):
        print(f"
⚠️ خطأ: {result['extra']['error']}")
    
    print("
" + "=" * 60 + "
")


async def test_multi():
    """
    اختبار عدة منصات معًا
    """
    print("
" + "=" * 60)
    print("🧪 اختبار Multi-Platform Enrichment")
    print("=" * 60 + "
")
    
    username = input("👤 أدخل Username (أو اضغط Enter لـ 'github'): ").strip()
    
    if not username:
        username = "github"
    
    print(f"
🔎 جاري البحث في GitHub و Reddit ...
")
    
    results = await enrich_multiple_accounts(
        platforms=["github", "reddit"],
        username=username,
        timeout_per_platform=8,
        global_timeout=20
    )
    
    formatted = format_enrichment_result(results)
    print(formatted)
    
    print("
" + "=" * 60 + "
")


async def main():
    """
    قائمة الاختبار
    """
    while True:
        print("
")
        print("🚀 " + "=" * 58)
        print("🚀  Platform Enrichment - Test Suite")
        print("🚀 " + "=" * 58)
        print("
")
        print("1️⃣  اختبار GitHub")
        print("2️⃣  اختبار Reddit")
        print("3️⃣  اختبار Multi-Platform")
        print("0️⃣  خروج")
        print("
")
        
        choice = input("اختر (1/2/3/0): ").strip()
        
        if choice == "1":
            await test_github()
        elif choice == "2":
            await test_reddit()
        elif choice == "3":
            await test_multi()
        elif choice == "0":
            print("
✅ وداعًا!
")
            break
        else:
            print("
❌ اختر 1 أو 2 أو 3 أو 0
")


if __name__ == "__main__":
    asyncio.run(main())