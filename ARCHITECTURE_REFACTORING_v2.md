# 应用架构重构 v2.0

## 概述
本次重构将界面和操作逻辑清晰化，实现了三状态管理系统：**已加载 → 正在加载 → 无数据**。

---

## 核心设计原则

### 1. 三状态管理系统

#### 状态 1: **loaded** (已加载新闻)
- **条件**: 数据库中存在该日期该来源的新闻
- **UI显示**: 新闻卡片网格
- **用户体验**: 直接显示新闻，无需等待

#### 状态 2: **loading** (正在加载)
- **条件**: 该日期该来源没有缓存数据，且后台爬取进程正在运行
- **UI显示**: 
  - 进度条（实时更新进度百分比）
  - 日志流（实时显示爬取日志）
  - 预期等待时间提示
- **用户体验**: 实时反馈，用户知道系统在工作

#### 状态 3: **empty** (无数据)
- **条件**: 没有缓存数据且没有正在运行的爬取进程
- **UI显示**: 
  - 空状态提示
  - "开始抓取"按钮
- **用户体验**: 让用户可以手动启动爬取

---

## 后端架构

### 状态管理类

```python
class CrawlState(Enum):
    IDLE = "idle"              # 空闲
    RUNNING = "running"        # 运行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败

class SourceCrawlStatus:
    """单个数据源的爬取状态"""
    - source_key: str          # 数据源标识
    - state: CrawlState        # 当前状态
    - progress: int            # 0-100 进度百分比
    - logs: List[str]          # 日志队列
    - total_articles: int      # 已发现文章数
    - start_time: datetime     # 开始时间
    - end_time: datetime       # 结束时间
```

### 全局状态存储

```python
CRAWL_STATUS = {
    'fujian': SourceCrawlStatus('fujian'),
    'hainan': SourceCrawlStatus('hainan'),
    'nanfang': SourceCrawlStatus('nanfang'),
    'guangzhou': SourceCrawlStatus('guangzhou'),
    'guangxi': SourceCrawlStatus('guangxi')
}
```

### API 端点

#### 获取爬取状态
```
GET /api/crawl/status/<source_key>
Response: {
    'state': 'running',
    'progress': 45,
    'logs': ['[09:00:00] Starting...', '[09:00:05] Found 5 articles...'],
    'total_articles': 15,
    'start_time': '2025-11-25T09:00:00',
    'end_time': null
}
```

#### 手动启动爬取
```
POST /api/crawl/start/<source_key>
Body: { 'date': '2025-11-25' }
Response: { 'status': 'success', 'message': '...' }
```

#### 获取新闻（新返回格式）
```
GET /api/news/<source_key>?date=2025-11-25
Response: {
    'source': '福建日报',
    'status': 'loaded' | 'loading' | 'empty',  # 三种状态之一
    'crawl_status': {...},                      # 爬取进程的详细状态
    'data': [...]                               # 新闻数据或空数组
}
```

---

## 前端架构

### UI 三状态容器

#### 1. 已加载状态容器 (#news-loaded-state)
```html
<div id="news-loaded-state">
    <div id="news-grid" class="news-grid">
        <!-- 新闻卡片 -->
    </div>
</div>
```

#### 2. 正在加载状态容器 (#news-loading-state)
```html
<div id="news-loading-state">
    <div class="progress-section">
        <h3>正在获取报纸内容</h3>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <p class="progress-text"></p>
    </div>
    <div class="log-section">
        <h3>实时日志</h3>
        <div class="log-stream" id="log-stream"></div>
    </div>
</div>
```

#### 3. 空状态容器 (#news-empty-state)
```html
<div id="news-empty-state">
    <div class="empty-state-container">
        <div class="empty-icon">📰</div>
        <h2>暂无新闻</h2>
        <p>该日期暂无可用数据，请点击下方按钮开始抓取</p>
        <button id="fetch-button" class="fetch-button">
            开始抓取
        </button>
    </div>
</div>
```

### 状态转换流程

```
用户访问页面 → 获取新闻
    ↓
API 返回状态
    ├─ status='loaded' → showLoadedState()
    │   └─ 显示新闻网格，停止轮询
    │
    ├─ status='loading' → showLoadingState()
    │   └─ 显示进度条和日志
    │   └─ 启动状态轮询 (每秒一次)
    │   └─ 监听 RUNNING → COMPLETED 转换
    │
    └─ status='empty' → showEmptyState()
        └─ 显示手动抓取按钮
        └─ 用户点击 → POST /api/crawl/start/<source>
           → 启动后台爬取
           → showLoadingState()
           → 启动轮询直到完成
```

### JavaScript 核心函数

#### 状态显示函数
- `showLoadedState()` - 切换到已加载状态
- `showLoadingState()` - 切换到正在加载状态
- `showEmptyState()` - 切换到空状态

#### 轮询函数
- `startStatusPoller(sourceKey)` - 启动每秒轮询
- `stopStatusPoller()` - 停止轮询

#### 页面加载函数
- `loadPage()` - 主入口
- `loadSingleSource(sourceKey, dateStr)` - 加载单个来源
- `loadAllSources(dateStr)` - 加载所有来源（优先级：已加载 > 加载中 > 无数据）

#### 日志管理
- `appendLog(message)` - 追加日志到日志流

---

## 场景演示

### 场景 1: 用户打开主页，数据已在数据库中
```
1. 前端调用 GET /api/news/all
2. 后端检查所有来源的数据库
3. 响应 status='loaded'，返回新闻列表
4. 前端显示新闻卡片网格
5. 用户可以点击查看详情、收藏等
```

### 场景 2: 用户打开主页，没有数据，后台正在爬取
```
1. 前端调用 GET /api/news/all
2. 后端检查数据库为空，但发现有爬取进程在运行
3. 响应 status='loading'
4. 前端显示进度条和日志流
5. 前端启动轮询 /api/crawl/status/<source>
6. 每秒更新进度条、添加新日志
7. 爬取完成后响应 COMPLETED
8. 前端自动重新加载页面
9. 下次请求时状态为 'loaded'
```

### 场景 3: 用户打开主页，没有数据也没有爬取进程
```
1. 前端调用 GET /api/news/all
2. 后端检查：无缓存、无运行的爬取进程
3. 响应 status='empty'
4. 前端显示空状态和"开始抓取"按钮
5. 用户点击按钮
6. 前端调用 POST /api/crawl/start/<source>
7. 后端在后台线程启动爬取，更新状态为 RUNNING
8. 前端显示加载状态，启动轮询
9. ... 同场景 2
```

### 场景 4: 用户切换报纸源或日期
```
1. 用户点击导航按钮或日期选择器
2. 前端调用 loadPage()
3. 依次调用 GET /api/news/<source>?date=<date>
4. 根据各来源的状态决定显示什么
   - 如果任何来源是 'loaded' 且有数据，直接显示
   - 如果有来源是 'loading'，显示加载状态
   - 否则显示空状态
```

---

## 关键改进

| 方面 | 旧系统 | 新系统 |
|------|-------|--------|
| **状态清晰性** | 混乱，用户不知道发生了什么 | 三清晰状态，用户始终知道系统状态 |
| **用户反馈** | 无进度提示，用户等待时焦虑 | 实时进度条和日志，用户有预期 |
| **手动控制** | 无法手动重新抓取 | 可以在无数据状态下点击按钮启动爬取 |
| **多源并行** | 逐个加载，缓慢 | 并行加载所有源，显示优先级处理 |
| **日期切换** | 需要重新加载缓存 | 快速响应，按需加载 |
| **代码维护** | 逻辑混乱，难以维护 | 清晰的状态机，易于扩展 |

---

## 后续优化建议

1. **进度计算精度**: 根据实际处理进度更新百分比，而不是线性增长
2. **错误处理**: 当爬取失败时，显示错误信息和重试按钮
3. **缓存策略**: 实现增量更新，而不是每次全量替换
4. **多用户支持**: 为不同用户维护独立的状态
5. **性能优化**: 使用 WebSocket 替代轮询以减少服务器负载
6. **本地化**: 支持多语言日志消息

---

## 测试清单

- [x] 三个状态容器的显示/隐藏逻辑
- [x] 状态 API 的返回格式
- [x] 轮询的启动和停止
- [x] 日志的实时追加
- [x] 手动抓取按钮的触发
- [x] 日期和来源切换的处理
- [ ] 并发抓取的线程安全
- [ ] 长时间运行的稳定性
- [ ] 网络中断时的恢复机制

