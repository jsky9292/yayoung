#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Yahoo Auction 크롤러 실행 스크립트
Chrome 창이 자동으로 열리도록 설정
"""

import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import json

# 현재 디렉토리를 작업 디렉토리로 설정
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# yahoo_crawler 모듈 가져오기
from yahoo_crawler import search_yahoo_auction

def main():
    print("\n" + "="*70)
    print("⚾ Yahoo Auction Japan 글러브 크롤러")
    print("="*70)
    print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔍 최신 데이터 크롤링 시작...")
    print("="*70)

    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # headless 모드 비활성화 (창이 보이도록)
    # chrome_options.add_argument('--headless')  # 제거

    # 브라우저 크기 설정
    chrome_options.add_argument('--window-size=1280,800')

    # User-Agent 설정
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        # Chrome 드라이버 시작
        print("\n🌐 Chrome 브라우저 시작 중...")
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Chrome 브라우저가 시작되었습니다.")

        # 크롤링 실행
        keyword = '硬式グローブ'
        print(f"\n🔍 검색 키워드: {keyword}")
        print("⏳ 크롤링 진행 중... (약 1-2분 소요)")

        results = search_yahoo_auction(driver, keyword)

        print(f"\n✅ 크롤링 완료!")
        print(f"📦 수집된 상품: {len(results)}개")

        # 결과 저장
        if results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/yahoo_auction_{timestamp}.json'

            # data 디렉토리가 없으면 생성
            if not os.path.exists('data'):
                os.makedirs('data')

            # JSON 파일로 저장
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'crawled_at': datetime.now().isoformat(),
                    'keyword': keyword,
                    'total_count': len(results),
                    'products': results
                }, f, ensure_ascii=False, indent=2)

            print(f"💾 데이터 저장 완료: {filename}")

            # 처음 3개 상품 정보 출력
            print("\n📋 수집된 상품 예시:")
            for i, item in enumerate(results[:3], 1):
                print(f"\n{i}. {item.get('title', 'N/A')[:50]}...")
                print(f"   가격: ¥{item.get('current_price', 0):,}")
                print(f"   브랜드: {item.get('brand', 'N/A')}")
                print(f"   포지션: {item.get('position', 'N/A')}")

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        if 'driver' in locals():
            print("\n🔧 브라우저를 종료합니다...")
            driver.quit()
            print("✅ 브라우저가 종료되었습니다.")

    print("\n" + "="*70)
    print("크롤링 작업이 완료되었습니다.")
    print("="*70)

if __name__ == "__main__":
    main()