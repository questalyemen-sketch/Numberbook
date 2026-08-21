"""
ملف اختبار منفصل - لا يلمس main.py
نسخة مبسطة بدون مشاكل syntax
"""

import asyncio
from platform_enrichment import enrich_account


async def test_github():
    print("
" + "=" * 60)
    print("TEST: GitHub Enrichment")
    print("=" * 60 + "
")
    
    username = "torvalds"
    
    print("Searching for: " + username + " ...
")
    
    result = await enrich_account("github", username, timeout=8)
    
    print("RESULT:
")
    
    if result["found"]:
        print("Found: YES")
        print("Name: " + str(result["display_name"]))
        print("Bio: " + str(result["bio"]))
        print("Followers: " + str(result["followers"]))
        print("Posts: " + str(result["posts"]))
        print("Location: " + str(result["location"]))
        print("URL: " + result["url"])
    else:
        print("Found: NO")
        print("URL: " + result["url"])
    
    if result.get("extra", {}).get("error"):
        print("
Error: " + result["extra"]["error"])
    
    print("
" + "=" * 60 + "
")


async def test_reddit():
    print("
" + "=" * 60)
    print("TEST: Reddit Enrichment")
    print("=" * 60 + "
")
    
    username = "spez"
    
    print("Searching for: " + username + " ...
")
    
    result = await enrich_account("reddit", username, timeout=8)
    
    print("RESULT:
")
    
    if result["found"]:
        print("Found: YES")
        print("Name: " + str(result["display_name"]))
        print("Karma: " + str(result["posts"]))
        print("URL: " + result["url"])
    else:
        print("Found: NO")
        print("URL: " + result["url"])
    
    if result.get("extra", {}).get("error"):
        print("
Error: " + result["extra"]["error"])
    
    print("
" + "=" * 60 + "
")


async def main():
    print("
")
    print("STARTING TESTS...")
    print("
")
    
    await test_github()
    await test_reddit()
    
    print("ALL TESTS COMPLETED!")
    print("
")


if __name__ == "__main__":
    asyncio.run(main())