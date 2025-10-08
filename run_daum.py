#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Daum 카페 (야용사) 크롤러 실행
"""

import subprocess
import sys
from datetime import datetime

print("\n" + "="*70)
print("💬 Daum 카페 (야용사) 글러브 크롤러")
print("="*70)
print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🔍 최신 게시글 크롤링")
print("\n⚠️ 주의사항:")
print("1. 이미 로그인되어 있다면 자동으로 진행됩니다.")
print("2. 로그인이 필요한 경우 브라우저에서 수동 로그인해주세요.")
print("="*70)

# Daum 크롤러 실행
subprocess.run([sys.executable, "yayongsa_crawler.py"])