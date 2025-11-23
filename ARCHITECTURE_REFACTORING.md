# Architecture Refactoring Summary

This document explains the major architectural refactoring to solve JavaScript redirect issues.

## Problem
Guangzhou Daily and Nanfang Daily failed to fetch content on cloud servers due to JavaScript redirect pages (using `window.location.href`) that couldn't be properly handled by simple HTTP requests.

## Solution
Implemented a **unified fetching architecture** with:

### 1. Unified HTML Fetcher
**File:** [`utils/fetcher.py`](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/utils/fetcher.py)

- Centralized HTTP client with proper browser headers
- Automatic JS redirect detection and following
- Rate limiting to avoid bot detection
- Session pooling for better performance

### 2. URL Generators

#### Guangzhou Daily
**File:** [`sources/gzdaily.py`](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/sources/gzdaily.py)

- **Function:** `gzdaily_index_url(date)` 
- **Change:** Switch from PC version to **H5 version**
- **URL Pattern:** `https://gzdaily.dayoo.com/h5/html5/YYYY-MM/DD/node_867.htm`
- **Benefit:** Direct access, bypasses JS redirect portal pages

#### Nanfang Daily
**File:** [`sources/nfdaily.py`](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/sources/nfdaily.py)

- **Function:** `nfdaily_section_url(date, section)`
- **URL Pattern:** `https://epaper.southcn.com/nfdaily/html/YYYYMM/DD/node_{section}.html`
- **Benefit:** Direct section access without portal navigation

### 3. Updated App Logic
**File:** [`app.py`](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/app.py)

- Replaced manual `requests.get()` calls with `fetch_html()`
- Uses URL generators for cleaner, more maintainable code
- Better error handling and logging

## Key Benefits

1. **Reliability:** No more JS redirect failures on cloud servers
2. **Performance:** Direct URLs = fewer redirects = faster loading
3. **Maintainability:** Centralized fetching logic, easy to update headers/behavior
4. **Scalability:** Easy to add new newspapers using the same patterns

## Deployment

After pulling this update on your cloud server:

```bash
cd news_aggreg
git pull
docker-compose down
docker-compose up -d --build
```

Both Guangzhou Daily and Nanfang Daily should now fetch correctly.
