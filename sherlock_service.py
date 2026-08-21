"""
Sherlock Service
================
واجهة بسيطة لربط Sherlock مع Numberbook Telegram Bot.

يستخدم نسخة Sherlock المثبتة من:
questalyemen-sketch/sherlock
"""

from typing import List, Dict, Any
import asyncio
import re

from sherlock_project.sherlock import sherlock
from sherlock_project.sites import SitesInformation
from sherlock_project.result import QueryStatus
from sherlock_project.notify import QueryNotifyPrint


# ============================================================
# إعدادات
# ============================================================

DEFAULT_TIMEOUT = 20

# منع إدخال أشياء ليست Username
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,50}$")


# ============================================================
# تحميل قائمة المواقع
# ============================================================

def _load_sites():
    """
    تحميل قائمة المواقع التي يستخدمها Sherlock.
    """

    sites = SitesInformation(
        honor_exclusions=True
    )

    # إزالة المواقع المصنفة NSFW
    sites.remove_nsfw_sites()

    return {
        site.name: site.information
        for site in sites
    }


# ============================================================
# البحث الأساسي
# ============================================================

def search_username(
    username: str,
    timeout: int = DEFAULT_TIMEOUT
) -> List[Dict[str, Any]]:
    """
    البحث عن Username باستخدام Sherlock.

    يعيد فقط النتائج التي تم العثور عليها.
    """

    username = username.strip()

    # إزالة @ إذا كتبها المستخدم
    if username.startswith("@"):
        username = username[1:]

    # التحقق من Username
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError(
            "Username غير صالح. استخدم الأحرف الإنجليزية "
            "والأرقام و . _ - فقط."
        )

    # تحميل المواقع
    site_data = _load_sites()

    # كائن الإشعارات الخاص بـSherlock
    query_notify = QueryNotifyPrint(
        result=None,
        verbose=False,
        print_all=False,
        browse=False
    )

    # تشغيل Sherlock
    results = sherlock(
        username=username,
        site_data=site_data,
        query_notify=query_notify,
        timeout=timeout
    )

    found = []

    for site_name, data in results.items():

        status = data.get("status")

        if status is None:
            continue

        # CLAIMED = الحساب موجود
        if status.status == QueryStatus.CLAIMED:

            found.append({
                "site": site_name,
                "url": data.get("url_user", ""),
                "status": "found"
            })

    return found


# ============================================================
# تشغيل البحث بدون تجميد بوت Telegram
# ============================================================

async def search_username_async(
    username: str,
    timeout: int = DEFAULT_TIMEOUT
) -> List[Dict[str, Any]]:
    """
    نسخة Async حتى لا يتجمد بوت Telegram أثناء البحث.
    """

    return await asyncio.to_thread(
        search_username,
        username,
        timeout
    )


# ============================================================
# تنسيق النتائج
# ============================================================

def format_results(
    username: str,
    results: List[Dict[str, Any]]
) -> str:
    """
    تحويل النتائج إلى رسالة مناسبة لـTelegram.
    """

    if not results:
        return (
            "🔎 <b>Sherlock</b>\n\n"
            f"👤 Username: <code>{username}</code>\n\n"
            "❌ لم يتم العثور على تطابقات مؤكدة."
        )

    lines = [
        "🔎 <b>Sherlock OSINT</b>",
        "",
        f"👤 Username: <code>{username}</code>",
        f"✅ النتائج: <b>{len(results)}</b>",
        "",
        "━━━━━━━━━━━━━━━━━━"
    ]

    for index, result in enumerate(results, 1):

        site = result.get("site", "Unknown")
        url = result.get("url", "")

        if url:
            lines.append(
                f"{index}. 🌐 <b>{site}</b>\n"
                f"   {url}"
            )
        else:
            lines.append(
                f"{index}. 🌐 <b>{site}</b>"
            )

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━",
        "⚠️ النتيجة تعني وجود تطابق لاسم المستخدم، "
        "ولا تثبت أن الحسابات تعود لنفس الشخص."
    ])

    return "\n".join(lines)