#!/usr/bin/env python3
"""
测试重构后的系统架构
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """测试所有导入"""
    print("测试导入...")
    try:
        from app import (
            CrawlState, SourceCrawlStatus, CRAWL_STATUS, 
            _perform_crawl, get_news_realtime
        )
        print("✓ 所有导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_crawl_status():
    """测试爬取状态类"""
    print("\n测试爬取状态类...")
    try:
        from app import SourceCrawlStatus, CrawlState
        
        status = SourceCrawlStatus('fujian')
        assert status.source_key == 'fujian'
        assert status.state == CrawlState.IDLE
        
        # 测试添加日志
        status.add_log("测试日志")
        assert len(status.logs) == 1
        
        # 测试转换为字典
        status_dict = status.to_dict()
        assert status_dict['state'] == 'idle'
        
        print("✓ 爬取状态类测试通过")
        return True
    except Exception as e:
        print(f"✗ 爬取状态类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_structure():
    """测试API响应结构"""
    print("\n测试API响应结构...")
    try:
        from app import app
        from datetime import datetime
        
        with app.test_client() as client:
            # 测试爬取状态API
            response = client.get('/api/crawl/status/fujian')
            assert response.status_code == 200
            data = response.json
            assert 'state' in data
            assert 'logs' in data
            assert 'progress' in data
            
            print("✓ API响应结构测试通过")
            return True
    except Exception as e:
        print(f"✗ API响应结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_html():
    """测试HTML UI结构"""
    print("\n测试HTML UI结构...")
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        required_elements = [
            'news-loaded-state',
            'news-loading-state',
            'news-empty-state',
            'progress-bar',
            'log-stream',
            'fetch-button'
        ]
        
        for elem in required_elements:
            assert elem in html, f"缺少元素: {elem}"
        
        print("✓ HTML UI结构测试通过")
        return True
    except Exception as e:
        print(f"✗ HTML UI结构测试失败: {e}")
        return False

def test_js_logic():
    """测试JavaScript逻辑结构"""
    print("\n测试JavaScript逻辑结构...")
    try:
        with open('static/js/main.js', 'r', encoding='utf-8') as f:
            js = f.read()
        
        required_functions = [
            'showLoadedState',
            'showLoadingState',
            'showEmptyState',
            'startStatusPoller',
            'stopStatusPoller',
            'loadPage',
            'loadSingleSource',
            'loadAllSources',
            'appendLog'
        ]
        
        for func in required_functions:
            assert f'function {func}' in js or f'{func}()' in js, f"缺少函数: {func}"
        
        print("✓ JavaScript逻辑结构测试通过")
        return True
    except Exception as e:
        print(f"✗ JavaScript逻辑结构测试失败: {e}")
        return False

if __name__ == '__main__':
    results = []
    
    results.append(("导入测试", test_imports()))
    results.append(("爬取状态类", test_crawl_status()))
    results.append(("API结构", test_api_structure()))
    results.append(("HTML结构", test_ui_html()))
    results.append(("JavaScript结构", test_js_logic()))
    
    print("\n" + "="*50)
    print("测试总结:")
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    passed = sum(1 for _, r in results if r)
    print(f"\n通过: {passed}/{len(results)}")
    
    sys.exit(0 if passed == len(results) else 1)
