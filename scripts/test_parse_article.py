import json
import re
import glob
import os

def parse_citations(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    content = data['content']
    
    # Split content into sections by Region [...]
    # Then split by "1. ", "2. " etc.
    
    # Regex to find regions: [Region Name]
    # We iterate through the text to find regions and their content
    
    region_pattern = re.compile(r'\[([^\]]+)\]')
    regions = []
    
    # Find all region headers and their positions
    for match in region_pattern.finditer(content):
        regions.append({
            "name": match.group(1),
            "start": match.end(),
            "end": len(content) # Default to end of string
        })
    
    # Fix end positions
    for i in range(len(regions) - 1):
        regions[i]['end'] = regions[i+1]['start'] - len(regions[i+1]['name']) - 2 # subtract [Name] length
        
    items = []
    
    for region in regions:
        region_text = content[region['start']:region['end']]
        
        # Find items starting with "1.", "2.", etc.
        # We look for "\n\d+\." or "^\d+\."
        # We can split by this pattern, but we need to keep the delimiter
        
        # Regex: newline followed by digit and dot (allow whitespace)
        item_splits = re.split(r'(?:\n|^)(\d+\s*\.)', region_text)
        
        # re.split with capturing group returns [preamble, delimiter, content, delimiter, content...]
        # item_splits[0] is usually empty or preamble
        
        current_item_num = None
        
        for i in range(1, len(item_splits), 2):
            num_marker = item_splits[i]
            item_body = item_splits[i+1]
            
            full_item_text = num_marker + item_body
            # Clean up newlines for regex processing, but keep them for display if needed
            # Actually, better to replace newlines with spaces for citation matching
            text_flat = full_item_text.replace('\n', ' ')
            
            # Debug
            print(f"DEBUG: Processing item: {text_flat[:30]}...")
            
            # Strategy: Look for citation in the first 200 characters (Headline area)
            # Citation MUST contain a date-like pattern (\d.\d) or be at the end of the headline
            
            headline_area = text_flat[:300] # Look at first 300 chars
            
            # Regex: Parens containing a date pattern
            # e.g. (11.7 南方日报 A1) or (福建日报 11.8 A2)
            citation_matches = re.findall(r'\(([^)]*?\d{1,2}\.\d{1,2}[^)]*?)\)', headline_area)
            
            citation = ""
            if citation_matches:
                # Take the one that looks most like a citation (has newspaper and page?)
                # Usually it's the last one in the headline area (if multiple)
                citation = citation_matches[-1]
                print(f"DEBUG: Found citation via date-parens: {citation}")
            else:
                # Fallback: Look for "Newspaper Date Page" pattern without parens (or malformed)
                # e.g. ... 면담福建日报 11.9 A1
                end_match = re.search(r'([\u4e00-\u9fff]+\s+\d{1,2}\.\d{1,2}\s+[A-Z]?\d+)', headline_area)
                if end_match:
                    citation = end_match.group(1)
                    print(f"DEBUG: Found citation via fallback regex: {citation}")
            
            newspaper = "Unknown"
            page = "Unknown"
            date = "Unknown"
            
            if citation:
                # Parse Citation
                date_match = re.search(r'(\d{1,2}\.\d{1,2})', citation)
                if date_match:
                    date = date_match.group(1)
                    rest = citation.replace(date, '').strip()
                    
                    parts = rest.split()
                    # print(f"DEBUG: Parts: {parts}")
                    
                    newspaper_parts = []
                    for part in parts:
                        part = part.strip()
                        if not part: continue
                        
                        if re.match(r'^[A-Z]?\d+$', part):
                            page = part
                        elif re.search(r'[\u4e00-\u9fff]', part):
                            newspaper_parts.append(part)
                            
                    if newspaper_parts:
                        newspaper = "".join(newspaper_parts)
                else:
                     print(f"DEBUG: Date not found in citation: {citation}")
                     pass
            
            items.append({
                "region": region['name'],
                "headline": full_item_text.strip()[:50] + "...",
                "citation_raw": citation,
                "parsed": {
                    "newspaper": newspaper,
                    "date": date,
                    "page": page
                }
            })
            
    return items

def main():
    # Find the specific file we looked at
    files = glob.glob("data/mofa/articles/*11.6-11.12*.json")
    if not files:
        print("File not found.")
        return

    target_file = files[0]
    print(f"Analyzing: {target_file}")
    
    items = parse_citations(target_file)
    
    print(f"\nFound {len(items)} items:")
    for i, item in enumerate(items, 1):
        p = item['parsed']
        print(f"{i}. [{item['region']}] {p['newspaper']} | {p['date']} | {p['page']}")
        print(f"   Headline: {item['headline'][:50]}...")

if __name__ == "__main__":
    main()
