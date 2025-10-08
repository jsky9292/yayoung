#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
통합 크롤러 실행 스크립트
Yahoo Auction과 Daum 카페 크롤러를 순차적으로 실행
"""

import subprocess
import sys
import time
from datetime import datetime

def print_header(title):
    """헤더 출력"""
    print("\n" + "="*70)
    print(f"🚀 {title}")
    print("="*70)

def run_yahoo_crawler():
    """Yahoo Auction 크롤러 실행"""
    print_header("Yahoo Auction Japan 크롤러 시작")

    try:
        # yahoo_crawler.py 실행
        result = subprocess.run(
            [sys.executable, "yahoo_crawler.py"],
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print("✅ Yahoo 크롤러 완료!")
            return True
        else:
            print("❌ Yahoo 크롤러 실행 중 오류 발생")
            return False

    except Exception as e:
        print(f"❌ Yahoo 크롤러 실행 실패: {e}")
        return False

def run_daum_crawler():
    """Daum 카페 (야용사) 크롤러 실행"""
    print_header("Daum 카페 크롤러 시작")

    try:
        # yayongsa_crawler.py 실행
        result = subprocess.run(
            [sys.executable, "yayongsa_crawler.py"],
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print("✅ Daum 카페 크롤러 완료!")
            return True
        else:
            print("❌ Daum 카페 크롤러 실행 중 오류 발생")
            return False

    except Exception as e:
        print(f"❌ Daum 카페 크롤러 실행 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("\n" + "🏀"*35)
    print("\n" + " "*20 + "⚾ 글러브 마켓 통합 크롤러 ⚾")
    print("\n" + "🏀"*35)

    start_time = datetime.now()
    print(f"\n시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 크롤러 선택
    print("\n" + "="*70)
    print("크롤링 옵션을 선택하세요:")
    print("1. Yahoo Auction만 크롤링")
    print("2. Daum 카페만 크롤링")
    print("3. 모두 크롤링 (Yahoo → Daum)")
    print("="*70)

    choice = input("\n선택 (1/2/3): ").strip()

    yahoo_success = False
    daum_success = False

    if choice == '1':
        # Yahoo만 실행
        yahoo_success = run_yahoo_crawler()

    elif choice == '2':
        # Daum만 실행
        print("\n⚠️ 주의: Daum 카페 크롤링은 로그인이 필요합니다.")
        print("로그인 화면이 나오면 수동으로 로그인해주세요.")
        time.sleep(2)
        daum_success = run_daum_crawler()

    elif choice == '3':
        # 둘 다 실행
        # 1. Yahoo 크롤러 실행
        yahoo_success = run_yahoo_crawler()

        if yahoo_success:
            print("\n잠시 대기 중...")
            time.sleep(3)

            # 2. Daum 크롤러 실행
            print("\n⚠️ 주의: Daum 카페 크롤링은 로그인이 필요할 수 있습니다.")
            print("이미 로그인되어 있다면 자동으로 진행됩니다.")
            time.sleep(2)
            daum_success = run_daum_crawler()
    else:
        print("❌ 잘못된 선택입니다.")
        return

    # 결과 요약
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "="*70)
    print("📊 크롤링 결과 요약")
    print("="*70)

    if choice in ['1', '3']:
        status = "✅ 성공" if yahoo_success else "❌ 실패"
        print(f"Yahoo Auction: {status}")

    if choice in ['2', '3']:
        status = "✅ 성공" if daum_success else "❌ 실패"
        print(f"Daum 카페: {status}")

    print(f"\n총 소요 시간: {duration}")
    print(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "="*70)
    print("✨ 크롤링이 완료되었습니다!")
    print("📂 수집된 데이터는 JSON 파일로 저장되었습니다.")
    print("🖼️ 이미지는 별도 폴더에 저장되었습니다.")
    print("="*70)

if __name__ == "__main__":
    main()