"""
Platform Enrichment Layer

هذا الملف مسؤول عن جمع البيانات العامة المتاحة من حسابات المنصات الاجتماعية
بعد العثور عليها عبر Sherlock.

الهدف:
- توحيد هيكل البيانات من جميع المنصات
- استخدام APIs الرسمية عندما تكون متاحة
- عدم تجاوز أي حماية أو قيود
- التعامل مع الأخطاء بشكل آمن

المنصات المدعومة حاليًا:
✅ GitHub - API رسمي
✅ Reddit - API عام
⏳ باقي المنصات - قيد التطوير
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List


# =========================================================
# الهيكل الموحد للنتائج
# =========================================================

def create_empty_result(
    platform: str,
    username: str,
    url: str
) -> Dict[str, Any]:
    """
    إنشاء هيكل نتيجة فارغ موحد لجميع المنصات.
    
    جميع المنصات يجب أن تعيد هذا الهيكل مع ملء القيم المتاحة فقط.
    """
    return {
        "platform": platform,
        "username": username,
        "url": url,
        "found": False,
        "display_name": None,
        "bio": None,
        "avatar": None,
        "location": None,
        "website": None,
        "followers": None,
        "following": None,
        "posts": None,
        "account_type": None,
        "extra": {}
    }


# =========================================================
# GitHub Enrichment
# =========================================================

async def get_github_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من GitHub باستخدام API الرسمي.
    
    API: https://api.github.com/users/{username}
    
    البيانات المتاحة:
    - name (display_name)
    - bio
    - avatar_url
    - location
    - blog (website)
    - public_repos (posts)
    - followers
    - following
    - type (account_type)
    """
    result = create_empty_result(
        platform="GitHub",
        username=username,
        url=f"https://github.com/{username}"
    )
    
    api_url = f"https://api.github.com/users/{username}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Numberbook-Sherlock-Bot"
    }
    
    try:
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            
            async with session.get(
                api_url,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    
                    data = await response.json()
                    
                    result["found"] = True
                    result["display_name"] = data.get("name")
                    result["bio"] = data.get("bio")
                    result["avatar"] = data.get("avatar_url")
                    result["location"] = data.get("location")
                    result["website"] = data.get("blog")
                    result["followers"] = data.get("followers")
                    result["following"] = data.get("following")
                    result["posts"] = data.get("public_repos")
                    result["account_type"] = data.get("type")
                    
                    result["extra"] = {
                        "company": data.get("company"),
                        "hireable": data.get("hireable"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "public_gists": data.get("public_gists")
                    }
                    
                elif response.status == 404:
                    # المستخدم غير موجود
                    result["found"] = False
                    
                elif response.status == 403:
                    # Rate limit
                    result["found"] = True
                    result["extra"]["error"] = "Rate limit exceeded"
                    
                else:
                    result["extra"]["error"] = f"HTTP {response.status}"
                    
    except asyncio.TimeoutError:
        result["extra"]["error"] = "Timeout"
        
    except aiohttp.ClientError as error:
        result["extra"]["error"] = str(error)[:100]
        
    except Exception as error:
        result["extra"]["error"] = f"Unexpected: {str(error)[:100]}"
    
    return result


# =========================================================
# Reddit Enrichment
# =========================================================

async def get_reddit_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من Reddit باستخدام JSON API.
    
    API: https://www.reddit.com/user/{username}/about.json
    
    البيانات المتاحة:
    - name (display_name)
    - icon_img (avatar)
    - total_karma (posts)
    - created (account age)
    - has_verified_email
    - is_employee
    - is_mod
    - is_gold
    """
    result = create_empty_result(
        platform="Reddit",
        username=username,
        url=f"https://www.reddit.com/user/{username}"
    )
    
    api_url = f"https://www.reddit.com/user/{username}/about.json"
    
    headers = {
        "User-Agent": "Numberbook-Sherlock-Bot/1.0"
    }
    
    try:
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            
            async with session.get(
                api_url,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    
                    data = await response.json()
                    
                    user_data = data.get("data", {})
                    
                    if user_data:
                        
                        result["found"] = True
                        result["display_name"] = user_data.get("name")
                        result["avatar"] = user_data.get("icon_img")
                        result["posts"] = user_data.get("total_karma")
                        result["account_type"] = "gold" if user_data.get("is_gold") else "standard"
                        
                        result["extra"] = {
                            "comment_karma": user_data.get("comment_karma"),
                            "link_karma": user_data.get("link_karma"),
                            "created_utc": user_data.get("created_utc"),
                            "has_verified_email": user_data.get("has_verified_email"),
                            "is_employee": user_data.get("is_employee"),
                            "is_mod": user_data.get("is_mod"),
                            "is_gold": user_data.get("is_gold"),
                            "subreddit": user_data.get("subreddit")
                        }
                        
                    else:
                        result["found"] = False
                    
                elif response.status == 404:
                    result["found"] = False
                    
                elif response.status == 429:
                    # Rate limit
                    result["found"] = True
                    result["extra"]["error"] = "Rate limit exceeded"
                    
                else:
                    result["extra"]["error"] = f"HTTP {response.status}"
                    
    except asyncio.TimeoutError:
        result["extra"]["error"] = "Timeout"
        
    except aiohttp.ClientError as error:
        result["extra"]["error"] = str(error)[:100]
        
    except Exception as error:
        result["extra"]["error"] = f"Unexpected: {str(error)[:100]}"
    
    return result


# =========================================================
# Telegram Enrichment (Placeholder)
# =========================================================

async def get_telegram_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من Telegram.
    
    ملاحظة: Telegram لا يوفر API عام للبيانات الشخصية بدون تسجيل دخول.
    هذه الدالة حالياً ترجع هيكل فارغ كـ placeholder.
    
    مستقبلاً يمكن استخدام:
    - Telegram Bot API (محدود جداً)
    - Telegram Client API (يتطلب تسجيل دخول)
    """
    result = create_empty_result(
        platform="Telegram",
        username=username,
        url=f"https://t.me/{username}"
    )
    
    # TODO: تنفيذ عند توفر طريقة آمنة وقانونية
    result["extra"]["status"] = "Not implemented - API limitations"
    
    return result


# =========================================================
# Instagram Enrichment (Placeholder)
# =========================================================

async def get_instagram_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من Instagram.
    
    ملاحظة: Instagram يفرض قيودًا صارمة على scraping.
    هذه الدالة حالياً ترجع هيكل فارغ كـ placeholder.
    
    مستقبلاً يمكن استخدام:
    - Instagram Basic Display API (يتطلب OAuth)
    - Graph API (للحسابات التجارية)
    """
    result = create_empty_result(
        platform="Instagram",
        username=username,
        url=f"https://instagram.com/{username}"
    )
    
    # TODO: تنفيذ عند توفر API مناسب
    result["extra"]["status"] = "Not implemented - API limitations"
    
    return result


# =========================================================
# Facebook Enrichment (Placeholder)
# =========================================================

async def get_facebook_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من Facebook.
    
    ملاحظة: Facebook يفرض قيودًا صارمة جدًا.
    هذه الدالة حالياً ترجع هيكل فارغ كـ placeholder.
    """
    result = create_empty_result(
        platform="Facebook",
        username=username,
        url=f"https://facebook.com/{username}"
    )
    
    # TODO: تنفيذ عند توفر API مناسب
    result["extra"]["status"] = "Not implemented - API limitations"
    
    return result


# =========================================================
# X/Twitter Enrichment (Placeholder)
# =========================================================

async def get_x_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من X (Twitter).
    
    ملاحظة: Twitter API v2 يتطلب مصادقة.
    هذه الدالة حالياً ترجع هيكل فارغ كـ placeholder.
    """
    result = create_empty_result(
        platform="X",
        username=username,
        url=f"https://twitter.com/{username}"
    )
    
    # TODO: تنفيذ عند توفر API مناسب
    result["extra"]["status"] = "Not implemented - API limitations"
    
    return result


# =========================================================
# LinkedIn Enrichment (Placeholder)
# =========================================================

async def get_linkedin_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من LinkedIn.
    
    ملاحظة: LinkedIn يفرض قيودًا صارمة ويتطلب تسجيل دخول.
    هذه الدالة حالياً ترجع هيكل فارغ كـ placeholder.
    """
    result = create_empty_result(
        platform="LinkedIn",
        username=username,
        url=f"https://linkedin.com/in/{username}"
    )
    
    # TODO: تنفيذ عند توفر API مناسب
    result["extra"]["status"] = "Not implemented - API limitations"
    
    return result


# =========================================================
# TikTok Enrichment (Placeholder)
# =========================================================

async def get_tiktok_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من TikTok.
    
    ملاحظة: TikTok API محدود.
    هذه الدالة حالياً ترجع هيكل فارغ كـ placeholder.
    """
    result = create_empty_result(
        platform="TikTok",
        username=username,
        url=f"https://tiktok.com/@{username}"
    )
    
    # TODO: تنفيذ عند توفر API مناسب
    result["extra"]["status"] = "Not implemented - API limitations"
    
    return result


# =========================================================
# YouTube Enrichment (Placeholder)
# =========================================================

async def get_youtube_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من YouTube.
    
    ملاحظة: YouTube Data API v3 يتطلب API Key.
    هذه الدالة حالياً ترجع هيكل فارغ كـ placeholder.
    
    مستقبلاً يمكن استخدام:
    - YouTube Data API v3
    """
    result = create_empty_result(
        platform="YouTube",
        username=username,
        url=f"https://youtube.com/@{username}"
    )
    
    # TODO: تنفيذ عند توفر API Key
    result["extra"]["status"] = "Not implemented - API key required"
    
    return result


# =========================================================
# Pinterest Enrichment (Placeholder)
# =========================================================

async def get_pinterest_profile(
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    جمع البيانات العامة من Pinterest.
    
    ملاحظة: Pinterest API يتطلب مصادقة.
    هذه الدالة حالياً ترجع هيكل فارغ كـ placeholder.
    """
    result = create_empty_result(
        platform="Pinterest",
        username=username,
        url=f"https://pinterest.com/{username}"
    )
    
    # TODO: تنفيذ عند توفر API مناسب
    result["extra"]["status"] = "Not implemented - API limitations"
    
    return result


# =========================================================
# الدالة الموحدة للإنريشمنت
# =========================================================

PLATFORM_FUNCTIONS = {
    "github": get_github_profile,
    "reddit": get_reddit_profile,
    "telegram": get_telegram_profile,
    "instagram": get_instagram_profile,
    "facebook": get_facebook_profile,
    "x": get_x_profile,
    "linkedin": get_linkedin_profile,
    "tiktok": get_tiktok_profile,
    "youtube": get_youtube_profile,
    "pinterest": get_pinterest_profile
}


async def enrich_account(
    platform: str,
    username: str,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    دالة موحدة لجمع بيانات الحساب من أي منصة.
    
    المعاملات:
    - platform: اسم المنصة (github, reddit, telegram, ...)
    - username: اسم المستخدم
    - timeout: الوقت الأقصى للانتظار بالثواني
    
    الإرجاع:
    - Dict بالهيكل الموحد (create_empty_result)
    """
    platform_lower = platform.lower()
    
    if platform_lower not in PLATFORM_FUNCTIONS:
        return create_empty_result(
            platform=platform,
            username=username,
            url="#"
        )
    
    func = PLATFORM_FUNCTIONS[platform_lower]
    
    try:
        
        result = await func(
            username=username,
            timeout=timeout
        )
        
        return result
        
    except Exception as error:
        
        result = create_empty_result(
            platform=platform,
            username=username,
            url="#"
        )
        
        result["extra"]["error"] = f"Enrichment failed: {str(error)[:100]}"
        
        return result


# =========================================================
# Enrichment متوازي لعدة منصات
# =========================================================

async def enrich_multiple_accounts(
    platforms: List[str],
    username: str,
    timeout_per_platform: int = 8,
    global_timeout: int = 20
) -> List[Dict[str, Any]]:
    """
    جمع بيانات الحساب من عدة منصات بشكل متوازي.
    
    المعاملات:
    - platforms: قائمة أسماء المنصات
    - username: اسم المستخدم (نفسه لكل المنصات)
    - timeout_per_platform: timeout لكل منصة على حدة
    - global_timeout: timeout إجمالي لكل العملية
    
    الإرجاع:
    - List[Dict] بالهيكل الموحد لكل منصة
    """
    
    async def enrich_with_timeout(platform: str) -> Dict[str, Any]:
        try:
            return await asyncio.wait_for(
                enrich_account(platform, username, timeout_per_platform),
                timeout=timeout_per_platform
            )
        except asyncio.TimeoutError:
            result = create_empty_result(
                platform=platform,
                username=username,
                url="#"
            )
            result["extra"]["error"] = "Platform timeout"
            return result
        except Exception as error:
            result = create_empty_result(
                platform=platform,
                username=username,
                url="#"
            )
            result["extra"]["error"] = str(error)[:100]
            return result
    
    try:
        
        tasks = [
            enrich_with_timeout(platform)
            for platform in platforms
        ]
        
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=global_timeout
        )
        
        # معالجة الاستثناءات في النتائج
        final_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    create_empty_result(
                        platform=platforms[i],
                        username=username,
                        url="#"
                    )
                )
            else:
                final_results.append(result)
        
        return final_results
        
    except asyncio.TimeoutError:
        
        # Timeout إجمالي - نرجع ما حصلنا عليه
        return []


# =========================================================
# تنسيق النتيجة للعرض
# =========================================================

def format_enrichment_result(
    enrichment_results: List[Dict[str, Any]]
) -> str:
    """
    تنسيق نتائج الإنريشمنت للعرض في Telegram.
    
    الإرجاع:
    - نص HTML منسق
    """
    import html
    
    if not enrichment_results:
        return "❌ لا توجد نتائج للعرض."
    
    output_parts = []
    
    for result in enrichment_results:
        
        platform = result.get("platform", "Unknown")
        username = result.get("username", "Unknown")
        found = result.get("found", False)
        url = result.get("url", "#")
        
        # أيقونة الحالة
        if found:
            status_icon = "🟢"
            status_text = "FOUND"
        else:
            status_icon = "🔴"
            status_text = "NOT FOUND"
        
        # رأس القسم
        section = f"""
━━━━━━━━━━━━━━━━━━

{status_icon} <b>{html.escape(platform)}</b>
{status_text}
"""
        
        # إذا تم العثور على الحساب
        if found:
            
            display_name = result.get("display_name")
            bio = result.get("bio")
            followers = result.get("followers")
            posts = result.get("posts")
            location = result.get("location")
            website = result.get("website")
            account_type = result.get("account_type")
            
            details = []
            
            if display_name:
                details.append(f"👤 الاسم: {html.escape(str(display_name))}")
            
            if bio:
                details.append(f"📝 النبذة: {html.escape(str(bio))}")
            
            if followers is not None:
                details.append(f"👥 المتابعون: {followers}")
            
            if posts is not None:
                details.append(f"📊 المنشورات/الرصيد: {posts}")
            
            if location:
                details.append(f"📍 الموقع: {html.escape(str(location))}")
            
            if website:
                details.append(f"🌐 الموقع: {html.escape(str(website))}")
            
            if account_type:
                details.append(f"🏷 النوع: {html.escape(str(account_type))}")
            
            if details:
                section += "
".join(details) + "
"
            
            # الرابط
            section += f"
🔗 <a href='{html.escape(url)}'>{html.escape(url)}</a>"
        
        # معالجة الأخطاء
        extra = result.get("extra", {})
        error = extra.get("error")
        
        if error:
            section += f"

⚠️ <i>{html.escape(str(error))}</i>"
        
        output_parts.append(section)
    
    return "
".join(output_parts)


# =========================================================
__all__ = [
    "create_empty_result",
    "get_github_profile",
    "get_reddit_profile",
    "get_telegram_profile",
    "get_instagram_profile",
    "get_facebook_profile",
    "get_x_profile",
    "get_linkedin_profile",
    "get_tiktok_profile",
    "get_youtube_profile",
    "get_pinterest_profile",
    "enrich_account",
    "enrich_multiple_accounts",
    "format_enrichment_result"
]