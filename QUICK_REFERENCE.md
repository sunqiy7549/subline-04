# 快速参考卡

## 三状态系统速览

```
┌─────────────────────────────────────────────────────┐
│                  应用状态机                          │
└─────────────────────────────────────────────────────┘

                    用户打开页面
                        ↓
            ┌──────────────────────┐
            │   检查数据库中      │
            │   是否有该来源新闻   │
            └──────────────────────┘
                   ↙          ↘
                有            没有
                ↓              ↓
           ┌────────┐    ┌─────────────┐
           │ loaded │    │检查是否正在 │
           │(已加载)│    │后台爬取    │
           └────────┘    └─────────────┘
                             ↙      ↘
                           是        否
                           ↓         ↓
                    ┌────────┐  ┌───────┐
                    │loading │  │ empty │
                    │(加载中) │  │(空)   │
                    └────────┘  └───────┘
                       ↓          ↓
                  显示进度条   显示按钮
                  显示日志流   用户点击
                       ↓          ↓
                    轮询...   启动爬取
                       ↓          ↓
                    完成时    进入loading
                    重新加载
```

---

## API 速查表

### 获取爬取状态
```bash
curl http://localhost:5001/api/crawl/status/fujian
```
**响应**: 
```json
{
  "state": "running|idle|completed|failed",
  "progress": 0-100,
  "logs": ["[时间] 消息", ...],
  "total_articles": 数字,
  "start_time": "ISO时间",
  "end_time": "ISO时间或null"
}
```

### 启动爬取
```bash
curl -X POST http://localhost:5001/api/crawl/start/fujian \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-11-25"}'
```
**响应**: 
```json
{"status": "success", "message": "..."}
```

### 获取新闻 (新格式)
```bash
curl http://localhost:5001/api/news/fujian?date=2025-11-25
```
**响应**:
```json
{
  "source": "福建日报",
  "status": "loaded|loading|empty",
  "crawl_status": {...},
  "data": [...]
}
```

---

## JavaScript 函数索引

### 状态显示函数
| 函数 | 作用 | 何时调用 |
|------|------|---------|
| `showLoadedState()` | 显示新闻网格 | 数据已加载 |
| `showLoadingState()` | 显示进度条 | 开始加载 |
| `showEmptyState()` | 显示空状态 | 无数据 |

### 轮询管理
| 函数 | 作用 |
|------|------|
| `startStatusPoller(sourceKey)` | 开始每秒轮询 |
| `stopStatusPoller()` | 停止轮询 |

### 页面加载
| 函数 | 作用 |
|------|------|
| `loadPage()` | 主入口 |
| `loadSingleSource(source, date)` | 单源 |
| `loadAllSources(date)` | 全部 |

### 日志管理
| 函数 | 作用 |
|------|------|
| `appendLog(message)` | 追加日志 |

---

## HTML 元素 ID

```html
<!-- UI 容器 -->
<div id="news-loaded-state">       <!-- 已加载状态 -->
<div id="news-loading-state">      <!-- 加载中状态 -->
<div id="news-empty-state">        <!-- 空状态 -->

<!-- 加载状态组件 -->
<div id="progress-fill">           <!-- 进度条 -->
<p id="progress-text">             <!-- 进度文本 -->
<div id="log-stream">              <!-- 日志流 -->

<!-- 操作按钮 -->
<button id="fetch-button">         <!-- 开始抓取按钮 -->
```

---

## CSS 类名参考

```css
.loading-container    /* 加载界面容器 */
.progress-section     /* 进度条区域 */
.progress-bar         /* 进度条背景 */
.progress-fill        /* 进度条填充 */
.log-section          /* 日志区域 */
.log-stream           /* 日志流容器 */
.log-entry            /* 单条日志 */
.empty-state-container /* 空状态容器 */
.fetch-button         /* 抓取按钮 */
```

---

## 数据库查询

### 查看文章总数
```sql
SELECT COUNT(*) FROM article;
```

### 按来源统计
```sql
SELECT source_key, COUNT(*) 
FROM article 
GROUP BY source_key;
```

### 按日期统计
```sql
SELECT date, COUNT(*) 
FROM article 
GROUP BY date 
ORDER BY date DESC;
```

### 查看最新文章
```sql
SELECT * FROM article 
ORDER BY date DESC, created_at DESC 
LIMIT 10;
```

### 清理旧数据
```sql
DELETE FROM article 
WHERE date < date('now', '-7 days');
```

---

## 配置参数

### 轮询间隔
**位置**: `static/js/main.js` 第 ~90 行
```javascript
crawlStatusPoller = setInterval(async () => {
    // ...
}, 1000);  // 改这个值（毫秒）
```
- 1000 = 1秒（推荐）
- 500 = 0.5秒（高频）
- 2000 = 2秒（低频）

### 日志保留数量（前端）
**位置**: `static/js/main.js` 第 ~73 行
```javascript
const entries = logStream.querySelectorAll('.log-entry');
if (entries.length > 50) {  // 改这个值
    entries[0].remove();
}
```

### 日志保留数量（后端）
**位置**: `app.py` 第 ~28 行
```python
if len(self.logs) > 100:  # 改这个值
    self.logs.pop(0)
```

---

## 环境变量 (可选)

### Flask 配置
```bash
export FLASK_ENV=development    # 开发模式
export FLASK_ENV=production     # 生产模式
export FLASK_DEBUG=1            # 启用调试
```

### 数据库路径
```bash
export DB_PATH=/custom/path/news.db
```

---

## 常见命令

### 启动应用
```bash
python3 app.py
```

### 运行测试
```bash
python3 test_refactor.py
```

### 查看日志
```bash
tail -f app.log
```

### 重启应用
```bash
# 1. 找到进程 ID
ps aux | grep app.py

# 2. 杀死进程
kill <PID>

# 3. 重新启动
python3 app.py
```

---

## 调试技巧

### 启用详细日志
在 `app.py` 中：
```python
logger.setLevel(logging.DEBUG)
```

### 检查浏览器请求
1. 打开 DevTools (F12)
2. 进入 Network 标签
3. 刷新页面
4. 查看 API 调用和响应

### 检查内存使用
```bash
# Mac/Linux
ps aux | grep python3 | grep app.py

# Windows
tasklist | findstr python
```

### 检查数据库连接
```python
from database import get_session
session = get_session()
result = session.query(Article).count()
print(f"Total articles: {result}")
```

---

## 文档导航

| 文档 | 内容 | 适合 |
|------|------|------|
| `QUICK_START.md` | 快速启动 | 新用户 |
| `ARCHITECTURE_REFACTORING_v2.md` | 架构设计 | 开发者 |
| `REFACTORING_REPORT.md` | 重构报告 | 项目经理 |
| `COMPLETION_SUMMARY.md` | 完成总结 | 全员 |
| 本文件 | 快速参考 | 快查 |

---

## SOS - 快速问题解决

**Q: 进度条不动怎么办？**
A: 检查是否有网络问题，查看日志，重启应用

**Q: 按钮灰显怎么办？**
A: 已有爬取进程运行，等待完成

**Q: 看不到日志怎么办？**
A: 检查浏览器控制台错误，查看服务器日志

**Q: 数据没存储怎么办？**
A: 检查数据目录权限和数据库连接

---

**最后更新**: 2025-11-25  
**版本**: v2.0  
**状态**: ✅ 生产就绪

