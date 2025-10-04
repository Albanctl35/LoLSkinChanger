#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalization utilities for text matching
"""

import unicodedata
import re
from rapidfuzz.distance import Levenshtein


def normalize_text(s: str) -> str:
    """Normalize text for robust matching"""
    if not s: 
        return ""
    s = s.replace("\u00A0", " ").replace("：", ":")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def levenshtein_score(ocr_text: str, skin_text: str) -> float:
    """Calculate a score based on normalized Levenshtein distance.
    Returns a score between 0.0 and 1.0, where 1.0 = perfect match.
    """
    if not ocr_text or not skin_text:
        return 0.0
    
    # Levenshtein distance
    distance = Levenshtein.distance(ocr_text, skin_text)
    
    # Normalization: score = 1 - (distance / max(len(ocr), len(skin)))
    max_len = max(len(ocr_text), len(skin_text))
    if max_len == 0:
        return 1.0
    
    score = 1.0 - (distance / max_len)
    return max(0.0, score)  # Ensure score is not negative
