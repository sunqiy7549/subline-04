# Implementation Plan - Content Fetching & Dataset Creation

## Goal
Fetch the full text of the original Chinese articles for the successfully matched items.
Discard items where no match was found or no candidate scores high enough.

## Input
*   `data/mofa/matches.json`: Contains items and their candidate lists.

## Proposed Changes

### [NEW] scripts/fetch_originals.py
This script will:
1.  **Load** `data/mofa/matches.json`.
2.  **Iterate** through each matched item.
3.  **Select Best Candidate**:
    *   The previous step only listed candidates on the page.
    *   Now, we must **score** them against the Korean headline/summary.
    *   *Scoring Logic*:
        *   Extract keywords from Korean headline (or use a simple mapping if possible).
        *   Actually, since we don't have a Korean-Chinese dictionary, we will rely on:
            *   **Numbers**: (e.g., "14", "5", "2025")
            *   **Common Terms**: (If possible to map)
            *   **Heuristic**: If there is only 1 candidate, take it? No, page usually has many.
            *   **Refined Strategy**: We will try to match the *numbers* and *proper nouns* (if in parens in Korean text) to the Chinese title.
            *   If confidence is low, we might have to skip or take the top one if it looks reasonable.
            *   *Alternative*: Just fetch ALL candidates? No, user said "matched originals".
            *   *Decision*: I will implement a scoring based on **numbers** and **English/Chinese characters found in the Korean text** (e.g. names in parens).
4.  **Fetch Content**:
    *   For the selected URL, download the page.
    *   **Extract Body**: Use `BeautifulSoup` with newspaper-specific selectors or a generic "largest text block" fallback.
5.  **Save**:
    *   Save individual files: `data/originals/{date}_{newspaper}_{title}.json`
    *   Append to `data/dataset.json`.

## Content Selectors (Tentative)
*   **Nanfang**: `#content`, `.article-content`
*   **Guangzhou**: `div.article-content`, `#content`
*   **Fujian**: `.article-content`, `#content`
*   **Hainan**: `#content`, `.content`

## Verification
*   Run script.
*   Check `data/dataset.json`.
*   Verify a few samples.
