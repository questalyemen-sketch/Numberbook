"""
Sherlock Service
================

واجهة ربط Sherlock مع Numberbook.

الوظائف:
- تنظيف Username
- البحث باستخدام Sherlock
- تشغيل البحث في Thread
- استخراج النتائج المؤكدة
- تنسيق النتائج لـ Telegram
- تقسيم الرسائل الطويلة

ملاحظة:
عدم العثور على حساب لا يعني بالضرورة أن الحساب غير موجود؛
قد تفشل بعض المواقع أو تحجب طلبات البحث.
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

# مهلة كل موقع
DEFAULT_TIMEOUT = 10

# أقصى طول لاسم المستخدم
MAX_USERNAME_LENGTH = 50

# عدد الأحرف المسموحة
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

    if username is None:
        raise ValueError(
            "لم يتم إدخال Username."
        )

    username = str(username).strip()

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
    تحميل مواقع Sherlock واستبعاد المواقع المصنفة NSFW.
    """

    sites = SitesInformation(
        honor_exclusions=True
    )

    # لا نريد مواقع NSFW في بوت عام
    try:
        sites.remove_nsfw_sites()
    except Exception as error:
        print(
            f"⚠️ تعذر إزالة NSFW sites: {error}"
        )

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

    يعيد النتائج التي أعلن Sherlock أنها CLAIMED.
    """

    username = clean_username(
        username
    )

    # حماية timeout
    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT

    if timeout < 3:
        timeout = 3

    if timeout > 30:
        timeout = 30

    # --------------------------------------------------------
    # تحميل المواقع
    # --------------------------------------------------------

    site_data = load_sites()

    print(
        f"🔎 Sherlock: searching '{username}' "
        f"across {len(site_data)} sites..."
    )

    # --------------------------------------------------------
    # إشعارات Sherlock
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

    found_results: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # تحليل النتائج
    # --------------------------------------------------------

    for site_name, data in results.items():

        if not data:
            continue

        status = data.get(
            "status"
        )

        # ----------------------------------------------------
        # الحساب موجود
        # ----------------------------------------------------

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
        f"✅ Sherlock: found "
        f"{len(found_results)} result(s)"
    )

    return found_results


# ============================================================
# Async Search
# ============================================================

async def search_username_async(
    username: str,
    timeout: int = DEFAULT_TIMEOUT
) -> List[Dict[str, Any]]:
    """
    تشغيل Sherlock في Thread منفصل.

    هذا يمنع البحث من تجميد Telegram Bot.
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
# تنسيق النتائج
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

    # --------------------------------------------------------
    # لا توجد نتائج
    # --------------------------------------------------------

    if not results:

        return (
            "🔎 <b>Sherlock OSINT</b>\n\n"
            f"👤 Username: "
            f"<code>{username}</code>\n\n"
            "❌ <b>لم يتم العثور على نتائج مؤكدة.</b>\n\n"
            "قد يعني ذلك عدم وجود تطابق، "
            "أو أن بعض المواقع لم تسمح بالتحقق."
        )

    # --------------------------------------------------------
    # بداية الرسالة
    # --------------------------------------------------------

    lines = [
        "🔎 <b>Sherlock OSINT</b>",
        "",
        f"👤 Username: "
        f"<code>{username}</code>",
        "",
        f"✅ تم العثور على "
        f"<b>{len(results)}</b> تطابقات:",
        "",
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]

    # --------------------------------------------------------
    # النتائج
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # التنبيه
    # --------------------------------------------------------

    lines.extend([
        "━━━━━━━━━━━━━━━━━━",
        "",
        "⚠️ <b>تنبيه:</b>",
        "وجود Username مطابق لا يثبت أن "
        "الحسابات تعود إلى نفس الشخص.",
        "",
        "🔎 النتائج هي تطابقات محتملة "
        "لاسم المستخدم فقط."
    ])

    return "\n".join(
        lines
    )


# ============================================================
# تقسيم رسائل Telegram
# ============================================================

def split_message(
    text: str,
    max_length: int = 4000
) -> List[str]:
    """
    تقسيم الرسالة الطويلة إلى أجزاء.
    """

    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []

    remaining = text

    while len(remaining) > max_length:

        # ----------------------------------------------------
        # حاول التقسيم عند آخر سطر
        # ----------------------------------------------------

        split_at = remaining.rfind(
            "\n",
            0,
            max_length
        )

        # إذا لم نجد سطرًا مناسبًا
        if split_at <= 0:

            split_at = max_length

        chunk = remaining[
            :split_at
        ]

        chunks.append(
            chunk
        )

        remaining = remaining[
            split_at:
        ].lstrip("\n")

    if remaining:

        chunks.append(
            remaining
        )

    return chunks


# ============================================================
# البحث + التنسيق
# ============================================================

async def search_and_format(
    username: str,
    timeout: int = DEFAULT_TIMEOUT
) -> str:
    """
    تنفيذ البحث ثم تنسيق النتائج.
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
    إرجاع معلومات Sherlock Service.
    """

    return {
        "name": "Sherlock",
        "type": "Username OSINT",
        "timeout": DEFAULT_TIMEOUT,
        "nsfw_sites": False,
        "status": "ready"
    }


# ============================================================
# اختبار داخلي اختياري
# ============================================================

if __name__ == "__main__":

    print(
        "🕵️ Sherlock Service Test"
    )

    test_username = "github"

    try:

        result = search_username(
            test_username
        )

        print(
            format_results(
                test_username,
                result
            )
        )

    except Exception as error:

        print(
            "❌ Test Error:"
        )

        print(
            repr(error)
        )