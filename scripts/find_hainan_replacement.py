import json

DATASET_FILE = "data/dataset.json"

def main():
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    hainan_items = [item for item in data if item.get('newspaper') == '海南日报']
    
    print(f"Found {len(hainan_items)} Hainan Daily items.")
    for i, item in enumerate(hainan_items):
        print(f"--- Item {i} ---")
        print(f"Korean: {item.get('korean_headline')}")
        print(f"Chinese: {item.get('chinese_title')}")
        # Simple check: do they share any numbers or names?
        print(f"URL: {item.get('source_url')}")

if __name__ == "__main__":
    main()
