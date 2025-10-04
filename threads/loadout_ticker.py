#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loadout countdown ticker thread
"""

import os
import sys
import time
import threading
import subprocess
from typing import Optional
from lcu.client import LCU
from state.shared_state import SharedState
from database.name_db import NameDB
from utils.logging import get_logger
from utils.normalization import normalize_text, levenshtein_score

log = get_logger()


class LoadoutTicker(threading.Thread):
    """High-frequency loadout countdown ticker"""
    
    def __init__(self, lcu: LCU, state: SharedState, hz: int, fallback_ms: int, 
                 ticker_id: int, mode: str = "auto", db: Optional[NameDB] = None):
        super().__init__(daemon=True)
        self.lcu = lcu
        self.state = state
        self.hz = max(10, min(2000, int(hz)))
        self.fallback_ms = max(0, int(fallback_ms))
        self.ticker_id = int(ticker_id)
        self.mode = mode
        self.db = db

    def run(self):
        """Main ticker loop"""
        # Exit immediately if another ticker has taken control
        if getattr(self.state, 'current_ticker', 0) != self.ticker_id:
            return
        
        # Local variables to avoid cross-resets if multiple tickers existed accidentally
        left0_ms = self.state.loadout_left0_ms
        t0 = self.state.loadout_t0
        # Absolute deadline in monotonic time (strict, non-increasing)
        deadline = t0 + (left0_ms / 1000.0)
        prev_remain_ms = 10**9
        poll_period_s = 0.2
        last_poll = 0.0
        last_bucket = None
        
        while (not self.state.stop) and (self.state.phase == "ChampSelect") and self.state.loadout_countdown_active and (self.state.current_ticker == self.ticker_id):
            now = time.monotonic()
            
            # Periodic LCU resync
            if (now - last_poll) >= poll_period_s:
                last_poll = now
                sess = self.lcu.session() or {}
                t = (sess.get("timer") or {})
                phase = str((t.get("phase") or "")).upper()
                left_ms = int(t.get("adjustedTimeLeftInPhase") or 0)
                if phase == "FINALIZATION" and left_ms > 0:
                    cand_deadline = time.monotonic() + (left_ms / 1000.0)
                    if cand_deadline < deadline:
                        deadline = cand_deadline
            
            # Local countdown
            remain_ms = int((deadline - time.monotonic()) * 1000.0)
            if remain_ms < 0:
                remain_ms = 0
            
            # Anti-jitter clamp: never go up
            if remain_ms > prev_remain_ms:
                remain_ms = prev_remain_ms
            prev_remain_ms = remain_ms
            
            bucket = remain_ms // 1000
            if bucket != last_bucket:
                last_bucket = bucket
                log.info(f"[loadout #{self.ticker_id}] T-{int(remain_ms // 1000)}s")
            
            # Write last hovered skin at T<=threshold (configurable)
            thresh = int(getattr(self.state, 'skin_write_ms', 1500) or 1500)
            if remain_ms <= thresh and not self.state.last_hover_written:
                raw = self.state.last_hovered_skin_key or self.state.last_hovered_skin_slug \
                    or (str(self.state.last_hovered_skin_id) if self.state.last_hovered_skin_id else None)
                
                # Build clean label: "<Skin> <Champion>" without duplication or inversion
                final_label = None
                try:
                    champ_id = self.state.locked_champ_id or self.state.hovered_champ_id
                    cname = self.db.champ_name_by_id.get(champ_id or -1, "").strip() if self.db else ""

                    # 1) Base: prefer skin ID (Data Dragon) → ex: "Blood Lord"
                    if self.state.last_hovered_skin_id and self.db and self.state.last_hovered_skin_id in self.db.skin_name_by_id:
                        base = self.db.skin_name_by_id[self.state.last_hovered_skin_id].strip()
                    else:
                        base = (raw or "").strip()

                    # Normalize spaces and apostrophes (NBSP etc.)
                    base_clean = base.replace(" ", " ").replace("'", "'")
                    c_clean = (cname or "").replace(" ", " ").replace("'", "'")

                    # 2) If label starts with champion (ex: "Vladimir Blood Lord"), remove prefix
                    if c_clean and base_clean.lower().startswith(c_clean.lower() + " "):
                        base_clean = base_clean[len(c_clean) + 1:].lstrip()
                    # 3) If label ends with champion (rare), remove suffix
                    elif c_clean and base_clean.lower().endswith(" " + c_clean.lower()):
                        base_clean = base_clean[:-(len(c_clean) + 1)].rstrip()

                    # 4) If champion name is already included in the middle (ex: "K/DA ALL OUT Seraphine Indie"), don't add it
                    nb = normalize_text(base_clean)
                    nc = normalize_text(c_clean)
                    if nc and (nc in nb.split()):
                        final_label = base_clean
                    else:
                        final_label = (base_clean + (" " + c_clean if c_clean else "")).strip()
                except Exception:
                    final_label = raw or ""

                name = final_label if final_label else None
                if not name:
                    try:
                        with open("hover_buffer.txt", "r", encoding="utf-8") as f:
                            s = f.read().strip()
                            if s:
                                name = s
                    except Exception:
                        pass
                
                name = getattr(self.state, 'ocr_last_text', None) or name
                if name:
                    # If OCR text is like "Champion X Champion", normalize to "X Champion"
                    try:
                        champ_id = self.state.locked_champ_id or self.state.hovered_champ_id
                        cname = (self.db.champ_name_by_id.get(champ_id or -1, "") or "").strip() if self.db else ""
                        if cname:
                            low = name.strip()
                            if low.lower().startswith(cname.lower() + " ") and low.lower().endswith(" " + cname.lower()):
                                core = low[len(cname) + 1:-(len(cname) + 1)].strip()
                                if core:
                                    name = f"{core} {cname}".strip()
                    except Exception:
                        pass
                    
                    try:
                        path = getattr(self.state, 'skin_file', "last_hovered_skin.txt")
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(str(self.state.last_hovered_skin_key or name).strip())
                        self.state.last_hover_written = True
                        log.info(f"[loadout #{self.ticker_id}] wrote {path}: {name}")
                        
                        # Launch injection batch (optional) - skip for base skins
                        if self.state.last_hovered_skin_id == 0:
                            log.info(f"[inject] skipping base skin injection (skinId=0)")
                        else:
                            try:
                                batch = (getattr(self.state, 'inject_batch', None) or '').strip()
                                # Normalize target directory of .txt
                                basedir = os.path.abspath(os.path.dirname(path))
                                
                                # If we received a directory, try known names in it
                                candidates = []
                                if batch:
                                    if os.path.isdir(batch):
                                        root = os.path.abspath(batch)
                                        candidates.extend([
                                            os.path.join(root, n) for n in ['run_cslol_tools.bat', 'run_cslol_tools.cmd',
                                                'fast_inject.bat', 'fast_inject.cmd',
                                                'inject_skin.bat', 'inject_last_hovered_skin.bat', 'inject_last_hovered.bat',
                                                'run_injector.bat', 'run_cslol_tools.bat', 'run_cslol_tools.cmd', 'inject.bat']
                                        ])
                                    else:
                                        candidates.append(os.path.abspath(batch))
                                
                                # Always try next to the written file
                                candidates.extend([
                                    os.path.join(basedir, n) for n in [
                                        'fast_inject.bat', 'fast_inject.cmd',
                                        'inject_skin.bat', 'inject_last_hovered_skin.bat', 'inject_last_hovered.bat',
                                        'run_injector.bat', 'run_cslol_tools.bat', 'run_cslol_tools.cmd', 'inject.bat']
                                ])
                                
                                # Deduplicate while preserving order
                                seen = set()
                                ordered = []
                                for c in candidates:
                                    c2 = os.path.normpath(c)
                                    if c2 not in seen:
                                        seen.add(c2)
                                        ordered.append(c2)
                                
                                chosen = None
                                for c in ordered:
                                    if os.path.isfile(c):
                                        chosen = c
                                        break
                                
                                if chosen:
                                    # Use new OCR/Database matching function to find ZIP
                                    try:
                                        base_dir = os.getcwd()
                                        incoming = os.path.join(base_dir, 'incoming_zips')
                                        skin_name = (self.state.last_hovered_skin_key or '').strip()
                                        champ_name = None
                                        champ_slug = getattr(self.state, 'last_hovered_skin_slug', None) or None
                                        cid = getattr(self.state, 'locked_champ_id', None)
                                        
                                        if self.db and cid:
                                            try:
                                                champ_name = self.db.champ_name_by_id.get(cid)
                                            except Exception:
                                                champ_name = None
                                        
                                        # Search in directories by priority order
                                        cand_dirs = []
                                        if champ_name: 
                                            cand_dirs.append(os.path.join(incoming, str(champ_name)))
                                        if champ_slug: 
                                            cand_dirs.append(os.path.join(incoming, str(champ_slug)))
                                        cand_dirs.append(incoming)  # Root directory as last resort
                                        
                                        best_path, best_score = None, 0.0
                                        target_norm = normalize_text(skin_name)
                                        
                                        for d in cand_dirs:
                                            try:
                                                if not os.path.isdir(d):
                                                    continue
                                                for fn in os.listdir(d):
                                                    if not fn.lower().endswith('.zip'):
                                                        continue
                                                    name_no_ext = os.path.splitext(fn)[0]
                                                    score = levenshtein_score(target_norm, normalize_text(name_no_ext))
                                                    
                                                    # Bonus if skin name is contained in filename
                                                    if target_norm and target_norm in normalize_text(name_no_ext):
                                                        score += 0.1
                                                    
                                                    if score > best_score:
                                                        best_score = score
                                                        best_path = os.path.join(d, fn)
                                            except Exception:
                                                continue
                                        
                                        # Confidence threshold to accept match
                                        min_confidence = 0.6
                                        if best_path and best_score >= min_confidence:
                                            # Use Python injector directly - look for it in current directory
                                            injector_path = os.path.join(os.getcwd(), 'cslol_tools_injector.py')
                                            if os.path.isfile(injector_path):
                                                cmd = [sys.executable, '-u', injector_path, '--timeout', '36000', '--zip', best_path]
                                                proc = subprocess.Popen(cmd, cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                                            else:
                                                log.warning(f"[inject] cslol_tools_injector.py not found in {os.getcwd()}")
                                                continue
                                            
                                            def _relay():
                                                try:
                                                    for line in iter(proc.stdout.readline, ''):
                                                        if not line: 
                                                            break
                                                        log.info(line.rstrip())
                                                except Exception:
                                                    pass
                                            
                                            threading.Thread(target=_relay, daemon=True).start()
                                            log.info(f"[inject] found match (score: {best_score:.3f}) → {best_path}")
                                        else:
                                            # Fallback to existing batch if no match found
                                            if chosen and os.path.isfile(chosen):
                                                proc = subprocess.Popen(['cmd.exe', '/c', chosen], cwd=os.path.dirname(chosen) or None, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                                                
                                                def _relay_cslol_logs():
                                                    try:
                                                        for line in iter(proc.stdout.readline, ''):
                                                            if not line: 
                                                                break
                                                            log.info(line.rstrip())
                                                    except Exception:
                                                        pass
                                                
                                                threading.Thread(target=_relay_cslol_logs, daemon=True).start()
                                                log.info(f"[inject] fallback to batch → {chosen}")
                                            else:
                                                log.warning(f"[inject] no suitable ZIP found (best score: {best_score:.3f}) and no batch available")
                                                
                                    except Exception as ie:
                                        log.warning(f"[inject] failed: {ie}")
                            except Exception as ie:
                                log.warning(f"[inject] failed: {ie}")
                    except Exception as e:
                        log.warning(f"[loadout #{self.ticker_id}] write failed: {e}")

            if remain_ms <= 0:
                break
            time.sleep(1.0 / float(self.hz))
        
        # End of ticker: only release if we're still the current ticker
        if getattr(self.state, 'current_ticker', 0) == self.ticker_id:
            self.state.loadout_countdown_active = False
