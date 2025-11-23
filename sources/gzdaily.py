"""
Guangzhou Daily (广州日报) URL generators.
"""
from datetime import date


def gzdaily_index_url(d: date) -> str:
    """
    Generate H5 digital newspaper index URL for Guangzhou Daily.
    
    Args:
        d: Date for the newspaper
        
    Returns:
        URL string for the H5 index page
        
    Example:
        >>> from datetime import date
        >>> gzdaily_index_url(date(2025, 11, 23))
        'https://gzdaily.dayoo.com/h5/html5/2025-11/23/node_867.htm'
    """
    return d.strftime("https://gzdaily.dayoo.com/h5/html5/%Y-%m/%d/node_867.htm")


def gzdaily_section_url(d: date, section: str) -> str:
    """
    Generate H5 section page URL for Guangzhou Daily.
    
    Args:
        d: Date for the newspaper
        section: Section identifier (e.g., 'node_868', 'node_869')
        
    Returns:
        URL string for the section page
    """
    date_path = d.strftime("%Y-%m/%d")
    return f"https://gzdaily.dayoo.com/h5/html5/{date_path}/{section}.htm"
