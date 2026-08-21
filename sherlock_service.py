"""
Sherlock Service
================

Sherlock integration for Numberbook Telegram Bot.

يدعم البحث المحدد في أشهر المنصات بدل فحص 400+ موقع.

المنصات:
- Telegram
- Instagram
- Facebook
- Twitter / X
- LinkedIn
- TikTok
- YouTube
- GitHub
- Reddit
- Pinterest
"""

import asyncio
import re
from typing import Any, Dict, List, Optional

from sherlock_project.sherlock import sherlock
from sherlock_project.sites import SitesInformation
from sherlock_project.result import QueryStatus
from sherlock_project.notify import QueryNotifyPrint


# ============================================================
# الإعدادات
# ============================================================

DEFAULT_TIMEOUT = 8

MAX_USERNAME_LENGTH = 50

USERNAME_PATTERN = re.compile(
    r"^[A-Za-z0-9._-]{1,50}$"
)


# ============================================================
# المنصات المدعومة في البوت
# ============================================================

PLATFORM_ALIASES = {

    "telegram": [
        "Telegram"
    ],

    "instagram": [
        "Instagram"
    ],

    "facebook": [
        "Facebook"
    ],

    "twitter": [
        "Twitter"
    ],

    "x": [
        "Twitter"
    ],

    "linkedin": [
        "LinkedIn"
    ],

    "tiktok": [
        "TikTok"
    ],

    "youtube": [
        "YouTube"
    ],

    "github": [
        "GitHub"
    ],

    "reddit": [
        "Reddit"
    ],

    "pinterest": [
        "Pinterest"
    ]
}


# ============================================================
# أسماء العرض في Telegram
# ============================================================

PLATFORM_NAMES = {

    "telegram": "📱 Telegram",

    "instagram": "📸 Instagram",

    "facebook": "👤 Facebook",

    "twitter": "𝕏 X / Twitter",

    "linkedin": "💼 LinkedIn",

    "tiktok": "🎵 TikTok",

    "youtube": "▶️ YouTube",

    "github": "🐙 GitHub",

    "reddit": "🤖 Reddit",

    "pinterest": "📌 Pinterest"
}


# ============================================================
# المنصات الافتراضية العشر
# ============================================================

DEFAULT_PLATFORMS = [
    "telegram",
    "instagram",
    "facebook",
    "twitter",
    "linkedin",
    "tiktok",
    "youtube",
    "github",
    "reddit",
    "pinterest"
]


# ============================================================
# تنظيف Username
# ============================================================

def clean_username(username: str) -> str:
    """
    تنظيف والتحقق من Username.
    """

    if username is None:

        raise ValueError(
            "لم يتم إدخال Username."
        )

    username = str(
        username
    ).strip()

    # إزالة @
    if username.startswith("@"):

        username = username[1:]

    username = username.strip()

    if not username:

        raise ValueError(
            "Username فارغ."
        )

    if len(username) > MAX_USERNAME_LENGTH:

        raise ValueError(
            "Username طويل جدًا."
        )

    if not USERNAME_PATTERN.fullmatch(
        username
    ):

        raise ValueError(
            "Username غير صالح.\n\n"
            "استخدم الأحرف الإنجليزية والأرقام "
            "والرموز التالية فقط:\n"
            ".  _  -"
        )

    return username


# ============================================================
# تحميل مواقع Sherlock
# ============================================================

def load_all_sites() -> Dict[str, Any]:
    """
    تحميل بيانات جميع المواقع من Sherlock.
    """

    sites = SitesInformation(
        honor_exclusions=True
    )

    # إزالة NSFW
    try:

        sites.remove_nsfw_sites()

    except Exception as error:

        print(
            f"⚠️ NSFW filter error: {error}"
        )

    return {
        site.name: site.information
        for site in sites
    }


# ============================================================
# البحث عن اسم موقع Sherlock
# ============================================================

def find_site_name(
    all_sites: Dict[str, Any],
    aliases: List[str]
) -> Optional[str]:
    """
    العثور على الاسم الحقيقي للموقع داخل Sherlock.

    المقارنة غير حساسة لحالة الأحرف.
    """

    normalized = {
        name.lower(): name
        for name in all_sites
    }

    for alias in aliases:

        result = normalized.get(
            alias.lower()
        )

        if result:

            return result

    return None


# ============================================================
# بناء قائمة المواقع المختارة
# ============================================================

def build_selected_sites(
    selected_platforms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    بناء site_data يحتوي فقط على المنصات المطلوبة.
    """

    all_sites = load_all_sites()

    if not selected_platforms:

        selected_platforms = DEFAULT_PLATFORMS

    selected_sites = {}

    missing = []

    for platform in selected_platforms:

        platform_key = str(
            platform
        ).lower().strip()

        aliases = PLATFORM_ALIASES.get(
            platform_key
        )

        if not aliases:

            missing.append(
                platform_key
            )

            continue

        site_name = find_site_name(
            all_sites,
            aliases
        )

        if site_name:

            selected_sites[
                site_name
            ] = all_sites[
                site_name
            ]

        else:

            missing.append(
                platform_key
            )

    if missing:

        print(
            "⚠️ Sherlock platforms not found:",
            ", ".join(missing)
        )

    print(
        f"🎯 Selected Sherlock sites: "
        f"{len(selected_sites)}"
    )

    return selected_sites


# ============================================================
# البحث الأساسي
# ============================================================

def search_username(
    username: str,
    timeout: int = DEFAULT_TIMEOUT,
    selected_platforms: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    البحث عن Username في المنصات المحددة فقط.
    """

    username = clean_username(
        username
    )

    # --------------------------------------------------------
    # حماية timeout
    # --------------------------------------------------------

    try:

        timeout = int(
            timeout
        )

    except (
        TypeError,
        ValueError
    ):

        timeout = DEFAULT_TIMEOUT

    timeout = max(
        3,
        min(timeout, 20)
    )

    # --------------------------------------------------------
    # بناء المواقع المختارة
    # --------------------------------------------------------

    site_data = build_selected_sites(
        selected_platforms
    )

    if not site_data:

        raise RuntimeError(
            "لم يتم العثور على أي منصة "
            "صالحة للبحث."
        )

    print(
        f"🔎 Sherlock searching: "
        f"{username}"
    )

    print(
        f"🌐 Sites: "
        f"{', '.join(site_data.keys())}"
    )

    # --------------------------------------------------------
    # Notify
    # --------------------------------------------------------

    query_notify = QueryNotifyPrint(
        result=None,
        verbose=False,
        print_all=False,
        browse=False
    )

    # --------------------------------------------------------
    # تشغيل Sherlock
    # --------------------------------------------------------

    results = sherlock(
        username=username,
        site_data=site_data,
        query_notify=query_notify,
        timeout=timeout
    )

    found_results = []

    # --------------------------------------------------------
    # تحليل النتائج
    # --------------------------------------------------------

    for site_name, data in results.items():

        if not data:

            continue

        status_object = data.get(
            "status"
        )

        # ====================================================
        # الإصدار الحالي من Sherlock يعيد QueryResult
        # ====================================================

        if hasattr(
            status_object,
            "status"
        ):

            status = (
                status_object.status
            )

        else:

            status = status_object

        # ----------------------------------------------------
        # الحساب موجود
        # ----------------------------------------------------

        if status == QueryStatus.CLAIMED:

            url = data.get(
                "url_user"
            )

            if not url:

                url_main = data.get(
                    "url_main",
                    ""
                )

                if url_main:

                    url = (
                        url_main.rstrip("/")
                        + "/"
                        + username
                    )

            found_results.append({

                "site": site_name,

                "url": url or "",

                "status": "found"

            })

    # --------------------------------------------------------
    # ترتيب النتائج
    # --------------------------------------------------------

    found_results.sort(
        key=lambda item: str(
            item.get(
                "site",
                ""
            )
        ).lower()
    )

    print(
        f"✅ Sherlock found: "
        f"{len(found_results)}"
    )

    return found_results


# ============================================================
# Async
# ============================================================

async def search_username_async(
    username: str,
    timeout: int = DEFAULT_TIMEOUT,
    selected_platforms: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    تشغيل Sherlock في Thread منفصل.
    """

    return await asyncio.to_thread(
        search_username,
        username,
        timeout,
        selected_platforms
    )


# ============================================================
# تنسيق نتيجة واحدة
# ============================================================

def format_result_item(
    index: int,
    result: Dict[str, Any]
) -> str:

    site = result.get(
        "site",
        "Unknown"
    )

    url = result.get(
        "url",
        ""
    )

    if url:

        return (
            f"{index}. 🌐 "
            f"<b>{site}</b>\n"
            f"   🔗 {url}"
        )

    return (
        f"{index}. 🌐 "
        f"<b>{site}</b>"
    )


# ============================================================
# تنسيق النتائج
# ============================================================

def format_results(
    username: str,
    results: List[Dict[str, Any]]
) -> str:

    username = clean_username(
        username
    )

    if not results:

        return (
            "🕵️ <b>Sherlock</b>\n\n"

            f"👤 Username:\n"
            f"<code>{username}</code>\n\n"

            "❌ <b>لم يتم العثور على حسابات مؤكدة "
            "في المنصات المحددة.</b>\n\n"

            "⚠️ قد تكون بعض المنصات قد حجبت "
            "أو رفضت طلب التحقق."
        )

    lines = [

        "🕵️ <b>Sherlock</b>",

        "",

        f"👤 Username:\n"
        f"<code>{username}</code>",

        "",

        f"✅ تم العثور على "
        f"<b>{len(results)}</b> حساب:",

        "",

        "━━━━━━━━━━━━━━━━━━",

        ""
    ]

    for index, result in enumerate(
        results,
        start=1
    ):

        lines.append(
            format_result_item(
                index,
                result
            )
        )

        lines.append("")

    lines.extend([

        "━━━━━━━━━━━━━━━━━━",

        "",

        "⚠️ <b>تنبيه:</b>",

        "تطابق Username لا يثبت أن "
        "الحسابات تعود إلى نفس الشخص."
    ])

    return "\n".join(
        lines
    )


# ============================================================
# تقسيم الرسائل
# ============================================================

def split_message(
    text: str,
    max_length: int = 4000
) -> List[str]:

    if not text:

        return []

    if len(text) <= max_length:

        return [text]

    chunks = []

    remaining = text

    while len(remaining) > max_length:

        split_at = remaining.rfind(
            "\n",
            0,
            max_length
        )

        if split_at <= 0:

            split_at = max_length

        chunks.append(
            remaining[:split_at]
        )

        remaining = (
            remaining[
                split_at:
            ].lstrip("\n")
        )

    if remaining:

        chunks.append(
            remaining
        )

    return chunks


# ============================================================
# بحث + تنسيق
# ============================================================

async def search_and_format(
    username: str,
    timeout: int = DEFAULT_TIMEOUT,
    selected_platforms: Optional[List[str]] = None
) -> str:

    username = clean_username(
        username
    )

    results = await search_username_async(
        username,
        timeout,
        selected_platforms
    )

    return format_results(
        username,
        results
    )


# ============================================================
# معلومات المنصات
# ============================================================

def get_platforms() -> Dict[str, str]:
    """
    إرجاع المنصات التي سيعرضها البوت للمستخدم.
    """

    return {
        key: PLATFORM_NAMES[key]
        for key in DEFAULT_PLATFORMS
    }


# ============================================================
# معلومات الخدمة
# ============================================================

def get_service_info() -> Dict[str, Any]:

    return {

        "name": "Sherlock",

        "type": "Username OSINT",

        "timeout": DEFAULT_TIMEOUT,

        "platforms": len(
            DEFAULT_PLATFORMS
        ),

        "nsfw_sites": False,

        "status": "ready"
    }


# ============================================================
# اختبار محلي
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 50
    )

    print(
        "🕵️ Sherlock Service Test"
    )

    print(
        "=" * 50
    )

    username = "github"

    try:

        results = search_username(
            username
        )

        print()

        print(
            format_results(
                username,
                results
            )
        )

    except Exception as error:

        print(
            "❌ Error:"
        )

        print(
            repr(error)
        )