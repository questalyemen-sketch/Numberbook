"""
Sherlock Service
================

واجهة ربط Sherlock مع Numberbook Telegram Bot.

يستخدم نسخة Sherlock المثبتة من:
https://github.com/questalyemen-sketch/sherlock

الوظائف:
- البحث عن Username
- تشغيل البحث في Thread حتى لا يتجمد البوت
- تنظيف النتائج
- تنسيق النتائج لتناسب Telegram
"""

import asyncio
import re
from typing import Any, Dict, List

from sherlock_project.sherlock import sherlock
from sherlock_project.sites import SitesInformation
from sherlock_project.result import QueryStatus
from sherlock_project.notify import QueryNotifyPrint


# ============================================================
# الإعدادات
# ============================================================

DEFAULT_TIMEOUT = 20

# الحد الأقصى لاسم المستخدم
MAX_USERNAME_LENGTH = 50

# الأحرف المسموحة في Username
USERNAME_PATTERN = re.compile(
    r"^[A-Za-z0-9._-]{1,50}$"
)


# ============================================================
# تنظيف Username
# ============================================================

def clean_username(username: str) -> str:
    """
    تنظيف والتحقق من Username.
    """

    if not username:
        raise ValueError(
            "لم يتم إدخال Username."
        )

    username = username.strip()

    # إزالة @
    if username.startswith("@"):
        username = username[1:]

    # إزالة المسافات
    username = username.strip()

    if not username:
        raise ValueError(
            "Username فارغ."
        )

    if len(username) > MAX_USERNAME_LENGTH:
        raise ValueError(
            "Username طويل جدًا."
        )

    if not USERNAME_PATTERN.fullmatch(username):
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

def load_sites() -> Dict[str, Any]:
    """
    تحميل قائمة المواقع التي سيبحث فيها Sherlock.

    يتم استبعاد المواقع المصنفة NSFW.
    """

    sites = SitesInformation(
        honor_exclusions=True
    )

    # استبعاد مواقع NSFW
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

    يعيد قائمة بالنتائج التي تم العثور عليها.
    """

    username = clean_username(username)

    # تحميل المواقع
    site_data = load_sites()

    # إنشاء نظام الإشعارات
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

    found_results: List[Dict[str, Any]] = []

    # معالجة النتائج
    for site_name, data in results.items():

        if not data:
            continue

        status = data.get("status")

        # الحساب موجود
        if status == QueryStatus.CLAIMED:

            url = data.get(
                "url_user",
                ""
            )

            found_results.append({
                "site": site_name,
                "url": url,
                "status": "found"
            })

    # ترتيب النتائج أبجديًا
    found_results.sort(
        key=lambda item: item.get(
            "site",
            ""
        ).lower()
    )

    return found_results


# ============================================================
# البحث Async
# ============================================================

async def search_username_async(
    username: str,
    timeout: int = DEFAULT_TIMEOUT
) -> List[Dict[str, Any]]:
    """
    تشغيل Sherlock في Thread منفصل.

    هذا يمنع Sherlock من تجميد بوت Telegram
    أثناء فحص المواقع.
    """

    return await asyncio.to_thread(
        search_username,
        username,
        timeout
    )


# ============================================================
# تنسيق نتيجة واحدة
# ============================================================

def format_result_item(
    index: int,
    result: Dict[str, Any]
) -> str:
    """
    تنسيق نتيجة واحدة.
    """

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
            f"{index}. 🌐 <b>{site}</b>\n"
            f"   {url}"
        )

    return (
        f"{index}. 🌐 <b>{site}</b>"
    )


# ============================================================
# تنسيق جميع النتائج
# ============================================================

def format_results(
    username: str,
    results: List[Dict[str, Any]]
) -> str:
    """
    تحويل نتائج Sherlock إلى رسالة Telegram.
    """

    username = clean_username(
        username
    )

    # لا توجد نتائج
    if not results:

        return (
            "🔎 <b>Sherlock OSINT</b>\n\n"
            f"👤 Username: "
            f"<code>{username}</code>\n\n"
            "❌ <b>لم يتم العثور على نتائج.</b>\n\n"
            "لم يتم العثور على حسابات مطابقة "
            "ضمن المواقع التي تم فحصها."
        )

    lines = [
        "🔎 <b>Sherlock OSINT</b>",
        "",
        f"👤 Username: "
        f"<code>{username}</code>",
        f"✅ النتائج: "
        f"<b>{len(results)}</b>",
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
        "وجود Username مطابق لا يعني أن "
        "الحسابات تعود بالضرورة إلى نفس الشخص."
    ])

    return "\n".join(lines)


# ============================================================
# تقسيم رسالة Telegram
# ============================================================

def split_message(
    text: str,
    max_length: int = 4000
) -> List[str]:
    """
    تقسيم النص الطويل إلى أجزاء مناسبة لـTelegram.
    """

    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []

    while len(text) > max_length:

        # محاولة التقسيم عند سطر
        split_at = text.rfind(
            "\n",
            0,
            max_length
        )

        if split_at <= 0:
            split_at = max_length

        chunks.append(
            text[:split_at]
        )

        text = text[
            split_at:
        ].lstrip("\n")

    if text:
        chunks.append(text)

    return chunks


# ============================================================
# دالة موحدة للبحث والتنسيق
# ============================================================

async def search_and_format(
    username: str,
    timeout: int = DEFAULT_TIMEOUT
) -> str:
    """
    تنفيذ البحث ثم إرجاع النتيجة
    جاهزة للإرسال إلى Telegram.
    """

    username = clean_username(
        username
    )

    results = await search_username_async(
        username,
        timeout
    )

    return format_results(
        username,
        results
    )


# ============================================================
# معلومات الخدمة
# ============================================================

def get_service_info() -> Dict[str, Any]:
    """
    معلومات عن خدمة Sherlock.
    """

    return {
        "name": "Sherlock",
        "type": "Username OSINT",
        "timeout": DEFAULT_TIMEOUT,
        "nsfw_sites": False,
        "status": "ready"
    }