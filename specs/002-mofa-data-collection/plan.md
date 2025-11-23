# Implementation Plan: MOFA Data Collection

## 1. Architecture
*   **Language**: Python 3
*   **Libraries**:
    *   `requests`: For HTTP requests (handling cookies/headers to avoid redirect loops).
    *   `beautifulsoup4`: For parsing HTML to find article links and attachments.
    *   `fake_useragent` (optional, or just hardcode a modern UA): To bypass basic anti-bot checks.

## 2. Workflow
1.  **Fetch List Page**: Access `https://guangzhou.mofa.go.kr/cn-guangzhou-ko/brd/m_123/list.do`.
2.  **Parse Articles**:
    *   Iterate through the table rows.
    *   Filter for titles containing "화남지역 주간 정무 동향".
    *   Extract the Date (from the date column) and the Link.
    *   **Date Filter**: Stop processing if the date is older than 1 month.
3.  **Fetch Article Details**:
    *   Follow the link to the article detail page (`view.do`).
    *   **Extract Content**:
        *   Locate the main content container (likely `div.view_cont` or similar).
        *   If specific container is hard to find, extract all text and use regex to capture text between the "Modification Date" and the "List" button.
        *   Clean up whitespace.
4.  **Save Data**:
    *   Save as JSON: `data/mofa/articles/YYYYMMDD_Title.json`.
    *   Format: `{"title": ..., "date": ..., "url": ..., "content": ...}`.

## 3. File Structure
```
news_aggregator/
├── scripts/
│   └── scrape_mofa.py      # The main script
├── data/
│   └── mofa/
│       └── articles/       # Scraped JSON files
```

## 4. Verification
*   Run the script.
*   Check `data/mofa/articles/` for JSON files.
*   Verify that `content` field contains the news text (e.g., "[Guangdong]").
