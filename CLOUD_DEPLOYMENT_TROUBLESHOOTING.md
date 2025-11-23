# Cloud Deployment Troubleshooting

## Issue
Guangzhou Daily and Nanfang Daily show "暂无新闻" (No News) on cloud server but work fine locally.

## Root Cause
**Playwright system dependencies were missing in the Docker container.**

The base Playwright Python image includes the browser binaries, but some JavaScript-heavy websites require additional system libraries that were not automatically installed with `playwright install chromium`.

## Diagnosis
- **Local environment**: System dependencies are already present on Windows
- **Docker container**: `playwright install chromium` only installs browser binaries, not all required system libraries

This caused the browser to fail silently when trying to render JavaScript-heavy content from Guangzhou Daily and Nanfang Daily.

## Solution
Updated [`Dockerfile`](file:///c:/Users/Sun/Downloads/news_aggregator-20251123T185915Z-1-001/news_aggregator/Dockerfile) line 16:

**Before:**
```dockerfile
RUN playwright install chromium
```

**After:**
```dockerfile
RUN playwright install --with-deps chromium
```

The `--with-deps` flag ensures **all system dependencies** required by Chromium are installed, including:
- Font libraries
- Graphics libraries (Mesa, etc.)
- Media codecs
- And other OS-level dependencies

## Deployment Instructions

1. Pull the latest code on your cloud server:
   ```bash
   cd news_aggreg
   git pull
   ```

2. Rebuild the Docker container:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

3. Verify the fix by checking if Guangzhou Daily and Nanfang Daily now display content.

## Expected Result
After rebuilding with the updated Dockerfile, all news sources (including Guangzhou Daily and Nanfang Daily) should fetch and display content correctly on the cloud server.
