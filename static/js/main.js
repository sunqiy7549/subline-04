document.addEventListener('DOMContentLoaded', () => {
    const newsGrid = document.getElementById('news-grid');
    const navBtns = document.querySelectorAll('.nav-btn');

    let allNews = [];
    // Restore currentSource from sessionStorage or default to 'all'
    let currentSource = sessionStorage.getItem('currentSource') || 'all';

    // Restore date from sessionStorage or default to today
    let currentDate = new Date();
    const savedDate = sessionStorage.getItem('currentDate');
    if (savedDate && !window.IS_SELECTION_PAGE) {
        currentDate = new Date(savedDate);
    }

    // Date Elements
    const datePicker = document.getElementById('date-picker');
    const dateDisplay = document.getElementById('current-date-display');
    const prevDayBtn = document.getElementById('prev-day');
    const nextDayBtn = document.getElementById('next-day');

    // Initialize
    if (window.IS_SELECTION_PAGE) {
        fetchSelectedNews();
    } else {
        // Set active button based on restored source
        navBtns.forEach(btn => {
            if (btn.dataset.source === currentSource) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        updateDateDisplay();
        fetchAllNews();
    }

    // Date Event Listeners
    if (datePicker) {
        datePicker.addEventListener('change', (e) => {
            if (e.target.value) {
                currentDate = new Date(e.target.value);
                updateDateDisplay();
                fetchAllNews();
            }
        });
    }

    if (prevDayBtn) {
        prevDayBtn.addEventListener('click', () => {
            currentDate.setDate(currentDate.getDate() - 1);
            updateDateDisplay();
            fetchAllNews();
        });
    }

    if (nextDayBtn) {
        nextDayBtn.addEventListener('click', () => {
            if (isToday(currentDate)) return;
            currentDate.setDate(currentDate.getDate() + 1);
            updateDateDisplay();
            fetchAllNews();
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
        sessionStorage.setItem('currentDate', `${yyyy}-${mm}-${dd}`);

        if (isToday(currentDate)) {
            nextDayBtn.classList.add('disabled');
        } else {
            nextDayBtn.classList.remove('disabled');
        }
    }

    // Event Listeners
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (window.IS_SELECTION_PAGE) return;

            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            currentSource = btn.dataset.source;
            sessionStorage.setItem('currentSource', currentSource);

            renderNews();
        });
    });

    async function fetchSelectedNews() {
        newsGrid.innerHTML = '<div class="loading">正在获取筛选筐内容...</div>';
        try {
            const res = await fetch('/api/selection');
            const data = await res.json();
            if (data.status === 'success') {
                allNews = data.data;
                renderNews();
            } else {
                newsGrid.innerHTML = '<div class="loading">获取失败</div>';
            }
        } catch (err) {
            console.error(err);
            newsGrid.innerHTML = '<div class="loading">网络错误</div>';
        }
    }

    async function fetchAllNews() {
        if (window.IS_SELECTION_PAGE) return;

        const dateStr = datePicker.value;
        const cacheKey = `news_cache_${dateStr}`;

        const cachedData = sessionStorage.getItem(cacheKey);
        if (cachedData) {
            console.log('Using cached news data');
            allNews = JSON.parse(cachedData);
            renderNews();
            return;
        }

        newsGrid.innerHTML = '<div class="loading">正在获取报纸内容...</div>';
        allNews = [];

        try {
            // Fetch fast sources ONLY (Fujian, Hainan, Nanfang, Guangzhou)
            // Guangxi is now handled separately
            const fastSources = ['fujian', 'hainan', 'nanfang', 'guangzhou'];
            const fastPromises = fastSources.map(source =>
                fetch(`/api/news/${source}?date=${dateStr}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === 'success') {
                            return data.data.map(item => ({
                                ...item,
                                source: data.source,
                                sourceKey: source
                            }));
                        }
                        return [];
                    })
                    .catch(err => {
                        console.error(`Failed to fetch ${source}:`, err);
                        return [];
                    })
            );

            const fastResults = await Promise.all(fastPromises);
            allNews = fastResults.flat();

            sessionStorage.setItem(cacheKey, JSON.stringify(allNews));
            renderNews();

        } catch (error) {
            console.error('Error fetching news:', error);
            newsGrid.innerHTML = '<div class="loading">获取新闻失败，请稍后重试</div>';
        }
    }

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

        // Special handling for Guangxi Daily view
        if (currentSource === 'guangxi') {
            const dateStr = datePicker ? datePicker.value : '';
            const guangxiUrl = `/guangxi?date=${dateStr}`;

            newsGrid.innerHTML = `
                <div style="text-align: center; padding: 50px; width: 100%;">
                    <div style="font-size: 60px; margin-bottom: 20px;">📰</div>
                    <h2 style="margin-bottom: 15px; color: #333;">广西日报</h2>
                    <p style="color: #666; margin-bottom: 30px;">广西日报内容较多，加载时间较长。请点击下方按钮在新标签页中打开。</p>
                    <a href="${guangxiUrl}" target="_blank" class="nav-btn active" style="text-decoration: none; display: inline-block; padding: 12px 30px; font-size: 16px;">
                        在新标签页中打开广西日报
                    </a>
                </div>
            `;
            return;
        }

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

                    // Update cache
                    if (!window.IS_SELECTION_PAGE && datePicker) {
                        const dateStr = datePicker.value;
                        const cacheKey = `news_cache_${dateStr}`;
                        sessionStorage.setItem(cacheKey, JSON.stringify(allNews));
                    } else if (window.IS_SELECTION_PAGE) {
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            if (key && key.startsWith('news_cache_')) {
                                try {
                                    const cachedNews = JSON.parse(sessionStorage.getItem(key));
                                    const itemIndex = cachedNews.findIndex(n => n.link === item.link);
                                    if (itemIndex !== -1) {
                                        cachedNews[itemIndex].starred = isStarred;
                                        sessionStorage.setItem(key, JSON.stringify(cachedNews));
                                    }
                                } catch (e) {
                                    console.error('Error updating cache:', e);
                                }
                            }
                        }
                    }
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


});
