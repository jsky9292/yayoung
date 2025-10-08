#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Yahoo Auction 크롤러 실행
"""

import subprocess
import sys
from datetime import datetime

print("\n" + "="*70)
print("⚾ Yahoo Auction Japan 글러브 크롤러")
print("="*70)
print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🔍 최신 데이터 크롤링 (진행중인 경매만)")
print("="*70)

# Yahoo 크롤러 실행
subprocess.run([sys.executable, "yahoo_crawler.py"])