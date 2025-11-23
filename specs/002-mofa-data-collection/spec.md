# Functional Specification: MOFA Data Collection

## 1. Goal
Collect "Weekly Political Trends in South China" (화남지역 주간 정무 동향) reports from the Consulate General of the Republic of Korea in Guangzhou website for the past month.

## 2. Scope
*   **Source**: `https://guangzhou.mofa.go.kr/cn-guangzhou-ko/brd/m_123/list.do`
*   **Timeframe**: Last 1 month.
*   **Target Content**: Posts with title containing "화남지역 주간 정무 동향".
*   **Action**:
    1.  Identify relevant posts.
    2.  Extract date range from the title (e.g., "11.13-11.19").
    3.  **Scrape the full text content** directly from the article detail page.
    4.  (Optional) Download .hwp as backup if text extraction fails.

## 3. Technical Constraints & Risks
*   **Content Extraction**: Text is visible on the page. We need to identify the correct HTML container to avoid scraping menus/footers.
    *   *Mitigation*: Use heuristics (e.g., text between "Modification Date" and "List" button) or specific CSS selectors (`div.view_cont` is common).
*   **Anti-Scraping**: The site has redirect/blocking mechanisms.
    *   *Mitigation*: Use `requests` with headers or `browser_subagent` if needed.

## 4. Data Structure
We will save the data as JSON files (one per article) or a single JSONL file.
```
data/
  mofa/
    articles/
      [date_range]_[title].json  # {title, date, content, url}
```

## 5. Success Criteria
*   All "화남지역 주간 정무 동향" reports from the last month are scraped.
*   JSON files contain clean text content (no HTML tags, no menu text).
