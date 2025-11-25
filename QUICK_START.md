# 快速启动指南 - 重构版本 v2.0

## 新功能概览

### 三状态系统
您的应用现在支持三种清晰的状态：

1. **已加载** 🎉
   - 数据已准备好显示
   - 看到新闻卡片网格
   - 可以立即阅读

2. **正在加载** ⏳
   - 系统正在获取数据
   - 看到实时进度条
   - 看到实时日志流
   - 知道需要等待多久

3. **无数据** 📭
   - 当前没有数据
   - 看到"开始抓取"按钮
   - 可以手动触发爬取

---

## 用户操作流程

### 打开主页
```
1. 访问 http://localhost:5001
2. 应用自动检查是否有缓存数据
3. 根据不同情况显示对应的界面
```

### 等待新闻加载
```
1. 如果显示进度条，说明正在加载
2. 进度条会实时更新百分比
3. 下方会显示实时日志
4. 完成后会自动刷新并显示新闻
```

### 手动触发抓取
```
1. 如果看到"暂无新闻"的空状态
2. 点击"开始抓取"按钮
3. 等待进度条完成
4. 自动显示抓取的新闻
```

### 切换报纸或日期
```
1. 点击顶部导航栏的报纸名称
2. 或使用日期选择器切换日期
3. 应用会自动重新加载该来源/日期的新闻
4. 如果有缓存会立即显示，否则自动开始加载
```

---

## 新增 API 接口

### 1. 获取爬取状态
```
GET /api/crawl/status/<source_key>

响应示例:
{
    "state": "running",
    "progress": 45,
    "logs": [
        "[09:00:00] Starting crawl",
        "[09:00:05] Found 5 articles",
        "[09:00:10] Processing articles..."
    ],
    "total_articles": 12,
    "start_time": "2025-11-25T09:00:00",
    "end_time": null
}
```

### 2. 手动启动爬取
```
POST /api/crawl/start/<source_key>

请求体:
{
    "date": "2025-11-25"
}

响应示例:
{
    "status": "success",
    "message": "Crawl started for fujian"
}
```

### 3. 获取新闻（改进格式）
```
GET /api/news/<source_key>?date=2025-11-25

响应示例:
{
    "source": "福建日报",
    "status": "loaded",  // 可能是 loaded, loading, 或 empty
    "crawl_status": {
        "state": "idle",
        "progress": 0,
        "total_articles": 25
    },
    "data": [
        {
            "title": "新闻标题",
            "title_ko": "뉴스 제목",
            "link": "http://...",
            "section": "第01版",
            "source": "福建日报",
            "starred": false
        }
    ]
}
```

---

## 配置说明

### 轮询频率
前端每秒轮询一次状态，可在 `static/js/main.js` 中修改：

```javascript
crawlStatusPoller = setInterval(async () => {
    // ... 轮询逻辑
}, 1000);  // 改为其他数值（毫秒）
```

### 日志保留数量
日志流最多显示最后 20 条，可在 `static/js/main.js` 中修改：

```javascript
const newLogs = status.logs.filter(l => !currentLogs.includes(l));
// 改为其他数值
```

### 后端日志队列大小
后端最多保留最后 100 条日志，可在 `app.py` 中修改：

```python
if len(self.logs) > 100:  # 改为其他数值
    self.logs.pop(0)
```

---

## 故障排查

### 问题 1: 页面显示"正在加载"但进度不动
**原因**: 后台爬取进程可能卡住
**解决**:
1. 刷新页面
2. 检查服务器日志
3. 重启应用

### 问题 2: 按钮无响应
**原因**: 可能已经有爬取进程在运行
**解决**:
1. 等待当前爬取完成
2. 查看日志确认状态
3. 不要同时启动多个爬取

### 问题 3: 日志没有出现
**原因**: 爬取进程可能出错
**解决**:
1. 检查网络连接
2. 查看服务器日志获取详细错误
3. 尝试其他数据源

### 问题 4: 数据没有保存到数据库
**原因**: 数据库路径不存在或无权限
**解决**:
1. 确保 `data/` 目录存在
2. 检查目录权限
3. 查看服务器日志

---

## 监控和调试

### 查看服务器日志
```bash
# 实时查看日志
tail -f app.log

# 查看最近的错误
grep ERROR app.log | tail -20
```

### 检查数据库状态
```bash
# 查看已保存的文章数
sqlite3 data/news.db "SELECT COUNT(*) FROM article;"

# 查看各来源的文章数
sqlite3 data/news.db "SELECT source_key, COUNT(*) FROM article GROUP BY source_key;"
```

### 浏览器开发者工具
1. 打开浏览器 DevTools (F12)
2. 查看 Network 标签，监控 API 调用
3. 查看 Console 标签，查看 JavaScript 错误
4. 查看 Storage 标签，检查缓存数据

---

## 性能优化建议

### 1. 启用浏览器缓存
应用已实现 sessionStorage 缓存，同一会话内的重复请求会使用缓存。

### 2. 减少 API 调用
切换不同的报纸/日期时，应用会智能判断是否需要重新加载。

### 3. 监控爬取时间
观察日志流中的时间戳，了解各个步骤的耗时：
```
[09:00:00] Starting crawl
[09:00:05] Found X articles (5秒内发现)
[09:00:15] Saved Y articles (10秒内保存)
```

---

## 常见问题

**Q: 为什么每次打开页面都要重新加载？**
A: 当没有缓存数据时，应用会自动启动爬取。下次打开同一日期同一来源时会使用缓存。

**Q: 可以同时抓取多个来源吗？**
A: 是的，应用支持并行加载。按"全部"时会同时请求所有来源。

**Q: 怎么清除缓存？**
A: 清除浏览器的 sessionStorage 数据，或使用管理员 API 清除数据库。

**Q: 爬取需要多长时间？**
A: 取决于来源，从几秒到几十秒不等。查看日志流了解进度。

---

## 下一步

1. **生产部署**: 确保服务器可正常运行
2. **性能测试**: 监控并发加载情况
3. **用户反馈**: 收集用户意见并改进
4. **后续功能**: 考虑添加 WebSocket、失败重试等

---

## 需要帮助？

查看以下文档获取更多信息：
- `ARCHITECTURE_REFACTORING_v2.md` - 详细技术文档
- `REFACTORING_CHECKLIST.md` - 完整功能清单
- `REFACTORING_REPORT.md` - 重构报告

