#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR backend implementation
"""

import os
from typing import Optional
import numpy as np
import cv2


class OCR:
    """OCR backend using tesserocr"""
    
    def __init__(self, lang: str = "eng", psm: int = 7, tesseract_exe: Optional[str] = None):
        self.lang = lang
        self.psm = int(psm)
        self.backend = None
        self.api = None
        
        try:
            from tesserocr import PyTessBaseAPI, PSM  # pyright: ignore[reportMissingImports]
            
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
            # Remove character whitelist to allow all Unicode characters
            # This enables recognition of Korean, Chinese, Greek, and other Unicode characters
            self.backend = "tesserocr"
        except ImportError:
            raise ImportError("tesserocr is required for OCR functionality")

    def recognize(self, img: np.ndarray) -> str:
        """Recognize text in image"""
        if self.backend == "tesserocr":
            from PIL import Image
            pil = Image.fromarray(img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            self.api.SetImage(pil)
            txt = self.api.GetUTF8Text() or ""
        else:
            cfg = f"-l {self.lang} --oem 3 --psm {self.psm} -c preserve_interword_spaces=1"
            txt = self.pytesseract.image_to_string(img, config=cfg)
        
        txt = txt.replace("\n", " ").strip()
        txt = txt.replace("'", "'").replace("`", "'")
        return " ".join(txt.split())
