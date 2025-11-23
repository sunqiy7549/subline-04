# Implementation Plan - Chinese Original Matching

## Goal
Find the original Chinese article URL for a given Korean summary citation (Newspaper, Date, Page).
Specifically, match the first item: "Nanfang Daily, 2025-11-07, Page A1".

## Proposed Changes

### [NEW] scripts/match_article.py
Create a script to:
1.  Construct the e-paper URL for Nanfang Daily based on date and page.
    *   Format: `https://epaper.southcn.com/nfdaily/html/YYYYMM/DD/node_PAGE.html`
2.  Fetch the page content.
3.  Extract the list of article titles and their links.
4.  Filter/Search for the matching article based on keywords (e.g., "十四五", "规划").

## Verification Plan

### Automated Verification
*   Run `python3 scripts/match_article.py`
*   Expect it to output a list of articles from `2025-11-07` Page `A01`.
*   Expect it to identify a candidate title containing "十四五" (14th Five-Year Plan).

### Manual Verification
*   Review the output to confirm the Chinese title matches the meaning of the Korean summary ("Guangdong 14th Five-Year Plan Performance Report...").
