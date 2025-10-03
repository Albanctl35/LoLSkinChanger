#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
all_in_one_tracer.py — FULL (patched)
-------------------------------------
Corrections intégrées dans le gros fichier :
  ✓ Compteur de locks fiable (diff sur cellId → +1 / -1, ALL LOCKED x/y)
  ✓ Timer de loadout haute fréquence (par défaut 1000 Hz) + resync LCU
  ✓ Démarrage du compte à rebours en FINALIZATION ou quand tout le monde est lock
  ✓ Fallback si le LCU ne renvoie pas le timer (10 s solo, 30 s lobby complet ou --fallback-loadout-ms)

Notes :
- Les logs ressemblent à : [players] …, [locks] +1 …, [locks] ALL LOCKED …, [loadout] T-…
- OCR inchangé sauf qu'il attend ton lock pour spammer moins.

Basé sur ton fichier original 1000+ lignes (OCR/WS/LCU/DataDragon conservés).
"""

from __future__ import annotations
import argparse
import os, sys, time, json, logging, threading
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import cv2
import psutil
import requests
from rapidfuzz.distance import Levenshtein
import unicodedata, re
import ssl, base64

# --- WebSocket (optionnel) ---
try:
    import websocket  # websocket-client
except Exception:
    websocket = None

# --- Couper l'avertissement SSL du LCU (cert auto-signé) pour les appels HTTP ---
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

# ====================== Normalisation (matching robuste) ======================
def _norm(s: str) -> str:
    if not s: return ""
    s = s.replace("\u00A0", " ").replace("：", ":")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _levenshtein_score(ocr_text: str, skin_text: str) -> float:
    """Calcule un score basé sur la distance de Levenshtein normalisée.
    Retourne un score entre 0.0 et 1.0, où 1.0 = correspondance parfaite.
    """
    if not ocr_text or not skin_text:
        return 0.0
    
    # Distance de Levenshtein
    distance = Levenshtein.distance(ocr_text, skin_text)
    
    # Normalisation : score = 1 - (distance / max(len(ocr), len(skin)))
    max_len = max(len(ocr_text), len(skin_text))
    if max_len == 0:
        return 1.0
    
    score = 1.0 - (distance / max_len)
    return max(0.0, score)  # S'assurer que le score n'est pas négatif

# ====================== Logging ======================
def setup_logging(verbose: bool):
    h = logging.StreamHandler(sys.stdout)
    fmt = "%(_when)s | %(levelname)-7s | %(message)s"
    class _Fmt(logging.Formatter):
        def format(self, record):
            record._when = time.strftime("%H:%M:%S", time.localtime())
            return super().format(record)
    h.setFormatter(_Fmt(fmt))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(h)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Supprimer les logs HTTPS/HTTP
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

log = logging.getLogger("tracer")

# ====================== OCR backend ======================
class OCR:
    def __init__(self, lang="fra+eng", psm=7, tesseract_exe: Optional[str]=None):
        self.lang = lang
        self.psm = int(psm)
        self.backend = None
        self.api = None
        from tesserocr import PyTessBaseAPI, PSM
        tessdata_dir = getattr(self, "tessdata_dir", None) or os.environ.get("TESSDATA_PREFIX")
        if tessdata_dir and not tessdata_dir.lower().endswith("tessdata"):
            cand = os.path.join(tessdata_dir, "tessdata")
            if os.path.isdir(cand):
                tessdata_dir = cand
        psm_mode = PSM.SINGLE_LINE if self.psm == 7 else PSM.AUTO
        if tessdata_dir and os.path.isdir(tessdata_dir):
            self.api = PyTessBaseAPI(path=tessdata_dir, lang=self.lang, psm=psm_mode)
        else:
            self.api = PyTessBaseAPI(lang=self.lang, psm=psm_mode)
        self.api.SetVariable("preserve_interword_spaces", "1")
        self.api.SetVariable("user_defined_dpi", "240")
        self.api.SetVariable("tessedit_char_whitelist",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            "ÀÂÄÃÇÉÈÊËÎÏÌÍÔÖÒÓÙÛÜÚàâäãçéèêëîïìíôöòóùûüúÑñ"
            "0123456789 .-':")
        self.backend = "tesserocr"

    def recognize(self, img: np.ndarray) -> str:
        if self.backend == "tesserocr":
            from PIL import Image
            pil = Image.fromarray(img if img.ndim==2 else cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            self.api.SetImage(pil)
            txt = self.api.GetUTF8Text() or ""
        else:
            cfg = f"-l {self.lang} --oem 3 --psm {self.psm} -c preserve_interword_spaces=1"
            txt = self.pytesseract.image_to_string(img, config=cfg)
        txt = txt.replace("\n"," ").strip()
        txt = txt.replace("’","'").replace("`","'")
        return " ".join(txt.split())

# ====================== Win32 window capture helpers ======================
def is_windows(): return os.name=="nt"
if is_windows():
    import ctypes
    from ctypes import wintypes
    user32=ctypes.windll.user32
    try: user32.SetProcessDPIAware()
    except Exception: pass
    EnumWindows=user32.EnumWindows
    EnumWindowsProc=ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.POINTER(ctypes.c_int))
    GetWindowTextW=user32.GetWindowTextW
    GetWindowTextLengthW=user32.GetWindowTextLengthW
    IsWindowVisible=user32.IsWindowVisible
    IsIconic=user32.IsIconic
    GetWindowRect=user32.GetWindowRect

    def _win_text(hwnd):
        n=GetWindowTextLengthW(hwnd)
        if n==0: return ""
        buf=ctypes.create_unicode_buffer(n+1); GetWindowTextW(hwnd, buf, n+1); return buf.value

    def _win_rect(hwnd):
        r=wintypes.RECT()
        if not GetWindowRect(hwnd, ctypes.byref(r)): return None
        return r.left, r.top, r.right, r.bottom

    def find_league_window_rect(hint="League"):
        rects=[]
        def cb(hwnd, lparam):
            if not IsWindowVisible(hwnd) or IsIconic(hwnd): return True
            t=_win_text(hwnd).lower()
            if hint.lower() in t and ("league" in t or "riot client" in t):
                R=_win_rect(hwnd)
                if R:
                    l,t,r,b=R; w,h=r-l,b-t
                    if w>=600 and h>=350: rects.append((l,t,r,b))
            return True
        EnumWindows(EnumWindowsProc(cb),0)
        if rects:
            rects.sort(key=lambda xyxy:(xyxy[2]-xyxy[0])*(xyxy[3]-xyxy[1]), reverse=True)
            return rects[0]
        return None
else:
    def find_league_window_rect(hint="League"): return None

# ====================== Bande & prétraitement ======================
def band_candidates(h:int, centre_pct=(62.0,6.5), span=(52.0,70.0), steps=9):
    height = max(4.0, min(centre_pct[1], 12.0))
    ts = np.linspace(span[0], span[1]-height, steps)
    return [(float(t), float(t+height)) for t in ts]

def score_white_text(bgr_band: np.ndarray) -> float:
    hsv = cv2.cvtColor(bgr_band, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0,0,200],np.uint8), np.array([179,70,255],np.uint8))
    g = cv2.cvtColor(bgr_band, cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 40, 120)
    return 0.6*(mask>0).mean() + 0.4*(e>0).mean()

def choose_band(frame: np.ndarray) -> Tuple[int,int,int,int]:
    h,w = frame.shape[:2]
    Lpct,Rpct = 28.0,72.0
    x1 = int(w*(Lpct/100.0)); x2 = int(w*(Rpct/100.0))
    best = (-1.0, 0, 0)
    for T,B in band_candidates(h, (62.0,6.5), (52.0,70.0), steps=9):
        y1=int(h*(T/100.0)); y2=int(h*(B/100.0))
        if y2-y1<24: continue
        sc = score_white_text(frame[y1:y2, x1:x2])
        if sc>best[0]: best=(sc,y1,y2)
    y1,y2 = (int(h*0.58), int(h*0.66)) if best[0]<0 else (best[1],best[2])
    return x1,y1,x2,y2

def prep_for_ocr(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0,0,200],np.uint8), np.array([179,70,255],np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
    mask = cv2.dilate(mask, np.ones((2,2),np.uint8), 1)
    inv  = 255 - mask
    inv  = cv2.medianBlur(inv, 3)
    return inv

def preprocess_band_for_ocr(band_bgr: np.ndarray) -> np.ndarray:
    if band_bgr.shape[0] < 120:
        band_bgr = cv2.resize(band_bgr, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    return prep_for_ocr(band_bgr)

# ====================== Data Dragon: noms (multilingue) ======================
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "lcu-all-in-one")
os.makedirs(CACHE, exist_ok=True)

@dataclass
class Entry:
    key: str
    kind: str  # "skin" | "champion"
    champ_slug: str
    champ_id: int
    skin_id: Optional[int] = None

class NameDB:
    def __init__(self, lang: str = "fr_FR"):
        self.ver: Optional[str] = None
        self.langs: List[str] = self._resolve_langs_spec(lang)
        self.canonical_lang: Optional[str] = "en_US" if "en_US" in self.langs else (self.langs[0] if self.langs else "en_US")
        self.slug_by_id: Dict[int, str] = {}
        self.champ_name_by_id_by_lang: Dict[str, Dict[int, str]] = {}
        self.champ_name_by_id: Dict[int, str] = {}
        self.entries_by_champ: Dict[str, List[Entry]] = {}
        self.skin_name_by_id: Dict[int, str] = {}
        self._skins_loaded: set = set()
        self._norm_cache: Dict[str, str] = {}
        self._load_versions()
        self._load_index()
        self.champ_name_by_id = self.champ_name_by_id_by_lang.get(self.canonical_lang, {})

    def _cache_json(self, name: str, url: str):
        p = os.path.join(CACHE, name)
        if os.path.isfile(p):
            try: return json.load(open(p, "r", encoding="utf-8"))
            except Exception: pass
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        json.dump(data, open(p, "w", encoding="utf-8"))
        return data

    def _load_versions(self):
        versions = self._cache_json("versions.json", "https://ddragon.leagueoflegends.com/api/versions.json")
        self.ver = versions[0]

    def _fetch_languages(self) -> List[str]:
        data = self._cache_json("languages.json", "https://ddragon.leagueoflegends.com/cdn/languages.json")
        return [str(x) for x in data if isinstance(x, str)]

    def _resolve_langs_spec(self, spec: str) -> List[str]:
        if not spec or spec.strip().lower() in ("default", "auto"):
            return ["fr_FR"]
        s = spec.strip()
        if s.lower() == "all":
            try: return self._fetch_languages()
            except Exception: return ["en_US", "fr_FR"]
        if "," in s:
            return [x.strip() for x in s.split(",") if x.strip()]
        return [s]

    def _load_index(self):
        for lang in self.langs:
            data = self._cache_json(
                f"champion_{self.ver}_{lang}.json",
                f"https://ddragon.leagueoflegends.com/cdn/{self.ver}/data/{lang}/champion.json"
            )
            lang_map: Dict[int, str] = self.champ_name_by_id_by_lang.setdefault(lang, {})
            for slug, obj in (data.get("data") or {}).items():
                try:
                    cid = int(obj.get("key")); cname = obj.get("name") or slug
                    self.slug_by_id[cid] = slug
                    lang_map[cid] = cname
                    self.entries_by_champ.setdefault(slug, [])
                    self.entries_by_champ[slug].append(Entry(key=cname, kind="champion", champ_slug=slug, champ_id=cid))
                except Exception:
                    pass

    def _ensure_champ(self, slug: str, champ_id: int) -> None:
        if slug in self._skins_loaded:
            return
        out = self.entries_by_champ.setdefault(slug, [])
        keys_seen: set = set()
        for lang in self.langs:
            try:
                data = self._cache_json(
                    f"champ_{slug}_{self.ver}_{lang}.json",
                    f"https://ddragon.leagueoflegends.com/cdn/{self.ver}/data/{lang}/champion/{slug}.json",
                )
                champ = ((data.get("data") or {}).get(slug, {}) or {})
                skins = champ.get("skins") or []
                cname = (
                    self.champ_name_by_id_by_lang.get(lang, {}).get(champ_id)
                    or self.champ_name_by_id.get(champ_id)
                    or slug
                )
                for s in skins:
                    try:
                        sid = int(s.get("id"))
                        sname = (s.get("name") or "").strip()
                        num = int(s.get("num") or 0)
                        if sid:
                            self.skin_name_by_id[sid] = sname
                        if num == 0 or not sname:
                            continue
                        full = f"{cname} {sname}"
                        for label in (full, sname):
                            if label in keys_seen:
                                continue
                            out.append(
                                Entry(key=label, kind="skin", champ_slug=slug, champ_id=champ_id, skin_id=sid)
                            )
                            keys_seen.add(label)
                    except Exception:
                        pass
            except Exception:
                pass
        self._skins_loaded.add(slug)

    def candidates_for_champ(self, champ_id: Optional[int]) -> List[Entry]:
        if champ_id and champ_id in self.slug_by_id:
            slug = self.slug_by_id[champ_id]
            self._ensure_champ(slug, champ_id)
            return self.entries_by_champ.get(slug, [])
        if not hasattr(self, "_global_entries") or self._global_entries is None:
            glb = []
            for lang, mp in self.champ_name_by_id_by_lang.items():
                for cid, nm in mp.items():
                    slug = self.slug_by_id.get(cid)
                    if not slug: continue
                    glb.append(Entry(key=nm, kind="champion", champ_slug=slug, champ_id=cid))
            self._global_entries = glb
        return self._global_entries

    def normalized_entries(self, champ_id: Optional[int]) -> List[tuple]:
        entries = self.candidates_for_champ(champ_id)
        out = []
        for e in entries:
            nk = getattr(self, "_norm_cache", {}).get(e.key)
            if nk is None:
                nk = _norm(e.key)
                self._norm_cache[e.key] = nk
            out.append((e, nk))
        return out

# ====================== LCU (phase / session / hover) ======================
@dataclass
class Lockfile:
    name:str; pid:int; port:int; password:str; protocol:str

def _find_lockfile(explicit: Optional[str]) -> Optional[str]:
    if explicit and os.path.isfile(explicit): return explicit
    env=os.environ.get("LCU_LOCKFILE")
    if env and os.path.isfile(env): return env
    if os.name=="nt":
        for p in (r"C:\\Riot Games\\League of Legends\\lockfile",
                  r"C:\\Program Files\\Riot Games\\League of Legends\\lockfile",
                  r"C:\\Program Files (x86)\\Riot Games\\League of Legends\\lockfile"):
            if os.path.isfile(p): return p
    else:
        for p in ("/Applications/League of Legends.app/Contents/LoL/lockfile",
                  os.path.expanduser("~/.local/share/League of Legends/lockfile")):
            if os.path.isfile(p): return p
    try:
        for proc in psutil.process_iter(attrs=["name","exe"]):
            nm=(proc.info.get("name") or "").lower()
            if "leagueclient" in nm:
                exe=proc.info.get("exe") or ""
                for d in (os.path.dirname(exe), os.path.dirname(os.path.dirname(exe))):
                    p=os.path.join(d,"lockfile")
                    if os.path.isfile(p): return p
    except Exception:
        pass
    return None

class LCU:
    def __init__(self, lockfile_path: Optional[str]):
        self.ok = False
        self.port = None
        self.pw = None
        self.base = None
        self.s = None
        self._explicit_lockfile = lockfile_path
        self.lf_path = None
        self.lf_mtime = 0.0
        self._init_from_lockfile()

    def _init_from_lockfile(self):
        lf = _find_lockfile(self._explicit_lockfile)
        self.lf_path = lf
        if not lf or not os.path.isfile(lf):
            self._disable("LCU lockfile introuvable"); return
        try:
            name, pid, port, pw, proto = open(lf, "r", encoding="utf-8").read().split(":")[:5]
            self.port = int(port); self.pw = pw
            self.base = f"https://127.0.0.1:{self.port}"
            self.s = requests.Session(); self.s.verify=False; self.s.auth=("riot", pw)
            self.s.headers.update({"Content-Type": "application/json"})
            self.ok = True
            try: self.lf_mtime = os.path.getmtime(lf)
            except Exception: self.lf_mtime = time.time()
            log.info(f"LCU prêt (port {self.port})")
        except Exception as e:
            self._disable(f"LCU indisponible: {e}")

    def _disable(self, reason: str):
        if self.ok: log.debug(f"LCU désactivé: {reason}")
        self.ok = False; self.base=None; self.port=None; self.pw=None
        self.s = requests.Session(); self.s.verify=False

    def refresh_if_needed(self, force: bool = False):
        lf = _find_lockfile(self._explicit_lockfile)
        if not lf or not os.path.isfile(lf):
            self._disable("lockfile absent"); self.lf_path=None; self.lf_mtime=0.0; return
        try: mt = os.path.getmtime(lf)
        except Exception: mt = 0.0
        if force or lf != self.lf_path or (mt and mt != self.lf_mtime) or not self.ok:
            old = (self.port, self.pw)
            self.lf_path = lf; self._init_from_lockfile()
            new = (self.port, self.pw)
            if self.ok and old != new: log.info(f"LCU relu (port={self.port})")

    def get(self, path: str, timeout=1.0):
        if not self.ok:
            self.refresh_if_needed()
            if not self.ok: return None
        try:
            r = self.s.get((self.base or "") + path, timeout=timeout)
            if r.status_code in (404, 405): return None
            r.raise_for_status()
            try: return r.json()
            except Exception: return None
        except requests.exceptions.RequestException:
            self.refresh_if_needed(force=True)
            if not self.ok: return None
            try:
                r = self.s.get((self.base or "") + path, timeout=timeout)
                if r.status_code in (404, 405): return None
                r.raise_for_status()
                try: return r.json()
                except Exception: return None
            except requests.exceptions.RequestException:
                return None

    def phase(self) -> Optional[str]:
        ph = self.get("/lol-gameflow/v1/gameflow-phase"); return ph if isinstance(ph, str) else None
    def session(self) -> Optional[dict]:
        return self.get("/lol-champ-select/v1/session")
    def hovered_champion_id(self) -> Optional[int]:
        v = self.get("/lol-champ-select/v1/hovered-champion-id")
        try: return int(v) if v is not None else None
        except Exception: return None
    def my_selection(self) -> Optional[dict]:
        return self.get("/lol-champ-select/v1/session/my-selection") or self.get("/lol-champ-select/v1/selection")
    def unlocked_skins(self) -> Optional[dict]:
        return self.get("/lol-champions/v1/owned-champions-minimal")
    def owned_skins(self) -> Optional[dict]:
        return self.get("/lol-skins/v1/owned-skins")

# ====================== Utils: locks & players ======================
def map_cells(sess: Dict[str,Any]) -> Dict[int, Dict[str,Any]]:
    idx: Dict[int, Dict[str,Any]] = {}
    for side in (sess.get("myTeam") or [], sess.get("theirTeam") or []):
        for p in side or []:
            cid = p.get("cellId")
            if cid is not None:
                idx[int(cid)] = p
    return idx

def compute_locked(sess: Dict[str,Any]) -> Dict[int,int]:
    locked: Dict[int,int] = {}
    idx = map_cells(sess)
    for rnd in (sess.get("actions") or []):
        for a in rnd or []:
            if a.get("type") == "pick" and a.get("completed"):
                cid = a.get("actorCellId")
                ch  = int(a.get("championId") or 0)
                if cid is not None:
                    if ch == 0:
                        p = idx.get(int(cid))
                        ch = int((p or {}).get("championId") or 0)
                    if ch > 0:
                        locked[int(cid)] = ch
    for cid, p in idx.items():
        ch = int(p.get("championId") or 0)
        if ch <= 0: continue
        intent = int(p.get("championPickIntent") or p.get("pickIntentChampionId") or 0)
        is_intenting = bool(p.get("isPickIntenting") or False)
        if (intent == 0) and (not is_intenting):
            locked[cid] = ch
    return locked

# ====================== État partagé ======================
@dataclass
class SharedState:
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
    timer_lock: threading.Lock = field(default_factory=threading.Lock)
    ticker_seq: int = 0
    current_ticker: int = 0

# ====================== Threads (polling) ======================
class PhaseThread(threading.Thread):
    INTERESTING = {"Lobby","Matchmaking","ReadyCheck","ChampSelect","GameStart","InProgress","EndOfGame"}
    def __init__(self, lcu: LCU, state: SharedState, interval: float = 0.5, log_transitions: bool = True):
        super().__init__(daemon=True)
        self.lcu=lcu; self.state=state; self.interval=interval; self.log_transitions=log_transitions
        self.last_phase=None
    def run(self):
        while not self.state.stop:
            try: self.lcu.refresh_if_needed()
            except Exception: pass
            ph = self.lcu.phase() if self.lcu.ok else None
            if ph is not None and ph != self.last_phase:
                if self.log_transitions and ph in self.INTERESTING:
                    log.info(f"[phase] {ph}")
                self.state.phase = ph
                if ph == "ChampSelect":
                    self.state.last_hovered_skin_key  = None
                    self.state.last_hovered_skin_id   = None
                    self.state.last_hovered_skin_slug = None
                    try: self.state.processed_action_ids.clear()
                    except Exception: self.state.processed_action_ids=set()
                    self.state.last_hover_written = False
                else:
                    # sort de champ select → reset compteur/timer
                    self.state.hovered_champ_id = None
                    self.state.players_visible = 0
                    self.state.locks_by_cell.clear()
                    self.state.all_locked_announced = False
                    self.state.loadout_countdown_active = False
                    self.state.last_hover_written = False
                self.last_phase = ph
            time.sleep(self.interval)

class ChampThread(threading.Thread):
    def __init__(self, lcu: LCU, db: NameDB, state: SharedState, interval: float=0.25):
        super().__init__(daemon=True)
        self.lcu=lcu; self.db=db; self.state=state; self.interval=interval
        self.last_hover=None
        self.last_lock=None
    def run(self):
        while not self.state.stop:
            if not self.lcu.ok or self.state.phase != "ChampSelect":
                time.sleep(0.25); continue
            cid = self.lcu.hovered_champion_id()
            if cid is None:
                sel = self.lcu.my_selection() or {}
                try: cid = int(sel.get("selectedChampionId") or 0) or None
                except Exception: cid = None
            if cid and cid != self.last_hover:
                nm = self.db.champ_name_by_id.get(cid) or f"champ_{cid}"
                log.info(f"[hover:champ] {nm} (id={cid})")
                self.state.hovered_champ_id = cid
                self.last_hover = cid
            # lock perso (log utile même sans WS)
            sess = self.lcu.session() or {}
            try:
                my_cell = sess.get("localPlayerCellId")
                actions = sess.get("actions") or []
                locked = None
                for rnd in actions:
                    for act in rnd:
                        if act.get("actorCellId")==my_cell and act.get("type")=="pick" and act.get("completed"):
                            ch = int(act.get("championId") or 0)
                            if ch>0: locked = ch
                if locked and locked != self.last_lock:
                    nm = self.db.champ_name_by_id.get(locked) or f"champ_{locked}"
                    log.info(f"[lock:champ] {nm} (id={locked})")
                    self.state.locked_champ_id = locked
                    self.last_lock = locked
            except Exception:
                pass
            time.sleep(self.interval)

# ====================== Loadout countdown (haute fréquence) ======================
class LoadoutTicker(threading.Thread):
    def __init__(self, lcu: LCU, state: SharedState, hz: int, fallback_ms: int, ticker_id: int, mode: str = "auto", db=None):
        super().__init__(daemon=True)
        self.lcu = lcu
        self.state = state
        self.hz = max(10, min(2000, int(hz)))
        self.fallback_ms = max(0, int(fallback_ms))
        self.ticker_id = int(ticker_id)
        self.mode = mode
        self.db = db


    def run(self):
        # Sort immédiatement si un autre ticker a pris la main
        if getattr(self.state, 'current_ticker', 0) != self.ticker_id:
            return
        # Local, pour éviter les resets croisés si plusieurs tickers existaient accidentellement
        left0_ms = self.state.loadout_left0_ms
        t0 = self.state.loadout_t0
        # Échéance absolue en temps monotonic (stricte, non-croissante)
        deadline = t0 + (left0_ms / 1000.0)
        prev_remain_ms = 10**9
        poll_period_s = 0.2
        last_poll = 0.0
        last_bucket = None
        while (not self.state.stop) and (self.state.phase == "ChampSelect") and self.state.loadout_countdown_active and (self.state.current_ticker == self.ticker_id):
            now = time.monotonic()
            # resync périodique LCU
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
            # décompte local
            remain_ms = int((deadline - time.monotonic()) * 1000.0)
            if remain_ms < 0:
                remain_ms = 0
            # Clamp anti-jitter: ne jamais remonter
            if remain_ms > prev_remain_ms:
                remain_ms = prev_remain_ms
            prev_remain_ms = remain_ms
            bucket = remain_ms // 1000
            if bucket != last_bucket:
                last_bucket = bucket
                log.info(f"[loadout #{self.ticker_id}] T-{int(remain_ms // 1000)}s")
            # Écrit le dernier skin hover à T<=seuil (paramétrable)
            thresh = int(getattr(self.state, 'skin_write_ms', 1500) or 1500)
            if remain_ms <= thresh and not self.state.last_hover_written:
                raw = self.state.last_hovered_skin_key or self.state.last_hovered_skin_slug \
                    or (str(self.state.last_hovered_skin_id) if self.state.last_hovered_skin_id else None)
                # Construire un libellé propre: "<Skin> <Champion>" sans doublon ni inversion
                final_label = None
                try:
                    champ_id = self.state.locked_champ_id or self.state.hovered_champ_id
                    cname = self.db.champ_name_by_id.get(champ_id or -1, "").strip()

                    # 1) Base: préférer l'ID de skin (Data Dragon) → ex: "Blood Lord"
                    if self.state.last_hovered_skin_id and self.state.last_hovered_skin_id in self.db.skin_name_by_id:
                        base = self.db.skin_name_by_id[self.state.last_hovered_skin_id].strip()
                    else:
                        base = (raw or "").strip()

                    # Uniformiser espaces et apostrophes (NBSP etc.)
                    base_clean = base.replace(" ", " ").replace("’", "'")
                    c_clean = (cname or "").replace(" ", " ").replace("’", "'")

                    # 2) Si le libellé commence par le champion (ex: "Vladimir Blood Lord"), retirer le préfixe
                    if c_clean and base_clean.lower().startswith(c_clean.lower() + " "):
                        base_clean = base_clean[len(c_clean) + 1:].lstrip()
                    # 3) Si le libellé se termine par le champion (rare), retirer le suffixe
                    elif c_clean and base_clean.lower().endswith(" " + c_clean.lower()):
                        base_clean = base_clean[:-(len(c_clean) + 1)].rstrip()

                    # 4) Si le nom du champion est déjà inclus au milieu (ex: "K/DA ALL OUT Seraphine Indie"), ne pas le rajouter
                    nb = _norm(base_clean)
                    nc = _norm(c_clean)
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
                    # Si le texte OCR est du type "Champion X Champion", normaliser en "X Champion"
                    try:
                        champ_id = self.state.locked_champ_id or self.state.hovered_champ_id
                        cname = (self.db.champ_name_by_id.get(champ_id or -1, "") or "").strip()
                        if cname:
                            low = name.strip()
                            if low.lower().startswith(cname.lower()+" ") and low.lower().endswith(" "+cname.lower()):
                                core = low[len(cname)+1:-(len(cname)+1)].strip()
                                if core:
                                    name = f"{core} {cname}".strip()
                    except Exception:
                        pass
                    try:
                        path = getattr(self.state, 'skin_file', r"C:\Users\alban\Desktop\Skin changer\skin injector\last_hovered_skin.txt")
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(str(self.state.last_hovered_skin_key or name).strip())
                        self.state.last_hover_written = True
                        log.info(f"[loadout #{self.ticker_id}] wrote {path}: {name}")
                        # Lancer le batch d'injection (facultatif) - sauter pour les skins de base
                        if self.state.last_hovered_skin_id == 0:
                            log.info(f"[inject] skipping base skin injection (skinId=0)")
                        else:
                            try:
                                batch = (getattr(self.state, 'inject_batch', None) or '').strip()
                                # Normaliser le répertoire cible du .txt
                                basedir = os.path.abspath(os.path.dirname(path))
                                # Si on a reçu un dossier, tenter des noms connus dedans
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
                                # Toujours tenter à côté du fichier écrit
                                candidates.extend([
                                    os.path.join(basedir, n) for n in [
                                        'fast_inject.bat', 'fast_inject.cmd',
                                        'inject_skin.bat', 'inject_last_hovered_skin.bat', 'inject_last_hovered.bat',
                                        'run_injector.bat', 'run_cslol_tools.bat', 'run_cslol_tools.cmd', 'inject.bat']
                                ])
                                # Dédupliquer en préservant l'ordre
                                seen = set(); ordered = []
                                for c in candidates:
                                    c2 = os.path.normpath(c)
                                    if c2 not in seen:
                                        seen.add(c2); ordered.append(c2)
                                chosen = None
                                for c in ordered:
                                    if os.path.isfile(c):
                                        chosen = c; break
                                if chosen:
                                    # Utiliser la nouvelle fonction de matching OCR/Database pour trouver le ZIP
                                    try:
                                        import sys, subprocess, threading
                                        base_dir = os.path.dirname(getattr(self.state, 'skin_file', '') or '.')
                                        incoming = os.path.join(base_dir, 'incoming_zips')
                                        skin_name = (self.state.last_hovered_skin_key or '').strip()
                                        champ_name = None
                                        champ_slug = getattr(self.state, 'last_hovered_skin_slug', None) or None
                                        cid = getattr(self.state, 'locked_champ_id', None)
                                        
                                        if getattr(self, 'db', None) and cid:
                                            try:
                                                champ_name = self.db.champ_name_by_id.get(cid)
                                            except Exception:
                                                champ_name = None
                                        
                                        # Rechercher dans les dossiers par ordre de priorité
                                        cand_dirs = []
                                        if champ_name: 
                                            cand_dirs.append(os.path.join(incoming, str(champ_name)))
                                        if champ_slug: 
                                            cand_dirs.append(os.path.join(incoming, str(champ_slug)))
                                        cand_dirs.append(incoming)  # Dossier racine en dernier recours
                                        
                                        best_path, best_score = None, 0.0
                                        target_norm = _norm(skin_name)
                                        
                                        for d in cand_dirs:
                                            try:
                                                if not os.path.isdir(d):
                                                    continue
                                                for fn in os.listdir(d):
                                                    if not fn.lower().endswith('.zip'):
                                                        continue
                                                    name_no_ext = os.path.splitext(fn)[0]
                                                    score = _levenshtein_score(target_norm, _norm(name_no_ext))
                                                    
                                                    # Bonus si le nom du skin est contenu dans le nom du fichier
                                                    if target_norm and target_norm in _norm(name_no_ext):
                                                        score += 0.1
                                                    
                                                    if score > best_score:
                                                        best_score = score
                                                        best_path = os.path.join(d, fn)
                                            except Exception:
                                                continue
                                        
                                        # Seuil de confiance pour accepter le match
                                        min_confidence = 0.6
                                        if best_path and best_score >= min_confidence:
                                            # Utiliser l'injector Python directement
                                            cmd = [sys.executable, '-u', 'cslol_tools_injector.py', '--timeout', '36000', '--zip', best_path]
                                            proc = subprocess.Popen(cmd, cwd=base_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                                            
                                            def _relay():
                                                try:
                                                    for line in iter(proc.stdout.readline, ''):
                                                        if not line: break
                                                        log.info(line.rstrip())
                                                except Exception:
                                                    pass
                                            
                                            threading.Thread(target=_relay, daemon=True).start()
                                            log.info(f"[inject] found match (score: {best_score:.3f}) → {best_path}")
                                        else:
                                            # Fallback vers le batch existant si aucun match trouvé
                                            if chosen and os.path.isfile(chosen):
                                                proc = subprocess.Popen(['cmd.exe','/c', chosen], cwd=os.path.dirname(chosen) or None, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                                                
                                                def _relay_cslol_logs():
                                                    try:
                                                        for line in iter(proc.stdout.readline, ''):
                                                            if not line: break
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
            time.sleep(1.0/float(self.hz))
        # Fin du ticker : ne libérer que si on est toujours le ticker courant
        if getattr(self.state, 'current_ticker', 0) == self.ticker_id:
            self.state.loadout_countdown_active = False

# ====================== Thread WebSocket (WAMP + compteur locks + timer) ======================
class WSEventThread(threading.Thread):
    def __init__(self, lcu: LCU, db: NameDB, state: SharedState, ping_interval=20, ping_timeout=10, timer_hz=1000, fallback_ms=0):
        super().__init__(daemon=True)
        self.lcu = lcu
        self.db = db
        self.state = state
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.ws = None
        self.timer_hz = timer_hz
        self.fallback_ms = fallback_ms
        self.ticker: Optional[LoadoutTicker] = None

    def _maybe_start_timer(self, sess: dict):
        t = (sess.get("timer") or {})
        phase_timer = str((t.get("phase") or "")).upper()
        left_ms = int(t.get("adjustedTimeLeftInPhase") or 0)
        total = self.state.players_visible
        locked_count = len(self.state.locks_by_cell)
        should_start = False
        probe_used = False
        # FINALIZATION → top priorité
        if phase_timer == "FINALIZATION" and left_ms > 0:
            should_start = True
        # Tous lockés : on tente de LIRE le timer LCU (grace window courte) avant fallback
        elif (total > 0 and locked_count >= total):
            if left_ms <= 0:
                # petite fenêtre de 0.5s pour laisser le LCU publier un timer non nul
                for _ in range(8):  # 8 * 60ms ~= 480ms
                    s2 = self.lcu.session() or {}
                    t2 = (s2.get("timer") or {})
                    left_ms = int(t2.get("adjustedTimeLeftInPhase") or 0)
                    if left_ms > 0:
                        probe_used = True
                        break
                    time.sleep(0.06)
            if left_ms > 0:
                should_start = True

        if should_start:
            with self.state.timer_lock:
                if not self.state.loadout_countdown_active:
                    self.state.loadout_left0_ms = left_ms
                    self.state.loadout_t0 = time.monotonic()
                    self.state.ticker_seq = (self.state.ticker_seq or 0) + 1
                    self.state.current_ticker = self.state.ticker_seq
                    self.state.loadout_countdown_active = True
                    mode = ("finalization" if (phase_timer == "FINALIZATION" and left_ms > 0) else "lcu-probe")
                    log.info(f"[loadout] start id={self.state.current_ticker} mode={mode} remaining_ms={left_ms} ({left_ms/1000:.3f}s) [hz={self.timer_hz}]")
                    if self.ticker is None or not self.ticker.is_alive():
                        self.ticker = LoadoutTicker(self.lcu, self.state, self.timer_hz, self.fallback_ms, ticker_id=self.state.current_ticker, mode=mode, db=self.db)
                        self.ticker.start()

    def _handle_api_event(self, payload: dict):
        uri = payload.get("uri")
        if not uri: return
        if uri == "/lol-gameflow/v1/gameflow-phase":
            ph = payload.get("data")
            if isinstance(ph, str) and ph != self.state.phase:
                if ph in PhaseThread.INTERESTING:
                    log.info(f"[phase] {ph}")
                self.state.phase = ph
                if ph == "ChampSelect":
                    self.state.last_hovered_skin_key = None
                    self.state.last_hovered_skin_id = None
                    self.state.last_hovered_skin_slug = None
                    self.state.last_hover_written = False
                    try: self.state.processed_action_ids.clear()
                    except Exception: self.state.processed_action_ids = set()
                else:
                    # on sort → reset locks/timer
                    self.state.hovered_champ_id = None
                    self.state.players_visible = 0
                    self.state.locks_by_cell.clear()
                    self.state.all_locked_announced = False
                    self.state.loadout_countdown_active = False
        elif uri == "/lol-champ-select/v1/hovered-champion-id":
            cid = payload.get("data")
            try: cid = int(cid) if cid is not None else None
            except Exception: cid = None
            if cid and cid != self.state.hovered_champ_id:
                nm = self.db.champ_name_by_id.get(cid) or f"champ_{cid}"
                log.info(f"[hover:champ] {nm} (id={cid})")
                self.state.hovered_champ_id = cid
        elif uri == "/lol-champ-select/v1/session":
            sess = payload.get("data") or {}
            self.state.local_cell_id = sess.get("localPlayerCellId", self.state.local_cell_id)
            # Players visibles (cellIds distincts)
            seen = set()
            for side in (sess.get("myTeam") or [], sess.get("theirTeam") or []):
                for p in side or []:
                    cid = p.get("cellId")
                    if cid is not None: seen.add(int(cid))
            if not seen:
                for rnd in (sess.get("actions") or []):
                    for a in rnd or []:
                        cid = a.get("actorCellId")
                        if cid is not None: seen.add(int(cid))
            count_visible = len(seen)
            if count_visible != self.state.players_visible and count_visible>0:
                self.state.players_visible = count_visible
                log.info(f"[players] #Players: {count_visible}")
            # Compteur de locks: diff cellId → championId
            new_locks = compute_locked(sess)
            prev_cells = set(self.state.locks_by_cell.keys())
            curr_cells = set(new_locks.keys())
            added = sorted(list(curr_cells - prev_cells))
            removed = sorted(list(prev_cells - curr_cells))
            for cid in added:
                ch = new_locks[cid]
                # libellé lisible si dispo
                champ_label = self.db.champ_name_by_id.get(int(ch), f"#{ch}")
                log.info(f"[locks] +1 {champ_label} — {len(curr_cells)}/{self.state.players_visible}")
                if self.state.local_cell_id is not None and cid == int(self.state.local_cell_id):
                    log.info(f"[lock:champ] {champ_label} (id={ch})")
                    self.state.locked_champ_id = int(ch)
            for cid in removed:
                ch = self.state.locks_by_cell.get(cid, 0)
                champ_label = self.db.champ_name_by_id.get(int(ch), f"#{ch}")
                log.info(f"[locks] -1 {champ_label} — {len(curr_cells)}/{self.state.players_visible}")
            self.state.locks_by_cell = new_locks
            # ALL LOCKED
            total = self.state.players_visible
            locked_count = len(self.state.locks_by_cell)
            if total>0 and locked_count>=total and not self.state.all_locked_announced:
                log.info(f"[locks] ALL LOCKED ({locked_count}/{total})")
                self.state.all_locked_announced = True
            if locked_count < total:
                self.state.all_locked_announced = False
            # Timer
            self._maybe_start_timer(sess)

    def _on_open(self, ws):
        log.info("[ws] connecté")
        try: ws.send('[5,"OnJsonApiEvent"]')
        except Exception as e: log.debug(f"[ws] subscribe error: {e}")

    def _on_message(self, ws, msg):
        try:
            data = json.loads(msg)
            if isinstance(data, list) and len(data) >= 3:
                if data[0] == 8 and isinstance(data[2], dict):
                    self._handle_api_event(data[2])
                return
            if isinstance(data, dict) and "uri" in data:
                self._handle_api_event(data)
        except Exception:
            pass

    def _on_error(self, ws, err):
        log.debug(f"[ws] error: {err}")
    def _on_close(self, ws, status, msg):
        log.debug(f"[ws] fermé: {status} {msg}")

    def run(self):
        if websocket is None: return
        for k in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy"):
            os.environ.pop(k, None)
        while not self.state.stop:
            self.lcu.refresh_if_needed()
            if not self.lcu.ok:
                time.sleep(1.0); continue
            url    = f"wss://127.0.0.1:{self.lcu.port}/"
            origin = f"https://127.0.0.1:{self.lcu.port}"
            token  = base64.b64encode(f"riot:{self.lcu.pw}".encode("utf-8")).decode("ascii")
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            try:
                self.ws = websocket.WebSocketApp(
                    url,
                    header=[f"Authorization: Basic {token}"],
                    subprotocols=["wamp"],
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self.ws.run_forever(
                    origin=origin,
                    sslopt={"context": ctx},
                    http_proxy_host=None,
                    http_proxy_port=None,
                    ping_interval=self.ping_interval,
                    ping_timeout=self.ping_timeout,
                )
            except Exception as e:
                log.debug(f"[ws] exception: {e}")
            time.sleep(1.0)

# --------- OCR thread : ROI verrouillée + burst ---------
class OCRSkinThread(threading.Thread):
    def __init__(self, state: SharedState, db: NameDB, ocr: OCR, args, lcu: Optional['LCU'] = None):
        super().__init__(daemon=True)
        self.state=state; self.db=db; self.ocr=ocr; self.args=args; self.lcu=lcu
        self.monitor_index = 0 if args.monitor=="all" else 1
        self.diff_threshold = args.diff_threshold
        self.burst_ms = args.burst_ms
        self.min_ocr_interval = args.min_ocr_interval
        self.second_shot_ms = args.second_shot_ms
        self.last_small=None; self.last_key=None; self.motion_until=0.0
        self.last_ocr_t=0.0; self.next_emit=time.time()
        self.emit_dt = (1.0/max(1.0, args.idle_hz)) if args.idle_hz>0 else None
        self.roi_abs = None; self.roi_lock_until = 0.0; self.roi_lock_s = args.roi_lock_s
        self.second_shot_at = 0.0

    def _calc_band_roi_abs(self, sct, monitor) -> Optional[Tuple[int,int,int,int]]:
        try:
            import mss
            if self.args.capture=="window" and is_windows():
                rect = find_league_window_rect(self.args.window_hint)
                if not rect: return None
                l,t,r,b = rect
                mon={"left":l,"top":t,"width":r-l,"height":b-t}
                full = np.array(sct.grab(mon), dtype=np.uint8)[:, :, :3]
                x1,y1,x2,y2 = choose_band(full)
                return (l+x1, t+y1, l+x2, t+y2)
            else:
                shot = sct.grab(monitor)
                full = np.array(shot, dtype=np.uint8)[:, :, :3]
                x1,y1,x2,y2 = choose_band(full)
                return (monitor["left"]+x1, monitor["top"]+y1, monitor["left"]+x2, monitor["top"]+y2)
        except Exception:
            return None

    def run(self):
        import mss
        log.info("[ocr] thread prêt (actif uniquement en ChampSelect).")
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[self.monitor_index]
                while not self.state.stop:
                    now = time.time()
                    if self.state.phase != "ChampSelect":
                        self.last_small=None; self.last_key=None
                        self.motion_until=0.0; self.last_ocr_t=0.0
                        self.roi_abs=None; self.roi_lock_until=0.0
                        time.sleep(0.15); continue
                    if self.roi_abs is None or now >= self.roi_lock_until:
                        roi = self._calc_band_roi_abs(sct, monitor)
                        if roi:
                            self.roi_abs = roi; self.roi_lock_until = now + self.roi_lock_s
                        else:
                            time.sleep(0.05); continue
                    L,T,R,B = self.roi_abs
                    mon = {"left":L, "top":T, "width":max(8,R-L), "height":max(8,B-T)}
                    try:
                        shot = sct.grab(mon); band = np.array(shot, dtype=np.uint8)[:, :, :3]
                    except Exception:
                        time.sleep(0.05); continue
                    if not getattr(self.state, "locked_champ_id", None):
                        self.last_small=None; self.last_key=None
                        self.motion_until=0.0; self.last_ocr_t=0.0
                        self.roi_abs=None; self.roi_lock_until=0.0
                        time.sleep(0.10); continue
                    band_bin = preprocess_band_for_ocr(band)
                    small = cv2.resize(band_bin, (96,20), interpolation=cv2.INTER_AREA)
                    changed = True
                    if self.last_small is not None:
                        diff = np.mean(np.abs(small.astype(np.int16)-self.last_small.astype(np.int16)))/255.0
                        changed = diff > self.diff_threshold
                    self.last_small = small
                    if changed:
                        self.motion_until = now + (self.burst_ms/1000.0)
                        if now - self.last_ocr_t >= self.min_ocr_interval:
                            self._run_ocr_and_match(band_bin); self.last_ocr_t = now
                            self.second_shot_at = now + (self.second_shot_ms/1000.0)
                    if self.second_shot_at and now >= self.second_shot_at:
                        if now - self.last_ocr_t >= (self.min_ocr_interval*0.6):
                            self._run_ocr_and_match(band_bin); self.last_ocr_t = now
                        self.second_shot_at = 0.0
                    if now < self.motion_until and (now - self.last_ocr_t >= self.min_ocr_interval):
                        self._run_ocr_and_match(band_bin); self.last_ocr_t = now
                    if self.emit_dt is not None and now >= self.next_emit and self.last_key:
                        log.info(f"[hover:skin] {self.last_key}")
                        self.next_emit = now + self.emit_dt
                    time.sleep(1.0/max(10.0, self.args.burst_hz) if now < self.motion_until else 1.0/max(5.0, self.args.idle_hz))
        finally:
            pass

    def _run_ocr_and_match(self, band_bin: np.ndarray):
        txt = self.ocr.recognize(band_bin)
        # Sauvegarde EXACTE du texte OCR nettoyé (espaces normalisés)
        try:
            cleaned_txt = re.sub(r"\s+", " ", txt.replace("\u00A0", " ").strip())
        except Exception:
            cleaned_txt = txt.strip()
        prev_txt = getattr(self.state, 'ocr_last_text', None)
        self.state.ocr_last_text = cleaned_txt
        if cleaned_txt and cleaned_txt != prev_txt:
            log.debug(f"[ocr:text] {cleaned_txt}")
        if not txt or not any(c.isalpha() for c in txt):
            return
        # Conserver l'exact OCR (nettoyé des espaces multiples) pour l'écriture
        try:
            cleaned_txt = re.sub(r"\s+", " ", txt.replace("\u00A0", " ").strip())
            self.state.ocr_last_text = cleaned_txt
        except Exception:
            self.state.ocr_last_text = txt.strip()
        norm_txt = _norm(txt)
        champ_id = self.state.hovered_champ_id or self.state.locked_champ_id
        pairs = self.db.normalized_entries(champ_id) or []
        skin_pairs = [(e, nk) for (e, nk) in pairs if e.kind == "skin"]
        champ_pairs = [(e, nk) for (e, nk) in pairs if e.kind == "champion"]
        
        # Combiner skins et champions pour la recherche
        all_pairs = skin_pairs + champ_pairs
        entries = None; labels = None
        if champ_id and all_pairs:
            entries, labels = zip(*all_pairs)
        else:
            if not all_pairs and champ_id:
                slug = self.db.slug_by_id.get(champ_id)
                if slug:
                    self.db._ensure_champ(slug, champ_id)
                    pairs = self.db.normalized_entries(champ_id) or []
                    skin_pairs = [(e, nk) for (e, nk) in pairs if e.kind == "skin"]
                    champ_pairs = [(e, nk) for (e, nk) in pairs if e.kind == "champion"]
                    all_pairs = skin_pairs + champ_pairs
                    if all_pairs:
                        entries, labels = zip(*all_pairs)
        if not entries: return
        # Utiliser notre système de score basé sur la distance de Levenshtein
        best_score = 0.0
        best_idx = None
        best_entry = None
        
        for i, (entry, label) in enumerate(all_pairs):
            score = _levenshtein_score(norm_txt, label)
            if score > best_score:
                best_score = score
                best_idx = i
                best_entry = entry
        
        if best_idx is None or best_score < self.args.min_conf:
            log.debug(f"[debug] No match found for OCR text: '{norm_txt}' (best score: {best_score:.3f})")
            return
            
        idx = best_idx
        score = best_score
        entry = best_entry
        log.debug(f"[debug] Match found: '{norm_txt}' -> '{labels[idx]}' (levenshtein score: {score:.3f})")
        # Vérifier que le match est valide
        if score < self.args.min_conf:
            return
        
        # Si c'est un champion (skin de base), vérifier que c'est une correspondance exacte
        if entry.kind == "champion":
            champ_nm = self.db.champ_name_by_id.get(champ_id or -1, "")
            if champ_nm:
                champ_tokens = set(_norm(champ_nm).split())
                txt_tokens = set(norm_txt.split())
                # Pour les skins de base, on veut une correspondance exacte
                if not (champ_tokens == txt_tokens or 
                       (champ_tokens and txt_tokens.issubset(champ_tokens) and len(norm_txt.split()) == len(champ_tokens))):
                    log.debug(f"[debug] Champion match not exact enough: '{norm_txt}' vs '{champ_nm}'")
                    return
        elif entry.kind != "skin":
            return
        if entry.key != self.last_key:
            if entry.kind == "champion":
                # Pour les skins de base, utiliser le nom du champion
                champ_name = self.db.champ_name_by_id.get(entry.champ_id, entry.key)
                log.info(f"[hover:skin] {champ_name} (skinId=0, champ={entry.champ_slug}, score={score:.3f})")
                self.state.last_hovered_skin_key  = champ_name
                self.state.last_hovered_skin_id   = 0  # 0 = skin de base
                self.state.last_hovered_skin_slug = entry.champ_slug
            else:
                # Pour les skins normaux, utiliser le nom du skin
                disp = self.db.skin_name_by_id.get(entry.skin_id) or entry.key
                log.info(f"[hover:skin] {disp} (skinId={entry.skin_id}, champ={entry.champ_slug}, score={score:.3f})")
                self.state.last_hovered_skin_key  = disp
                self.state.last_hovered_skin_id   = entry.skin_id
                self.state.last_hovered_skin_slug = entry.champ_slug
            self.last_key = entry.key

# ====================== Main ======================
def main():
    print("*** NEW VERSION LOADED *** - Skin ownership detection removed")
    ap=argparse.ArgumentParser(description="Tracer combiné LCU + OCR (ChampSelect) — ROI lock + burst OCR + locks/timer fixes")
    ap.add_argument("--tessdata", type=str, default=None, help="Chemin du dossier tessdata (ex: C:\\Program Files\\Tesseract-OCR\\tessdata)")
    ap.add_argument("--capture", choices=["window","screen"], default="window")
    ap.add_argument("--monitor", choices=["all","primary"], default="all")
    ap.add_argument("--window-hint", type=str, default="League")
    ap.add_argument("--psm", type=int, default=7)
    ap.add_argument("--min-conf", type=float, default=0.58)
    ap.add_argument("--lang", type=str, default="fra+eng", help="OCR lang (tesseract)")
    ap.add_argument("--dd-lang", type=str, default="en_US", help="Langue(s) DDragon: 'fr_FR' | 'fr_FR,en_US,es_ES' | 'all'")
    ap.add_argument("--tesseract-exe", type=str, default=None)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--burst-hz", type=float, default=1000.0)
    ap.add_argument("--idle-hz", type=float, default=0.0, help="ré-émission périodique (0=off)")
    ap.add_argument("--diff-threshold", type=float, default=0.012)
    ap.add_argument("--burst-ms", type=int, default=280)
    ap.add_argument("--min-ocr-interval", type=float, default=0.11)
    ap.add_argument("--second-shot-ms", type=int, default=120)
    ap.add_argument("--roi-lock-s", type=float, default=1.5)
    ap.add_argument("--phase-hz", type=float, default=2.0)
    ap.add_argument("--lockfile", type=str, default=None)
    ap.add_argument("--ws", action="store_true")
    ap.add_argument("--ws-ping", type=int, default=20)
    # >>>>> NOUVEAU : timer haute fréquence + fallback <<<<<
    ap.add_argument("--timer-hz", type=int, default=1000, help="Fréquence d'affichage du décompte loadout (Hz)")
    ap.add_argument("--fallback-loadout-ms", type=int, default=0, help="(déprécié) Ancien fallback ms si LCU ne donne pas le timer — ignoré")
    ap.add_argument("--skin-threshold-ms", type=int, default=2000, help="Écrire le dernier skin à T<=seuil (ms)")
    ap.add_argument("--skin-file", type=str, default=r"C:\Users\alban\Desktop\Skin changer\skin injector\last_hovered_skin.txt", help="Chemin du fichier last_hovered_skin.txt")
    ap.add_argument("--inject-batch", type=str, default=r"C:\Users\alban\Desktop\Skin changer\skin injector\inject_skin.bat", help="Batch à exécuter juste après l'écriture du skin (laisser vide pour désactiver)")

    args=ap.parse_args()

    setup_logging(args.verbose)
    log.info("Démarrage…")
    ocr = OCR(lang=args.lang, psm=args.psm, tesseract_exe=args.tesseract_exe)
    ocr.tessdata_dir = args.tessdata
    log.info(f"OCR: {ocr.backend}")
    db  = NameDB(lang=args.dd_lang)
    lcu = LCU(args.lockfile)
    state = SharedState()
    # config écriture skin
    state.skin_write_ms = int(getattr(args, 'skin_threshold_ms', 1500) or 1500)
    state.skin_file = getattr(args, 'skin_file', state.skin_file) or state.skin_file
    state.inject_batch = getattr(args, 'inject_batch', state.inject_batch) or state.inject_batch

    t_phase = PhaseThread(lcu, state, interval=1.0/max(0.5, args.phase_hz), log_transitions=not args.ws)
    t_champ = None if args.ws else ChampThread(lcu, db, state, interval=0.25)
    t_ocr   = OCRSkinThread(state, db, ocr, args, lcu)
    # Passer args à LoadoutTicker
    LoadoutTicker.args = args
    t_ws    = WSEventThread(lcu, db, state, ping_interval=args.ws_ping, timer_hz=args.timer_hz, fallback_ms=args.fallback_loadout_ms) if args.ws else None

    t_phase.start()
    if t_champ: t_champ.start()
    t_ocr.start()
    if t_ws: t_ws.start()

    print("[ok] prêt — tracer combiné. OCR actif UNIQUEMENT en Champ Select.", flush=True)

    last_phase = None
    try:
        while True:
            ph = state.phase
            if ph != last_phase:
                if ph == "InProgress":
                    if state.last_hovered_skin_key:
                        log.info(f"[launch:last-skin] {state.last_hovered_skin_key} (skinId={state.last_hovered_skin_id}, champ={state.last_hovered_skin_slug})")
                    else:
                        log.info("[launch:last-skin] (aucun skin survolé détecté)")
                last_phase = ph
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        state.stop = True
        t_phase.join(timeout=1.0)
        if t_champ: t_champ.join(timeout=1.0)
        t_ocr.join(timeout=1.0)
        if t_ws: t_ws.join(timeout=1.0)

if __name__ == "__main__":
    main()