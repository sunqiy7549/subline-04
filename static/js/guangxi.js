document.addEventListener('DOMContentLoaded', () => {
    const newsGrid = document.getElementById('news-grid');
    const progressContainer = document.getElementById('progress-container');
    const loadBtn = document.getElementById('load-btn');

    // Date Elements
    const datePicker = document.getElementById('date-picker');
    const dateDisplay = document.getElementById('current-date-display');
    const prevDayBtn = document.getElementById('prev-day');
    const nextDayBtn = document.getElementById('next-day');

    // Initialize Date
    let currentDate = new Date();
    const urlParams = new URLSearchParams(window.location.search);
    const dateParam = urlParams.get('date');
    if (dateParam) {
        currentDate = new Date(dateParam);
    }

    updateDateDisplay();
    fetchGuangxiNews();

    // Date Event Listeners
    if (datePicker) {
        datePicker.addEventListener('change', (e) => {
            if (e.target.value) {
                currentDate = new Date(e.target.value);
                updateDateDisplay();
                fetchGuangxiNews();
            }
        });
    }

    if (prevDayBtn) {
        prevDayBtn.addEventListener('click', () => {
            currentDate.setDate(currentDate.getDate() - 1);
            updateDateDisplay();
            fetchGuangxiNews();
        });
    }

    if (nextDayBtn) {
        nextDayBtn.addEventListener('click', () => {
            if (isToday(currentDate)) return;
            currentDate.setDate(currentDate.getDate() + 1);
            updateDateDisplay();
            fetchGuangxiNews();
        });
    }

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

        if (isToday(currentDate)) {
            nextDayBtn.classList.add('disabled');
        } else {
            nextDayBtn.classList.remove('disabled');
        }
    }

    async function fetchGuangxiNews() {
        const dateStr = datePicker.value;
        if (!dateStr) return;

        // Check cache first
        const cacheKey = `guangxi_news_${dateStr}`;
        const cachedData = sessionStorage.getItem(cacheKey);

        if (cachedData) {
            console.log('Using cached Guangxi news');
            const articles = JSON.parse(cachedData);
            renderArticles(articles);
            return;
        }

        // Clear previous content
        newsGrid.innerHTML = '';
        progressContainer.innerHTML = '';

        // Show progress indicator
        const progressHTML = `
            <div id="guangxi-progress" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <h3 style="margin: 0 0 15px 0; font-size: 18px;">🔄 正在加载广西日报...</h3>
                <div style="background: rgba(255,255,255,0.2); border-radius: 8px; height: 30px; overflow: hidden; margin-bottom: 15px;">
                    <div id="progress-bar" style="background: linear-gradient(90deg, #4ade80, #22c55e); height: 100%; width: 0%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px;">
                        <span id="progress-percent">0%</span>
                    </div>
                </div>
                <div id="progress-status" style="font-size: 14px; line-height: 1.6;">
                    <div>📊 预计需要: <strong>30-40分钟</strong></div>
                    <div>⏱️ 状态: <span id="status-text">开始抓取...</span></div>
                </div>
            </div>
        `;
        progressContainer.innerHTML = progressHTML;

        // Simulate progress
        let progress = 0;
        let messageIndex = 0;
        const statusMessages = [
            '正在连接广西日报服务器...',
            '正在抓取第001版文章...',
            '正在抓取第002版文章...',
            '正在抓取第003版文章...',
            '正在抓取第004版文章...',
            '正在翻译文章标题...',
            '即将完成...'
        ];

        const progressInterval = setInterval(() => {
            if (progress < 95) {
                progress += Math.random() * 2;
                const progressBar = document.getElementById('progress-bar');
                const progressPercent = document.getElementById('progress-percent');
                const statusText = document.getElementById('status-text');

                if (progressBar && progressPercent) {
                    progressBar.style.width = `${Math.min(progress, 95)}%`;
                    progressPercent.textContent = `${Math.floor(Math.min(progress, 95))}%`;
                }

                const newMessageIndex = Math.floor(progress / 15);
                if (newMessageIndex !== messageIndex && newMessageIndex < statusMessages.length) {
                    messageIndex = newMessageIndex;
                    if (statusText) {
                        statusText.textContent = statusMessages[messageIndex];
                    }
                }
            }
        }, 2000);

        try {
            // Fetch with long timeout
            const res = await fetch(`/api/news/guangxi?date=${dateStr}`, {
                signal: AbortSignal.timeout(900000)
            });
            const data = await res.json();

            clearInterval(progressInterval);

            if (data.status === 'success') {
                // Show 100%
                const progressBar = document.getElementById('progress-bar');
                const progressPercent = document.getElementById('progress-percent');
                const statusText = document.getElementById('status-text');

                if (progressBar) {
                    progressBar.style.width = '100%';
                    progressPercent.textContent = '100%';
                    statusText.textContent = `✅ 完成！共抓取 ${data.data.length} 篇文章`;

                    setTimeout(() => {
                        progressContainer.innerHTML = '';
                    }, 2000);
                }

                // Save to cache
                sessionStorage.setItem(cacheKey, JSON.stringify(data.data));
                renderArticles(data.data);
            } else {
                throw new Error(data.message || 'Fetch failed');
            }
        } catch (err) {
            clearInterval(progressInterval);
            console.error(err);
            const statusText = document.getElementById('status-text');
            if (statusText) {
                statusText.innerHTML = '❌ 加载失败或超时';
                statusText.style.color = '#fca5a5';
            }
        }
    }

    function renderArticles(articles) {
        newsGrid.innerHTML = '';
        if (articles.length === 0) {
            newsGrid.innerHTML = '<div class="loading">暂无新闻</div>';
            return;
        }

        articles.forEach(item => {
            const card = document.createElement('article');
            card.className = 'news-card';
            card.innerHTML = `
                <div class="news-content">
                    <div class="news-header">
                        <span class="news-source">广西日报</span>
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
                } catch (err) {
                    console.error('Star error:', err);
                    starBtn.classList.toggle('active');
                }
            });

            newsGrid.appendChild(card);
        });
    }

    // Modal Logic (Reused)
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

    async function toggleStar(e, item, btn) {
        e.stopPropagation();
        const isStarred = !btn.classList.contains('active');
        btn.classList.toggle('active');

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
        } catch (err) {
            console.error('Star error:', err);
            btn.classList.toggle('active'); // Revert
        }
    }
});
