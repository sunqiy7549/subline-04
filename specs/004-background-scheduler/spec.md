# Functional Specification: Background News Scheduler

## 1. Goal
Implement a background task scheduler that automatically crawls news from all sources daily, stores them in a persistent database, and enables instant page load when users visit the application.

## 2. User Stories
* **As a** cloud server deployment user,
* **I want** the system to automatically crawl news in the background (even when no one is visiting),
* **So that** when I visit the website, I can see news immediately without waiting for real-time crawling.

* **As a** user,
* **I want** to view news from the past 7 days,
* **So that** I can catch up on any news I might have missed.

## 3. Core Features

### 3.1 Background Scheduler
* **Technology**: APScheduler (Advanced Python Scheduler)
* **Schedule** (Server Local Time):
  - Daily 09:00 AM: Crawl fast sources (Fujian, Hainan, Nanfang, Guangzhou)
  - Daily 09:30 AM: Crawl Guangxi Daily (slow, ~30-40 mins)
  - Daily 10:30 AM: Clean up data older than 7 days
* **Concurrency**: Run crawling tasks in background threads to avoid blocking the web server
* **Timezone Handling**: Use server's local timezone; ensure scheduler respects timezone changes

### 3.2 Enhanced Content Extraction
* **Integration**: newspaper3k library for intelligent article parsing
* **Benefits**:
  - Automatic extraction of article title, text, metadata
  - Better handling of different webpage structures
  - Fallback to existing BeautifulSoup logic if newspaper3k fails
* **Usage Example**:
  ```python
  from newspaper import Article
  
  article = Article(url, language='zh')
  article.download()
  article.parse()
  
  title = article.title
  text = article.text
  publish_date = article.publish_date
  ```

### 3.3 Data Persistence
* **Database**: SQLite (lightweight, no additional setup needed)
* **Schema**:
  ```sql
  CREATE TABLE articles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source TEXT NOT NULL,           -- e.g., '福建日报'
      source_key TEXT NOT NULL,       -- e.g., 'fujian'
      section TEXT,                   -- e.g., '01 要闻'
      title TEXT NOT NULL,
      title_ko TEXT,                  -- Korean translation (optional)
      link TEXT NOT NULL UNIQUE,
      content_preview TEXT,           -- First 200 chars of article
      date TEXT NOT NULL,             -- YYYY-MM-DD
      last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      INDEX idx_date (date),
      INDEX idx_source (source_key),
      INDEX idx_link (link)
  );
  ```

### 3.4 API Modifications
* **Current**: `/api/news/<source>` - Real-time crawling
* **New**: `/api/news/<source>` - Read from database
  - Query params: `?date=YYYY-MM-DD`
  - If date not specified, return today's news
  - If no data in DB for requested date, trigger on-demand crawl
  - Response includes `cached: true/false` field

### 3.5 Admin Interface (Optional - Phase 2)
* Manual trigger buttons for each news source
* View scheduler status and last run time
* Force re-crawl specific dates
* Display database statistics (total articles, disk usage)

## 4. Technical Design

### 4.1 Architecture
```
┌─────────────────────────────────────────┐
│         Flask Web Server (Port 5001)    │
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │   Routes     │    │  Scheduler   │  │
│  │  /api/news/* │◄───┤ (APScheduler)│  │
│  └──────┬───────┘    └──────┬───────┘  │
│         │                   │          │
│         │         ┌─────────▼────────┐ │
│         │         │  newspaper3k     │ │
│         │         │  Content Extract │ │
│         │         └─────────┬────────┘ │
│         │                   │          │
│         └───────┬───────────┘          │
│                 ▼                       │
│         ┌──────────────┐                │
│         │  Database    │                │
│         │   (SQLite)   │                │
│         └──────────────┘                │
└─────────────────────────────────────────┘
```

### 4.2 New Files
```
news_aggregator/
├── scheduler/
│   ├── __init__.py
│   ├── jobs.py              # Crawling job functions
│   ├── scheduler.py         # APScheduler setup
│   └── extractors.py        # newspaper3k integration
├── database/
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy models
│   └── db.py                # Database initialization
└── data/
    └── news.db              # SQLite database file (auto-created)
```

### 4.3 Dependencies (Add to requirements.txt)
```
APScheduler==3.10.4
SQLAlchemy==2.0.23
newspaper3k==0.2.8
```

## 5. Implementation Plan

### Phase 1: Database Layer (Day 1, Morning)
- [ ] Create database schema with enhanced fields
- [ ] Implement SQLAlchemy models
- [ ] Create database helper functions (save_articles, get_articles_by_date)
- [ ] Test database operations

### Phase 2: Content Extraction Enhancement (Day 1, Afternoon)
- [ ] Install newspaper3k library
- [ ] Create extractor wrapper (newspaper3k with BeautifulSoup fallback)
- [ ] Test extraction on sample articles from each source
- [ ] Compare quality vs current BeautifulSoup approach

### Phase 3: Background Scheduler (Day 1, Evening)
- [ ] Install and configure APScheduler
- [ ] Create crawling job functions (integrate new extractor)
- [ ] Set up 9 AM daily schedules (server local time)
- [ ] Test scheduler in local environment

### Phase 4: API Refactoring (Day 2, Morning)
- [ ] Modify `/api/news/<source>` to read from database
- [ ] Implement fallback to real-time crawl if DB is empty
- [ ] Add `cached` field to API response
- [ ] Update frontend to handle cached data

### Phase 5: Testing & Deployment (Day 2, Afternoon)
- [ ] Test scheduler with multiple sources
- [ ] Verify 9 AM schedule executes correctly
- [ ] Verify 7-day data retention
- [ ] Deploy to cloud server
- [ ] Monitor first automated crawl cycle at 9 AM next day

## 6. Constraints & Risks

### 6.1 Technical Constraints
* **Cloud Server Resources**: Ensure sufficient disk space for 7 days of data (~100MB estimated)
* **Memory**: APScheduler runs in-process; monitor memory usage during Guangxi crawl
* **Timezone**: Scheduler uses server timezone; ensure crawl times are appropriate for Chinese news sources

### 6.2 Risks & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Crawler fails during scheduled run | Users see stale data | Implement retry logic (3 attempts); send email alerts on failure |
| Database grows too large | Disk space issues | Strict 7-day retention policy; add DB size monitoring |
| Scheduler conflicts with web requests | Server slowdown | Use separate thread pool for crawling; limit Guangxi concurrency |

## 7. Success Metrics
* **Page Load Speed**: Home page loads in <1 second (vs current 10-40 seconds)
* **Data Freshness**: News data updated daily by 10:30 AM (server local time)
* **Reliability**: 95%+ successful scheduled crawls
* **User Satisfaction**: Zero complaints about "waiting for news to load"
* **Content Quality**: newspaper3k improves article extraction accuracy by 20%+

## 8. Future Enhancements (Post-MVP)
* Real-time notifications when new articles are detected
* Historical search across all stored articles
* Analytics dashboard showing crawl success rates
* Celery + Redis for distributed task queue (if scaling needed)
