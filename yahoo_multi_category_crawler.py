#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Yahoo Auction 골프/낚시 크롤러
카테고리 메인 페이지의 섹션(인기메이커, 추천경매, 히트상품)에서 상품 수집
"""

import os
import re
import json
import time
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def search_yahoo_auction(driver, category_id, category_name=""):
    """
    Yahoo Auction 카테고리 메인 페이지에서 상품 수집

    Args:
        driver: 웹드라이버
        category_id: 카테고리 ID
        category_name: 카테고리 이름 (표시용)
    """
    products = []

    try:
        # 상품 목록 페이지 접속 (category/list 형식)
        search_url = f"https://auctions.yahoo.co.jp/category/list/{category_id}/?n=100"

        print(f"\n{'='*60}")
        print(f"📂 {category_name} 크롤링 시작")
        print(f"{'='*60}")
        print(f"   URL: {search_url}")

        driver.get(search_url)
        time.sleep(3)

        # 상품 목록 가져오기
        print(f"\n📋 상품 목록 수집 중...")

        # 상품 목록 (div.Products.Products--grid > div > ul > li)
        product_elements = driver.find_elements(By.CSS_SELECTOR, "div.Products.Products--grid > div > ul > li")

        print(f"   ✅ {len(product_elements)}개 상품 발견")

        if not product_elements:
            print("   ⚠️ 상품을 찾을 수 없습니다.")
            return products

        for idx, element in enumerate(product_elements, 1):
            try:
                product_data = {}

                # 상품명 (div.Product__detail > h3 > a)
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, "div.Product__detail > h3 > a")
                    product_data['title'] = title_elem.text.strip()
                except:
                    product_data['title'] = ''

                if not product_data['title']:
                    continue

                # 이미지 (div.Product__image > a > img)
                try:
                    img_elem = element.find_element(By.CSS_SELECTOR, "div.Product__image > a > img")
                    product_data['image_url'] = img_elem.get_attribute('src')
                except:
                    product_data['image_url'] = ''

                # 상품 링크 (div.Product__detail > h3 > a)
                try:
                    link_elem = element.find_element(By.CSS_SELECTOR, "div.Product__detail > h3 > a")
                    product_data['url'] = link_elem.get_attribute('href')
                except:
                    product_data['url'] = ''

                # 현재가
                try:
                    price_elem = element.find_element(By.CSS_SELECTOR, "div.Product__priceInfo > span:nth-child(1) > span.Product__priceValue")
                    price_text = price_elem.text.strip()
                    price_text = price_text.replace(',', '').replace('円', '').replace('¥', '').replace(' ', '')
                    product_data['current_price'] = int(price_text) if price_text.isdigit() else 0
                except:
                    product_data['current_price'] = 0

                # 기본 정보
                product_data['bids'] = '0'
                product_data['time_left'] = ''

                # 판매완료 제외
                sold_keywords = ['終了', '売り切れ', '完売', 'SOLD', '落札', '売却済']
                if any(word in product_data['title'] for word in sold_keywords):
                            continue

                        # 브랜드 (기본값)
                        product_data['brand'] = '기타'

                        # 상태
                        if any(word in product_data['title'] for word in ['新品', '未使用', 'NEW']):
                            product_data['condition'] = '신품'
                        else:
                            product_data['condition'] = '중고'

                        # 기본 분류
                        product_data['position'] = '올라운드'
                        product_data['age_group'] = '성인용'

                        # 원화 환산
                        exchange_rate = 9.2
                        product_data['price_krw'] = int(product_data['current_price'] * exchange_rate)
                        product_data['exchange_rate'] = exchange_rate

                        # 배송비 계산
                        weight_kg = 0.6
                        shipping_fee_krw = int(weight_kg * 5000)
                        shipping_fee_jpy = shipping_fee_krw / exchange_rate
                        agent_fee_jpy = product_data['current_price'] * 0.1

                        # 관세 계산
                        customs_threshold_jpy = 21739
                        customs_fee_jpy = 0
                        if product_data['current_price'] > customs_threshold_jpy:
                            customs_fee_jpy = product_data['current_price'] * 0.23

                        # 총 비용
                        total_cost_jpy = product_data['current_price'] + shipping_fee_jpy + agent_fee_jpy + customs_fee_jpy
                        total_cost_krw = int(total_cost_jpy * exchange_rate)

                        product_data['shipping_fee_jpy'] = shipping_fee_jpy
                        product_data['agent_fee_jpy'] = agent_fee_jpy
                        product_data['customs_fee_jpy'] = customs_fee_jpy
                        product_data['total_cost_jpy'] = total_cost_jpy
                        product_data['total_cost_krw'] = total_cost_krw

                        # 카테고리 정보 추가
                        product_data['category'] = category_name
                        product_data['category_id'] = category_id

                        products.append(product_data)

                    except Exception as e:
                        print(f"      ⚠️ 상품 추출 오류: {e}")
                        continue

            except Exception as e:
                print(f"   ⚠️ 섹션 처리 오류: {e}")
                continue

        print(f"\n✅ 총 {len(products)}개 상품 수집 완료")

    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        import traceback
        traceback.print_exc()

    return products


# 골프 카테고리 정의
GOLF_CATEGORIES = {
    "2-1": {"id": "2084032133", "name": "골프 > 드라이버", "jp_name": "ドライバー"},
    "2-2": {"id": "2084032191", "name": "골프 > 아이언", "jp_name": "アイアン"},
    "2-3": {"id": "2084032212", "name": "골프 > 퍼터", "jp_name": "パター"},
    "2-4": {"id": "2084032165", "name": "골프 > 페어웨이우드", "jp_name": "フェアウェイウッド"},
    "2-5": {"id": "2084032190", "name": "골프 > 유틸리티", "jp_name": "ユーティリティ"},
    "2-6": {"id": "2084032211", "name": "골프 > 웨지", "jp_name": "ウェッジ"},
    "2-7": {"id": "2084006790", "name": "골프 > 골프웨어", "jp_name": "ウェア"},
}

# 낚시 카테고리 정의
FISHING_CATEGORIES = {
    "3-1": {"id": "2084007603", "name": "낚시 > 낚시대(민물)", "jp_name": "ロッド(淡水)"},
    "3-2": {"id": "2084007608", "name": "낚시 > 낚시대(바다)", "jp_name": "ロッド(海水)"},
    "3-3": {"id": "2084007564", "name": "낚시 > 릴(스피닝)", "jp_name": "スピニングリール"},
    "3-4": {"id": "2084007563", "name": "낚시 > 릴(베이트)", "jp_name": "ベイトリール"},
    "3-5": {"id": "2084005213", "name": "낚시 > 소프트루어", "jp_name": "ソフトルアー"},
    "3-6": {"id": "2084005214", "name": "낚시 > 하드루어", "jp_name": "ハードルアー"},
}


def main():
    """메인 함수"""

    print("\n" + "="*60)
    print("Yahoo Auction 골프/낚시 크롤러")
    print("="*60)

    # Chrome 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 카테고리 선택
        print("\n카테고리를 선택하세요:")
        print("1. 골프")
        print("2. 낚시")

        choice = input("\n선택 (1-2): ").strip()

        if choice == "1":
            # 골프 서브카테고리 선택
            print("\n골프 서브카테고리:")
            for key, cat in GOLF_CATEGORIES.items():
                print(f"{key}. {cat['name']}")

            sub_choice = input("\n선택: ").strip()

            if sub_choice in GOLF_CATEGORIES:
                cat_info = GOLF_CATEGORIES[sub_choice]
                products = search_yahoo_auction(driver, cat_info['id'], cat_info['name'])
            else:
                print("잘못된 선택입니다.")
                return

        elif choice == "2":
            # 낚시 서브카테고리 선택
            print("\n낚시 서브카테고리:")
            for key, cat in FISHING_CATEGORIES.items():
                print(f"{key}. {cat['name']}")

            sub_choice = input("\n선택: ").strip()

            if sub_choice in FISHING_CATEGORIES:
                cat_info = FISHING_CATEGORIES[sub_choice]
                products = search_yahoo_auction(driver, cat_info['id'], cat_info['name'])
            else:
                print("잘못된 선택입니다.")
                return

        else:
            print("잘못된 선택입니다.")
            return

        # 중복 제거
        unique_products = {}
        for product in products:
            url = product.get('url', '')
            if url and url not in unique_products:
                unique_products[url] = product

        products = list(unique_products.values())

        print(f"\n📊 총 {len(products)}개 상품 (중복 제거)")

        # JSON 저장
        if products:
            # data 폴더 생성
            os.makedirs('data', exist_ok=True)

            # 현재 시간 (한국시간)
            kst = timezone(timedelta(hours=9))
            now = datetime.now(kst)

            # 파일명 생성
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            filename = f"data/yahoo_auction_{timestamp}.json"

            # JSON 데이터 구성
            result = {
                "crawled_at": now.isoformat(),
                "crawled_date": now.strftime("%Y-%m-%d"),
                "crawled_time": now.strftime("%H:%M:%S"),
                "total_count": len(products),
                "products": products
            }

            # 파일 저장
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"\n💾 저장 완료: {filename}")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n브라우저를 종료합니다...")
        driver.quit()


if __name__ == "__main__":
    main()
