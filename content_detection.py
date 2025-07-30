"""
Content Detection Utilities

This module provides functions for detecting adult content and doujinshi
in manga titles to ensure appropriate handling in the generation workflow.

Functions:
    is_adult_content: Detect adult/sexual content keywords
    is_potential_doujinshi: Detect doujinshi or self-published works
"""

from typing import List


def is_adult_content(manga_title: str) -> bool:
    """
    Detect if manga title contains adult/sexual content keywords that might break Google Search grounding.
    
    Args:
        manga_title: The manga title to analyze
        
    Returns:
        True if adult content is detected, False otherwise
    """
    # Japanese adult content keywords
    japanese_keywords = [
        '性的', '官能', 'エロ', 'ラブ', 'BL', 'TL', 'GL', 'エッチ', 
        'セックス', '恋愛', 'ティーンズラブ', 'ボーイズラブ', 'ガールズラブ',
        '大人', '誘惑', '甘い', '溺れて', '熱', '番', 'α', 'β', 'Ω',
        'オメガバース', 'ヤリチン', 'ヤリマン', '処女', '童貞', 'セクシー'
    ]
    
    # English adult content keywords
    english_keywords = [
        'love', 'romance', 'adult', 'mature', 'sexual', 'erotic', 'sexy', 
        'hot', 'steamy', 'passionate', 'seductive', 'temptation', 'desire',
        'boys love', 'girls love', 'yaoi', 'yuri', 'smut', 'hentai'
    ]
    
    # Check title (case insensitive for English)
    title_lower = manga_title.lower()
    
    # Check Japanese keywords (case sensitive)
    for keyword in japanese_keywords:
        if keyword in manga_title:
            return True
    
    # Check English keywords (case insensitive)        
    for keyword in english_keywords:
        if keyword in title_lower:
            return True
            
    return False


def is_potential_doujinshi(manga_title: str) -> bool:
    """
    Detect if manga title might be a doujinshi or self-published work.
    
    Args:
        manga_title: The manga title to analyze
        
    Returns:
        True if likely doujinshi, False otherwise
    """
    # Doujinshi indicators
    doujinshi_indicators = [
        # Very short titles (often doujinshi naming convention)
        len(manga_title.strip()) <= 8,
        # Unusual lowercase/mixed case (like motolog)
        manga_title.islower() and len(manga_title) > 3,
        # Contains common doujinshi terms
        'ログ' in manga_title,  # "log" 
        'まとめ' in manga_title,  # "matome" (compilation)
        '個人誌' in manga_title,  # "kojinshi" (personal publication)
        'サークル' in manga_title,  # "circle" (doujin circle)
        'オリジナル' in manga_title,  # "original"
        # Very specific volume indicators
        'No.' in manga_title,
        '#' in manga_title,
        # Unusual punctuation patterns
        manga_title.count('!') > 1,
        '！！' in manga_title,
    ]
    
    # If multiple indicators present, likely doujinshi
    indicator_count = sum(doujinshi_indicators)
    return indicator_count >= 2 or manga_title.islower()