#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image processing utilities for OCR
"""

import numpy as np
import cv2
from typing import Tuple


def band_candidates(h: int, centre_pct: Tuple[float, float] = (62.0, 6.5), 
                   span: Tuple[float, float] = (52.0, 70.0), steps: int = 9) -> list:
    """Generate band candidates for text detection"""
    height = max(4.0, min(centre_pct[1], 12.0))
    ts = np.linspace(span[0], span[1] - height, steps)
    return [(float(t), float(t + height)) for t in ts]


def score_white_text(bgr_band: np.ndarray) -> float:
    """Score band for white text content"""
    hsv = cv2.cvtColor(bgr_band, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 0, 200], np.uint8), np.array([179, 70, 255], np.uint8))
    g = cv2.cvtColor(bgr_band, cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 40, 120)
    return 0.6 * (mask > 0).mean() + 0.4 * (e > 0).mean()


def choose_band(frame: np.ndarray) -> Tuple[int, int, int, int]:
    """Choose the best band for text detection"""
    h, w = frame.shape[:2]
    Lpct, Rpct = 28.0, 72.0
    x1 = int(w * (Lpct / 100.0))
    x2 = int(w * (Rpct / 100.0))
    best = (-1.0, 0, 0)
    
    for T, B in band_candidates(h, (62.0, 6.5), (52.0, 70.0), steps=9):
        y1 = int(h * (T / 100.0))
        y2 = int(h * (B / 100.0))
        if y2 - y1 < 24: 
            continue
        sc = score_white_text(frame[y1:y2, x1:x2])
        if sc > best[0]: 
            best = (sc, y1, y2)
    
    y1, y2 = (int(h * 0.58), int(h * 0.66)) if best[0] < 0 else (best[1], best[2])
    return x1, y1, x2, y2


def prep_for_ocr(bgr: np.ndarray) -> np.ndarray:
    """Preprocess image for OCR"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 0, 200], np.uint8), np.array([179, 70, 255], np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    mask = cv2.dilate(mask, np.ones((2, 2), np.uint8), 1)
    inv = 255 - mask
    inv = cv2.medianBlur(inv, 3)
    return inv


def preprocess_band_for_ocr(band_bgr: np.ndarray) -> np.ndarray:
    """Preprocess band for OCR with upscaling if needed"""
    if band_bgr.shape[0] < 120:
        band_bgr = cv2.resize(band_bgr, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    return prep_for_ocr(band_bgr)
