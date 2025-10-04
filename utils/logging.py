#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging configuration and utilities
"""

import sys
import time
import logging
import urllib3
from urllib3.exceptions import InsecureRequestWarning


def setup_logging(verbose: bool):
    """Setup logging configuration"""
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
    
    # Suppress HTTPS/HTTP logs
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    # Disable SSL warnings for LCU (self-signed cert)
    urllib3.disable_warnings(InsecureRequestWarning)


def get_logger(name: str = "tracer") -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
