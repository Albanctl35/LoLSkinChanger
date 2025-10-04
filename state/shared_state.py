#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared state for the application
"""

import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SharedState:
    """Shared state between threads"""
    phase: Optional[str] = None
    hovered_champ_id: Optional[int] = None
    locked_champ_id: Optional[int] = None
    last_hovered_skin_key: Optional[str] = None
    last_hovered_skin_id: Optional[int] = None
    last_hovered_skin_slug: Optional[str] = None
    processed_action_ids: set = field(default_factory=set)
    stop: bool = False
    players_visible: int = 0
    locks_by_cell: dict[int, int] = field(default_factory=dict)
    all_locked_announced: bool = False
    local_cell_id: Optional[int] = None
    
    # Loadout timer
    loadout_countdown_active: bool = False
    loadout_t0: float = 0.0
    loadout_left0_ms: int = 0
    last_hover_written: bool = False
    timer_lock: threading.Lock = field(default_factory=threading.Lock)
    ticker_seq: int = 0
    current_ticker: int = 0
    
    # OCR last raw text (exact string to write)
    ocr_last_text: Optional[str] = None
    
    # Skin write config
    skin_write_ms: int = 1500
    skin_file: str = r"C:\Users\alban\Desktop\Skin changer\skin injector\last_hovered_skin.txt"
    inject_batch: Optional[str] = r"C:\Users\alban\Desktop\Skin changer\skin injector\inject_skin.bat"
