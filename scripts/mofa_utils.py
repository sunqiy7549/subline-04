import json
import re
import os

def parse_mofa_article(json_path):
    """
    Parses a MOFA article JSON file and extracts news items.
    Returns a list of dictionaries:
    {
        "region": str,
        "newspaper": str,
        "date": str,
        "page": str,
        "headline": str,
        "full_text": str
    }
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        content = data.get('content', '')
        if not content:
            return []

        # 1. Split by Region (e.g., [광둥성], [푸젠성])
        # Regex to find region headers
        region_pattern = r'\[(.*?)\]'
        regions = re.split(region_pattern, content)
        
        items = []
        current_region = "Unknown"
        
        # re.split returns [text_before, match1, text_after, match2, ...]
        # So we iterate and track current region
        
        for i, part in enumerate(regions):
            part = part.strip()
            if not part: continue
            
            # If it's a region name (short, no newlines usually)
            if len(part) < 20 and '\n' not in part and i % 2 == 1: 
                current_region = part
            elif i % 2 == 0: # Content part
                # Split into numbered items (1., 2.)
                # Use a lookahead for "digit dot space" or "digit dot newline"
                news_items = re.split(r'(?=\n\d+\s*\.)', part)
                
                for item_text in news_items:
                    item_text = item_text.strip()
                    if not item_text: continue
                    
                    # Must start with a number to be a valid item
                    if not re.match(r'\d+\s*\.', item_text):
                        continue
                        
                    # Parse Metadata
                    # Strategy: Look for citation in the first 300 characters
                    headline_area = item_text[:300]
                    
                    # Regex: Parens containing a date pattern
                    citation_matches = re.findall(r'\(([^)]*?\d{1,2}\.\d{1,2}[^)]*?)\)', headline_area)
                    
                    citation = ""
                    if citation_matches:
                        citation = citation_matches[-1]
                    else:
                        # Fallback
                        end_match = re.search(r'([\u4e00-\u9fff]+\s+\d{1,2}\.\d{1,2}\s+[A-Z]?\d+)', headline_area)
                        if end_match:
                            citation = end_match.group(1)
                            
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
                            newspaper_parts = []
                            for p in parts:
                                p = p.strip()
                                if not p: continue
                                
                                if re.match(r'^[A-Z]?\d+$', p):
                                    page = p
                                elif re.search(r'[\u4e00-\u9fff]', p):
                                    newspaper_parts.append(p)
                            
                            if newspaper_parts:
                                newspaper = "".join(newspaper_parts)

                    # Clean headline (remove number and citation if possible)
                    headline = item_text.split('\n')[0]
                    # Remove leading number
                    headline = re.sub(r'^\d+\s*\.\s*', '', headline)
                    
                    items.append({
                        "region": current_region,
                        "newspaper": newspaper,
                        "date": date,
                        "page": page,
                        "headline": headline,
                        "full_text": item_text,
                        "source_file": os.path.basename(json_path)
                    })
                    
        return items

    except Exception as e:
        print(f"Error parsing {json_path}: {e}")
        return []
