#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
야용사 크롤러 - 페이지네이션 포함 버전
"""

import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pytz

def search_yayongsa_gloves(user_dir="./"):
    """야용사 카페 크롤링 - 페이지네이션 포함"""

    print("=" * 60)
    print("야용사 카페 크롤러 시작 (다음 카페)")
    print("=" * 60)

    # Chrome 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_experimental_option("detach", True)  # 브라우저 유지

    print("📌 크롬 브라우저를 실행합니다...")
    print("   ⚠️ 창이 열리면 직접 로그인해주세요!")

    driver = webdriver.Chrome(options=options)
    products = []

    # 게시판 정보
    boards = [
        {"code": "79XF", "name": "중고글러브벼룩시장", "board": "중고글러브벼룩시장"},
        {"code": "2Fsn", "name": "새제품 글러브 벼룩시장", "board": "새제품 글러브 벼룩시장"}
    ]

    try:
        # 1. 야용사 카페 접속
        print("\n1. 야용사 카페 페이지로 이동합니다...")
        driver.get("https://cafe.daum.net/baseballsale")
        time.sleep(3)

        # 2. 로그인 확인
        if "login" in driver.current_url.lower() or "accounts.kakao.com" in driver.current_url:
            print("🔑 로그인이 필요합니다. 직접 로그인해주세요...")
            time.sleep(30)  # 30초 대기
        else:
            print("✅ 이미 로그인되어 있습니다!")

        print("\n5초 후 크롤링을 시작합니다...")
        time.sleep(5)

        print("\n2. 로그인 상태 확인 중...")
        current_url = driver.current_url
        if 'login' not in current_url.lower() and 'accounts.kakao.com' not in current_url:
            print("✅ 로그인 확인! 크롤링을 시작합니다...")
        else:
            print("⚠️ 로그인 상태 불확실 - 계속 진행합니다...")

        # 각 게시판 크롤링
        for board_info in boards:
            print(f"\n3. {board_info['name']} 게시판으로 이동...")

            board_url = f"https://cafe.daum.net/baseballsale/{board_info['code']}"
            driver.get(board_url)
            time.sleep(3)
            print(f"📅 최신 게시글 크롤링...")

            # iframe 전환 시도
            iframe_found = False
            iframe_ids = ["cafe_main", "down", "cafe_content"]

            for iframe_id in iframe_ids:
                try:
                    iframe = driver.find_element(By.ID, iframe_id)
                    driver.switch_to.frame(iframe)
                    print(f"   ✅ iframe 전환 성공: {iframe_id}")
                    iframe_found = True
                    time.sleep(1)
                    break
                except Exception as e:
                    print(f"   ❌ iframe 찾기 실패: {iframe_id}")
                    continue

            if not iframe_found:
                # name으로 시도
                try:
                    iframe = driver.find_element(By.NAME, "cafe_main")
                    driver.switch_to.frame(iframe)
                    print("   ✅ iframe 전환 성공 (name)")
                    iframe_found = True
                    time.sleep(1)
                except:
                    print("   ℹ️ iframe 없음 - 직접 파싱")

            # 페이지네이션 - 테스트를 위해 1페이지만
            max_pages = 1
            print(f"\n4. {board_info['name']} 게시글 목록 파싱... (최대 {max_pages}페이지)")

            for page_num in range(1, max_pages + 1):
                print(f"\n   📄 {page_num}페이지 수집 중...")

                # 2페이지부터 페이지 이동
                if page_num > 1:
                    try:
                        page_selector = f"#primaryContent > div.cont_boardlist > div.paging_g > div.inner_paging_number > ol > li:nth-child({page_num}) > a"
                        page_link = driver.find_element(By.CSS_SELECTOR, page_selector)
                        page_link.click()
                        time.sleep(2)
                        print(f"   ✅ {page_num}페이지로 이동")
                    except Exception as e:
                        print(f"   ⚠️ {page_num}페이지 이동 실패: {e}")
                        break  # 페이지가 없으면 중단

                # 게시글 찾기
                articles = []
                try:
                    articles = driver.find_elements(By.CSS_SELECTOR, "table.tbl_board_g tbody tr")
                    if not articles:
                        articles = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    print(f"   발견된 게시글: {len(articles)}개")
                except Exception as e:
                    print(f"   ❌ 게시글 찾기 실패: {e}")
                    continue

                # 게시글 수집 (step9 로직 사용)
                page_products = collect_articles(articles, board_info['board'])
                products.extend(page_products)

                print(f"   ✅ {page_num}페이지에서 {len(page_products)}개 수집")

            # iframe에서 벗어나기
            try:
                driver.switch_to.default_content()
            except:
                pass

        print(f"\n📊 전체 수집 완료: {len(products)}개 상품")

    except Exception as e:
        print(f"\n❌ 크롤링 오류: {e}")

    finally:
        print("\n크롤링 완료. 브라우저는 열려 있습니다.")

    # 결과 저장
    if products:
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst)
        timestamp = now.strftime('%Y%m%d_%H%M%S')

        # 데이터 저장
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)

        filename = f'yayongsa_{timestamp}.json'
        filepath = os.path.join(data_dir, filename)

        data = {
            'crawled_at': now.isoformat(),
            'crawled_date': now.strftime('%Y-%m-%d'),
            'crawled_time': now.strftime('%H:%M:%S'),
            'total_count': len(products),
            'products': products
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 데이터 저장 완료: {filepath}")
        print(f"   총 {len(products)}개 상품")
        print(f"   크롤링 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    return products

def collect_articles(articles, board_name):
    """게시글 수집 함수 - step9 로직 사용"""
    products = []

    for idx, article in enumerate(articles[:5], 1):  # 테스트를 위해 5개만
        try:
            product_data = {}
            product_data['board'] = board_name

            # TD들 찾기
            tds = article.find_elements(By.TAG_NAME, "td")

            # 두 번째 TD의 a 태그에서 제목 추출
            if len(tds) >= 2:
                try:
                    link = tds[1].find_element(By.TAG_NAME, "a")
                    product_data['title'] = link.text.strip()
                    product_data['url'] = link.get_attribute('href')
                except:
                    # 대체 방법
                    try:
                        link = article.find_element(By.CSS_SELECTOR, "a[href*='bbs_read']")
                        product_data['title'] = link.text.strip()
                        product_data['url'] = link.get_attribute('href')
                    except:
                        continue
            else:
                continue

            # 제목이 없으면 스킵
            if not product_data['title']:
                continue

            # 공지사항 제외
            if '공지' in product_data['title'] or '필독' in product_data['title']:
                continue

            # 나머지 데이터 추출
            if len(tds) >= 5:
                product_data['author'] = tds[2].text.strip() if len(tds) > 2 else ''
                product_data['date'] = tds[3].text.strip() if len(tds) > 3 else ''
                product_data['views'] = tds[4].text.strip() if len(tds) > 4 else '0'
            else:
                product_data['author'] = ''
                product_data['date'] = ''
                product_data['views'] = '0'

            # 추가 데이터 설정
            title_lower = product_data['title'].lower()

            # 상세 페이지에서 가격과 이미지 추출
            price, images = extract_details_from_article(driver, product_data['url'])
            product_data['price'] = price
            product_data['images'] = images

            # 브랜드 추출
            product_data['brand'] = extract_brand_from_title(product_data['title'])

            # 포지션 추출
            product_data['position'] = extract_position_from_title(product_data['title'])

            # 지역 설정
            product_data['location'] = '미상'

            # 상태 설정
            if '새상품' in title_lower or '신품' in title_lower:
                product_data['condition'] = '신품'
            else:
                product_data['condition'] = '중고'

            products.append(product_data)
            print(f"  ✅ [{idx}] {product_data['title'][:40]}...")

        except Exception as e:
            print(f"  ❌ [{idx}] 파싱 오류: {e}")
            continue

    return products

def extract_details_from_article(driver, article_url):
    """상세 페이지에서 가격과 이미지 추출"""
    price = 0
    images = []

    try:
        # 현재 창 핸들 저장
        main_window = driver.current_window_handle

        # 새 탭에서 상세 페이지 열기
        driver.execute_script(f"window.open('{article_url}', '_blank');")

        # 새 탭으로 전환
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)

        # iframe 전환 시도
        try:
            iframe = driver.find_element(By.ID, "down")
            driver.switch_to.frame(iframe)
        except:
            pass

        # 가격 추출 - 본문에서 숫자 찾기
        try:
            content_element = driver.find_element(By.ID, "user_contents")
            content_text = content_element.text

            # 가격 패턴 찾기 (판매가격 : 형식 우선)
            import re
            price_patterns = [
                r'판매가격\s*[:\s]*(\d{1,3}(?:,\d{3})*)\s*(?:만원|만)',
                r'판매가격\s*[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'판매가\s*[:\s]*(\d{1,3}(?:,\d{3})*)\s*(?:만원|만)',
                r'가격\s*[:\s]*(\d{1,3}(?:,\d{3})*)\s*(?:만원|만)',
                r'(\d{1,3}(?:,\d{3})*)\s*만원',
                r'판매가\s*[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'가격\s*[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'(\d{1,3}(?:,\d{3})*)\s*원',
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    price_str = matches[0].replace(',', '')
                    price = int(price_str)
                    # 패턴에 '만원' 또는 '만'이 포함되어 있으면 10000 곱하기
                    if '만원' in pattern or '만' in pattern:
                        price *= 10000
                    break

            # 가격을 못 찾았으면 더 넓은 패턴으로 재시도
            if price == 0:
                # 숫자만 찾기 (10000 이상인 첫 번째 숫자)
                number_pattern = r'(\d{5,7})'
                numbers = re.findall(number_pattern, content_text.replace(',', ''))
                for num_str in numbers:
                    num = int(num_str)
                    if 10000 <= num <= 9999999:  # 1만원~999만원 범위
                        price = num
                        break

            print(f"    추출된 가격: {price:,}원")
        except Exception as e:
            print(f"    가격 추출 실패: {e}")

        # 이미지 추출
        try:
            # 여러 이미지 셀렉터 시도 (특정 위치 우선)
            image_selectors = [
                "#user_contents > div:nth-child(10) > img",  # 사용자가 지정한 선택자
                "#user_contents > div > img",
                "#user_contents img",
                ".user_contents img",
                "img[src*='cafefile']"
            ]

            for selector in image_selectors:
                img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if img_elements:
                    for img in img_elements[:5]:  # 최대 5개까지
                        img_src = img.get_attribute('src')
                        if img_src and 'cafefile' in img_src:
                            images.append(img_src)
                    if images:  # 이미지를 찾았으면 중단
                        print(f"    이미지 {len(images)}개 추출 (선택자: {selector})")
                        break

        except Exception as e:
            print(f"    이미지 추출 실패: {e}")

        # 탭 닫고 원래 탭으로 돌아가기
        driver.close()
        driver.switch_to.window(main_window)

    except Exception as e:
        print(f"    상세 페이지 접근 실패: {e}")
        # 실패 시 원래 탭으로 돌아가기
        try:
            driver.switch_to.window(main_window)
        except:
            pass

    return price, images

def extract_brand_from_title(title):
    """제목에서 브랜드 추출"""
    brands = {
        '미즈노': 'Mizuno', 'mizuno': 'Mizuno', 'MIZUNO': 'Mizuno',
        '윌슨': 'Wilson', 'wilson': 'Wilson', 'WILSON': 'Wilson',
        '롤링스': 'Rawlings', 'rawlings': 'Rawlings', 'RAWLINGS': 'Rawlings',
        '제트': 'ZETT', 'zett': 'ZETT', 'ZETT': 'ZETT',
        'SSK': 'SSK', 'ssk': 'SSK',
        '아톰즈': 'ATOMS', 'atoms': 'ATOMS', 'ATOMS': 'ATOMS',
        '구보타': 'Kubota', 'kubota': 'Kubota', 'KUBOTA': 'Kubota',
    }

    title_lower = title.lower()
    for keyword, brand_name in brands.items():
        if keyword.lower() in title_lower:
            return brand_name

    return '기타'

def extract_position_from_title(title):
    """제목에서 포지션 추출"""
    positions = {
        '내야': '내야수', '외야': '외야수', '투수': '투수',
        '포수': '포수', '올라운드': '올라운드',
        '유격수': '내야수', '2루수': '내야수', '3루수': '내야수', '1루수': '내야수',
    }

    for keyword, position_name in positions.items():
        if keyword in title:
            return position_name

    return '올라운드'

if __name__ == "__main__":
    import sys
    user_dir = sys.argv[1] if len(sys.argv) > 1 else './'

    products = search_yayongsa_gloves(user_dir)
    print(f"\n총 {len(products)}개의 야용사 상품을 수집했습니다.")