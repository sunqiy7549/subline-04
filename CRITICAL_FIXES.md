# Critical Fixes Applied

## Issue
After user testing on server, identified that the URLs I initially chose were incorrect and encoding was not properly handled.

## Root Problems

### 1. Wrong URL Patterns
- **Guangzhou Daily**: I used H5 version URLs, but the **PC version** is the stable, pure HTML version that works
  - ❌ Wrong: `https://gzdaily.dayoo.com/h5/html5/...`
  - ✅ Correct: `https://gzdaily.dayoo.com/pc/html/YYYY-MM/DD/index_YYYY-MM-DD.htm`

### 2. Encoding Issues
- Original fetcher didn't properly handle `apparent_encoding`
- This caused 乱码 (garbled text): `å¹¿å·æ¥æ¥` instead of `广州日报`
- Any parsing logic matching Chinese characters would completely fail

## Solutions Applied

### 1. Updated URL Generators

**[sources/gzdaily.py](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/sources/gzdaily.py)**
```python
def gzdaily_index_url(d: date) -> str:
    # Now uses PC version - stable, pure HTML, no JS
    return d.strftime("https://gzdaily.dayoo.com/pc/html/%Y-%m/%d/index_%Y-%m-%d.htm")
```

**[sources/nfdaily.py](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/sources/nfdaily.py)**
```python
def nfdaily_section_url(d: date, section: str = "A01") -> str:
    # Corrected date format to use %Y%m and %d
    return f"https://epaper.southcn.com/nfdaily/html/{d:%Y%m}/{d:%d}/node_{section}.html"
```

### 2. Fixed Encoding Handling

**[utils/fetcher.py](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/utils/fetcher.py)**
```python
# CRITICAL FIX:
if resp.encoding is None or resp.encoding.lower() == "iso-8859-1":
    resp.encoding = resp.apparent_encoding or "utf-8"
```

This ensures:
- Detects correct encoding automatically
- Prevents 乱码 issues
- Chinese characters display correctly

### 3. Added Debug Logging

**[app.py](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/app.py)**
- Added logging for first 300 chars of fetched HTML
- Helps diagnose if we're getting:
  - ✅ Correct content
  - ❌ JS redirect shell
  - ❌ Encoding issues

```python
logging.info(f"GZDaily HTML first 300 chars: {html[:300]!r}")
logging.info(f"Nanfang Daily A01 HTML first 300 chars: {html[:300]!r}")
```

## Deployment

After pulling on cloud server:
```bash
cd news_aggreg
git pull
docker-compose down
docker-compose up -d --build
```

Check logs to see debug output:
```bash
docker-compose logs -f | grep "HTML first 300 chars"
```

If you see proper Chinese characters in the logs, fetching is working correctly. If parsing still fails, the issue is in the BeautifulSoup selectors, not the fetching.
