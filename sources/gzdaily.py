"""
Guangzhou Daily (广州日报) URL generators.
"""
from datetime import date


def gzdaily_index_url(d: date) -> str:
    """
    Generate PC digital newspaper index URL for Guangzhou Daily.
    
    This is the stable index page containing all sections for the day.
    Structure is pure HTML, does not rely on JS.
    
    Args:
        d: Date for the newspaper
        
    Returns:
        URL string for the PC index page
        
    Example:
        >>> from datetime import date
        >>> gzdaily_index_url(date(2025, 11, 22))
        'https://gzdaily.dayoo.com/pc/html/2025-11/22/index_2025-11-22.htm'
    """
    return d.strftime("https://gzdaily.dayoo.com/pc/html/%Y-%m/%d/index_%Y-%m-%d.htm")


def gzdaily_section_url(d: date, section: str) -> str:
    """
    Generate PC section page URL for Guangzhou Daily.
    
    Args:
        d: Date for the newspaper
        section: Section identifier (e.g., 'node_868', 'node_869')
        
    Returns:
        URL string for the section page
    """
    date_path = d.strftime("%Y-%m/%d")
    return f"https://gzdaily.dayoo.com/pc/html/{date_path}/{section}.htm"
