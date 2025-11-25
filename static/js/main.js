document.addEventListener('DOMContentLoaded', () => {
    // ============ UI 元素 ============
    const newsLoadedState = document.getElementById('news-loaded-state');
    const newsLoadingState = document.getElementById('news-loading-state');
    const newsEmptyState = document.getElementById('news-empty-state');
    
    const newsGrid = document.getElementById('news-grid');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const logStream = document.getElementById('log-stream');
    const fetchButton = document.getElementById('fetch-button');
    
    const navBtns = document.querySelectorAll('.nav-btn');
    const datePicker = document.getElementById('date-picker');
    const dateDisplay = document.getElementById('current-date-display');
    const prevDayBtn = document.getElementById('prev-day');
    const nextDayBtn = document.getElementById('next-day');

    // ============ 状态变量 ============
    let allNews = [];
    let currentSource = sessionStorage.getItem('currentSource') || 'all';
    let currentDate = new Date();
    let crawlStatusPoller = null;  // 状态轮询定时器
    
    const savedDate = sessionStorage.getItem('currentDate');
    if (savedDate && !window.IS_SELECTION_PAGE) {
        currentDate = new Date(savedDate);
    }

    // ============ 初始化 ============
    if (window.IS_SELECTION_PAGE) {
        fetchSelectedNews();
    } else {
        // 设置活跃按钮
        navBtns.forEach(btn => {
            if (btn.dataset.source === currentSource) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        updateDateDisplay();
        loadPage();
    }

    // ============ UI 状态管理 ============
    function showLoadedState() {
        newsLoadedState.style.display = 'block';
        newsLoadingState.style.display = 'none';
        newsEmptyState.style.display = 'none';
    }

    function showLoadingState() {
        newsLoadedState.style.display = 'none';
        newsLoadingState.style.display = 'block';
        newsEmptyState.style.display = 'none';
        logStream.innerHTML = '<div class="log-entry">准备中...</div>';
        progressFill.style.width = '0%';
        progressText.textContent = '准备中...';
    }

    function showEmptyState() {
        newsLoadedState.style.display = 'none';
        newsLoadingState.style.display = 'none';
        newsEmptyState.style.display = 'block';
        stopStatusPoller();
    }

    // ============ 日志管理 ============
    function appendLog(message) {
        const newEntry = document.createElement('div');
        newEntry.className = 'log-entry';
        newEntry.textContent = message;
        logStream.appendChild(newEntry);
        
        // 自动滚动到底部
        logStream.scrollTop = logStream.scrollHeight;
        
        // 只保留最后50条日志
        const entries = logStream.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[0].remove();
        }
    }

    // ============ 状态轮询 ============
    function startStatusPoller(sourceKey) {
        stopStatusPoller();
        
        crawlStatusPoller = setInterval(async () => {
            try {
                const response = await fetch(`/api/crawl/status/${sourceKey}`);
                const status = await response.json();
                
                if (status.logs && status.logs.length > 0) {
                    // 获取新日志
                    const currentLogs = logStream.innerText.split('\n').filter(l => l.trim());
                    const newLogs = status.logs.filter(l => !currentLogs.includes(l));
                    
                    newLogs.forEach(log => appendLog(log));
                }
                
                // 更新进度条
                progressFill.style.width = Math.min(status.progress, 100) + '%';
                progressText.textContent = `进度: ${status.progress}% | 已发现 ${status.total_articles} 篇`;
                
                // 检查是否完成
                if (status.state === 'completed') {
                    appendLog('✓ 爬取完成！');
                    stopStatusPoller();
                    
                    // 延迟1秒后重新加载页面
                    setTimeout(() => {
                        loadPage();
                    }, 1000);
                } else if (status.state === 'failed') {
                    appendLog('✗ 爬取失败');
                    stopStatusPoller();
                }
                
            } catch (err) {
                console.error('轮询状态失败:', err);
            }
        }, 1000);  // 每秒轮询一次
    }

    function stopStatusPoller() {
        if (crawlStatusPoller) {
            clearInterval(crawlStatusPoller);
            crawlStatusPoller = null;
        }
    }

    // ============ 页面加载逻辑 ============
    async function loadPage() {
        const dateStr = datePicker.value;
        
        if (currentSource === 'all') {
            // 加载所有来源
            await loadAllSources(dateStr);
        } else {
            // 加载单个来源
            await loadSingleSource(currentSource, dateStr);
        }
    }

    async function loadSingleSource(sourceKey, dateStr) {
        try {
            const response = await fetch(`/api/news/${sourceKey}?date=${dateStr}`);
            const data = await response.json();
            
            // 根据响应状态选择显示
            if (data.status === 'loaded') {
                // 状态1: 已加载新闻
                allNews = data.data.map(item => ({
                    ...item,
                    source: data.source,
                    sourceKey: sourceKey
                }));
                renderNews();
                showLoadedState();
                stopStatusPoller();
                
            } else if (data.status === 'loading') {
                // 状态2: 正在加载
                showLoadingState();
                startStatusPoller(sourceKey);
                
            } else if (data.status === 'empty') {
                // 状态3: 无数据，显示重新抓取按钮
                showEmptyState();
            }
            
        } catch (error) {
            console.error(`Failed to load ${sourceKey}:`, error);
            showEmptyState();
        }
    }

    async function loadAllSources(dateStr) {
        try {
            const sources = ['fujian', 'hainan', 'nanfang', 'guangzhou', 'guangxi'];
            const results = [];
            let anyLoading = false;
            let anyEmpty = false;
            let anyLoaded = false;
            
            const responses = await Promise.all(
                sources.map(source =>
                    fetch(`/api/news/${source}?date=${dateStr}`).then(r => r.json())
                )
            );
            
            // 分析响应状态
            responses.forEach(data => {
                if (data.status === 'loaded') {
                    anyLoaded = true;
                    results.push(...(data.data || []));
                } else if (data.status === 'loading') {
                    anyLoading = true;
                } else if (data.status === 'empty') {
                    anyEmpty = true;
                }
            });
            
            // 显示优先级: 已加载 > 正在加载 > 无数据
            if (anyLoaded) {
                allNews = results;
                renderNews();
                showLoadedState();
                stopStatusPoller();
                
            } else if (anyLoading) {
                // 至少有一个来源在加载，显示加载状态
                showLoadingState();
                appendLog('多个来源正在并行爬取...');
                // 为第一个加载的来源启动轮询
                const loadingSource = responses.find(r => r.status === 'loading');
                if (loadingSource) {
                    startStatusPoller(loadingSource.crawl_status.source_key);
                }
                
            } else {
                // 全部为空
                showEmptyState();
            }
            
        } catch (error) {
            console.error('Failed to load all sources:', error);
            showEmptyState();
        }
    }

    // ============ 事件监听器 ============
    
    // 日期选择
    if (datePicker) {
        datePicker.addEventListener('change', (e) => {
            if (e.target.value) {
                currentDate = new Date(e.target.value);
                updateDateDisplay();
                loadPage();
            }
        });
    }

    // 日期导航
    if (prevDayBtn) {
        prevDayBtn.addEventListener('click', () => {
            currentDate.setDate(currentDate.getDate() - 1);
            updateDateDisplay();
            loadPage();
        });
    }

    if (nextDayBtn) {
        nextDayBtn.addEventListener('click', () => {
            if (isToday(currentDate)) return;
            currentDate.setDate(currentDate.getDate() + 1);
            updateDateDisplay();
            loadPage();
        });
    }

    // 来源切换
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (window.IS_SELECTION_PAGE) return;

            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            currentSource = btn.dataset.source;
            sessionStorage.setItem('currentSource', currentSource);

            loadPage();
        });
    });

    // 手动抓取按钮
    if (fetchButton) {
        fetchButton.addEventListener('click', async () => {
            const dateStr = datePicker.value;
            const sourceKey = currentSource === 'all' ? 'fujian' : currentSource;  // 选择一个来源作为示例
            
            fetchButton.disabled = true;
            showLoadingState();
            appendLog(`开始手动抓取 ${sourceKey}...`);
            
            try {
                const response = await fetch(`/api/crawl/start/${sourceKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ date: dateStr })
                });
                
                if (response.ok) {
                    startStatusPoller(sourceKey);
                } else {
                    appendLog('✗ 启动抓取失败');
                    showEmptyState();
                }
            } catch (error) {
                appendLog(`✗ 错误: ${error.message}`);
                showEmptyState();
            } finally {
                fetchButton.disabled = false;
            }
        });
    }

    // ============ 辅助函数 ============

    function isToday(date) {
        const today = new Date();
        return date.getDate() === today.getDate() &&
            date.getMonth() === today.getMonth() &&
            date.getFullYear() === today.getFullYear();
    }

    function updateDateDisplay() {
        if (!dateDisplay) return;
        const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
        dateDisplay.textContent = currentDate.toLocaleDateString('zh-CN', options);

        const yyyy = currentDate.getFullYear();
        const mm = String(currentDate.getMonth() + 1).padStart(2, '0');
        const dd = String(currentDate.getDate()).padStart(2, '0');
        datePicker.value = `${yyyy}-${mm}-${dd}`;
        sessionStorage.setItem('currentDate', `${yyyy}-${mm}-${dd}`);

        if (isToday(currentDate)) {
            nextDayBtn.classList.add('disabled');
        } else {
            nextDayBtn.classList.remove('disabled');
        }
    }

    // ============ 新闻渲染 ============

    // Modal Elements
    const modal = document.getElementById('article-modal');
    const closeBtn = document.querySelector('.close-btn');
    const articleCn = document.getElementById('article-cn');
    const articleKo = document.getElementById('article-ko');

    closeBtn.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    async function openArticle(url) {
        modal.style.display = 'block';
        articleCn.innerHTML = '<div class="loading">正在加载原文...</div>';
        articleKo.innerHTML = '<div class="loading">正在翻译...</div>';

        try {
            const res = await fetch(`/api/article?url=${encodeURIComponent(url)}`);
            const data = await res.json();

            if (data.status === 'success') {
                articleCn.innerHTML = data.content_cn;
                articleKo.innerHTML = data.content_ko.map(p => `<p>${p}</p>`).join('');
            } else {
                articleCn.innerHTML = '<p>加载失败</p>';
                articleKo.innerHTML = '<p>Translation failed</p>';
            }
        } catch (err) {
            articleCn.innerHTML = '<p>网络错误</p>';
            articleKo.innerHTML = '<p>Network error</p>';
        }
    }

    function renderNews() {
        newsGrid.innerHTML = '';

        let filteredNews = allNews;

        if (!window.IS_SELECTION_PAGE) {
            filteredNews = currentSource === 'all'
                ? allNews
                : allNews.filter(item => item.sourceKey === currentSource);
        }

        if (filteredNews.length === 0) {
            newsGrid.innerHTML = '<div class="loading">暂无新闻</div>';
            return;
        }

        filteredNews.forEach(item => {
            const card = document.createElement('article');
            card.className = 'news-card';
            card.innerHTML = `
                <div class="news-content">
                    <div class="news-header">
                        <span class="news-source">${item.source}</span>
                        ${item.section ? `<span class="news-section">${item.section}</span>` : ''}
                    </div>
                    <h2 class="news-title">
                        <div class="title-cn">${item.title}</div>
                        <div class="title-ko">${item.title_ko || 'Loading...'}</div>
                    </h2>
                </div>
                <button class="star-btn ${item.starred ? 'active' : ''}" title="加入筛选筐">★</button>
            `;

            card.addEventListener('click', () => openArticle(item.link));

            const starBtn = card.querySelector('.star-btn');
            starBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const isStarred = !starBtn.classList.contains('active');
                starBtn.classList.toggle('active');

                if (window.IS_SELECTION_PAGE && !isStarred) {
                    card.style.display = 'none';
                }

                try {
                    await fetch('/api/star', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            url: item.link,
                            starred: isStarred,
                            item: item
                        })
                    });

                    item.starred = isStarred;

                } catch (err) {
                    console.error('Star error:', err);
                    starBtn.classList.toggle('active');
                    if (window.IS_SELECTION_PAGE && !isStarred) {
                        card.style.display = 'flex';
                    }
                }
            });

            newsGrid.appendChild(card);
        });
    }

    async function fetchSelectedNews() {
        showLoadingState();
        appendLog('正在获取筛选筐内容...');
        
        try {
            const res = await fetch('/api/selection');
            const data = await res.json();
            if (data.status === 'success') {
                allNews = data.data;
                renderNews();
                showLoadedState();
            } else {
                showEmptyState();
            }
        } catch (err) {
            console.error(err);
            showEmptyState();
        }
    }

});
