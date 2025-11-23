# Implementation Plan - Batch Matching & Reporting

## Goal
Process all scraped MOFA reports to find original Chinese articles for:
*   **Nanfang Daily** (南方日报)
*   **Guangzhou Daily** (广州日报)
*   **Fujian Daily** (福建日报)
*   **Hainan Daily** (海南日报)

**Exclude**: Guangxi Daily (广西日报).

## URL Patterns & Selectors
*   **Nanfang Daily**: `https://epaper.southcn.com/nfdaily/html/YYYYMM/DD/node_PAGE.html`
    *   Selector: `div#content_nav ul#artPList1 a`
*   **Guangzhou Daily**: `https://gzdaily.dayoo.com/pc/html/YYYY-MM/DD/node_PAGE.htm?v=1`
    *   Selector: *To be inspected*
*   **Fujian Daily**: `https://fjrb.fjdaily.com/pc/col/YYYYMM/DD/node_PAGE.html`
    *   Selector: *To be inspected*
*   **Hainan Daily**: `http://news.hndaily.cn/html/YYYY-MM/DD/node_PAGE.htm?v=1`
    *   Selector: *To be inspected*

## Proposed Changes

### 1. [NEW] scripts/mofa_utils.py
*   Move parsing logic from `test_parse_article.py` here.
*   Function: `parse_mofa_article(json_path) -> List[Dict]`

### 2. [NEW] scripts/batch_match.py
*   **Load** all JSON files.
*   **Parse** items.
*   **Filter**: Drop items where Newspaper == "广西日报".
*   **Match**:
    *   Detect newspaper type.
    *   Construct URL based on specific pattern (handle date formats YYYYMM vs YYYY-MM).
    *   Fetch page and extract links (using specific selectors).
    *   Find best match by keywords.
*   **Report**: Generate `matching_report.md`.

## Verification
*   Inspect selectors for new newspapers.
*   Run batch match on a subset first.
*   Review report.
