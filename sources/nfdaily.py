"""
Nanfang Daily (南方日报) URL generators.
"""
from datetime import date


def nfdaily_section_url(d: date, section: str = "A01") -> str:
    """
    Generate direct section page URL for Nanfang Daily.
    
    Args:
        d: Date for the newspaper
        section: Section identifier (e.g., 'A01', 'A02', 'A03')
        
    Returns:
        URL string for the section page
        
    Example:
        >>> from datetime import date
        >>> nfdaily_section_url(date(2025, 11, 23))
        'https://epaper.southcn.com/nfdaily/html/202511/23/node_A01.html'
    """
    return d.strftime(f"https://epaper.southcn.com/nfdaily/html/%Y%m/%d/node_{section}.html")


def nfdaily_article_url(d: date, article: str) -> str:
    """
    Generate direct article URL for Nanfang Daily.
    
    Args:
        d: Date for the newspaper
        article: Article identifier (e.g., 'content_10154249')
        
    Returns:
        URL string for the article page
    """
    return d.strftime(f"https://epaper.nfnews.com/nfdaily/html/%Y%m/%d/{article}.html")
