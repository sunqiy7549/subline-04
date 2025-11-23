# Content Fetching Report

## Overview
*   **Total Matched Items**: 120
*   **Date Range**: Nov 2024 - Nov 2025
*   **Output Directory**: `data/originals/`
*   **Dataset File**: `data/dataset.json`

## Statistics by Newspaper
| Newspaper | Count |
|---|---|
| 南方日报 (Nanfang Daily) | 65 |
| 福建日报 (Fujian Daily) | 32 |
| 海南日报 (Hainan Daily) | 18 |
| 广州日报 (Guangzhou Daily) | 5 |

## Sample Matches
| Date | Newspaper | Korean Headline | Chinese Title | Score |
|---|---|---|---|---|
| 11.22 | 南方日报 | 왕웨이중(王伟中) 성장, 아랍에미리트... | 王伟中会见阿联酋联邦最高委员会成员... | 10 |
| 12.25 | 南方日报 | 황쿤밍(黄坤明) 광둥성 당서기... | 黄坤明王伟中会见澳门特别行政区... | 20 |
| 1.7 | 海南日报 | 신임 하이난성 상무위원... (판샤오쥔) | 范少军同志任中共海南省委常委 | 10 |
| 4.2 | 福建日报 | 자오룽 성장, 푸저우(福州)에서... | 福州滨海快线启动全线列车动态调试 | 10 |

## Notes
*   **Success Rate**: High for articles mentioning specific people (names in parentheses).
*   **Challenges**: Some topic mismatches occurred when only location names matched (e.g., "Fujian" or "Hainan").
*   **Excluded**: Items with multiple low-confidence candidates were skipped to maintain quality.
