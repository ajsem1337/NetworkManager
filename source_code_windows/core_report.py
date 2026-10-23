#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import core_config
import security_utils

G, R, C, RESET = '\033[92m', '\033[91m', '\033[96m', '\033[0m'


def save(content, filename_prefix="Report"):
    """Save a unique report inside Reports, using private POSIX permissions."""
    try:
        core_config.init()
        path = security_utils.save_report(
            core_config.REPORTS_DIR, content, filename_prefix,
            time.strftime("%Y%m%d_%H%M%S"),
        )
        print(f"\n {G}[SUKCES]{RESET} Raport zapisano.")
        print(f" Plik: {C}{path}{RESET}")
        return path
    except Exception as exc:
        print(f"\n {R}[BŁĄD ZAPISU]{RESET} {exc}")
        return None
