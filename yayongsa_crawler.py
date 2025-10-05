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
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
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

        # 2. 로그인 대기
        print("\n2. 로그인 대기 중...")
        print("   ⚠️ 다음 카페에 로그인해주세요!")
        print("   ⚠️ 로그인 완료 후 30초 대기합니다...")

        # 30초 카운트다운
        for i in range(30, 0, -5):
            time.sleep(5)
            print(f"   ⏰ {i}초 남음...")

        print("\n✅ 대기 완료! 크롤링을 시작합니다...")
        time.sleep(2)

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

            # 페이지네이션 - 3페이지까지
            max_pages = 3
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

                # 게시글 찾기 - #article-list > tr 사용
                articles = []
                try:
                    articles = driver.find_elements(By.CSS_SELECTOR, "#article-list > tr")
                    if not articles:
                        # 대체 셀렉터
                        articles = driver.find_elements(By.CSS_SELECTOR, "table.tbl_board_g tbody tr")
                    if not articles:
                        articles = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    print(f"   발견된 게시글: {len(articles)}개")
                except Exception as e:
                    print(f"   ❌ 게시글 찾기 실패: {e}")
                    continue

                # 게시글 수집 (step9 로직 사용)
                page_products = collect_articles(driver, articles, board_info['board'])
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
        # 브라우저 종료
        try:
            driver.quit()
            print("\n✅ 크롤링 완료. 브라우저를 닫았습니다.")
        except:
            print("\n✅ 크롤링 완료.")

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

def collect_articles(driver, articles, board_name):
    """게시글 수집 함수 - step9 로직 사용"""
    products = []
    max_products = 50  # 페이지당 최대 수집 제품 수

    for idx, article in enumerate(articles, 1):  # 모든 게시글 처리
        # 이미 최대 제품 수에 도달하면 중단
        if len(products) >= max_products:
            break

        try:
            product_data = {}
            product_data['board'] = board_name

            # TD들 찾기
            tds = article.find_elements(By.TAG_NAME, "td")

            # 공지사항 제외 - 첫 번째 td 확인
            if len(tds) > 0:
                first_td_text = tds[0].text.strip()
                if '공지' in first_td_text or '필독' in first_td_text or 'notice' in first_td_text.lower():
                    print(f"  ⏭️ 공지사항 스킵: {first_td_text}")
                    continue

            # td.td_board에서 링크 찾기
            try:
                # td.td_board > div > div > a 형식으로 제목과 URL 추출
                td_board = article.find_element(By.CSS_SELECTOR, "td.td_board")
                link = td_board.find_element(By.TAG_NAME, "a")
                product_data['title'] = link.text.strip()
                product_data['url'] = link.get_attribute('href')
            except:
                # 대체 방법: 두 번째 TD의 a 태그
                if len(tds) >= 2:
                    try:
                        link = tds[1].find_element(By.TAG_NAME, "a")
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

            # 판매완료 여부 확인
            sold_out_keywords = ['판매완료', '거래완료', '완료', 'sold', 'sold out']
            product_data['sold_out'] = any(keyword in title_lower for keyword in sold_out_keywords)

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

        # 쿠키 저장
        cookies = driver.get_cookies()

        # 새 탭에서 상세 페이지 열기
        driver.execute_script(f"window.open('{article_url}', '_blank');")

        # 새 탭으로 전환
        driver.switch_to.window(driver.window_handles[-1])

        # 쿠키 복원 (동일 도메인이므로 자동 전달되지만 명시적으로 설정)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass

        # 페이지 새로고침하여 쿠키 적용
        driver.refresh()
        time.sleep(2)

        # iframe 전환 시도
        try:
            iframe = driver.find_element(By.ID, "down")
            driver.switch_to.frame(iframe)
        except:
            pass

        # 가격 추출 - 본문 전체에서 추출
        price = 0
        try:
            import re

            content_element = driver.find_element(By.ID, "user_contents")
            content_text = content_element.text

            price_patterns = [
                (r'판매가격\s*[:：]\s*(\d{1,3})\s*만', 10000),
                (r'판매가격\s*[:：]\s*(\d{2,3})(?:\s|$|\n)', 10000),
                (r'판매가\s*[:：]\s*(\d{1,3})\s*만', 10000),
                (r'가격\s*[:：]\s*(\d{1,3})\s*만', 10000),
                (r'(\d{1,3})\s*만\s*원', 10000),
            ]

            for pattern, multiplier in price_patterns:
                matches = re.findall(pattern, content_text, re.IGNORECASE)
                if matches:
                    try:
                        price_str = matches[0].replace(',', '').strip()
                        price = int(price_str) * multiplier
                        print(f"    ✅ 가격 추출 (본문): {price:,}원")
                        break
                    except:
                        continue

            # 숫자만 찾기
            if price == 0:
                content_element = driver.find_element(By.ID, "user_contents")
                content_text = content_element.text
                numbers = re.findall(r'\b(\d{5,6})\b', content_text.replace(',', ''))
                for num_str in numbers:
                    num = int(num_str)
                    if 20000 <= num <= 999999:
                        price = num
                        print(f"    ⚠️ 추정 가격: {price:,}원")
                        break

            if price == 0:
                print(f"    ❌ 가격 추출 실패")

        except Exception as e:
            print(f"    ❌ 가격 추출 오류: {e}")

        # 이미지 추출 - iframe 전체에서 검색
        try:
            # iframe 전체에서 img 태그 검색
            all_images = driver.find_elements(By.TAG_NAME, "img")

            if all_images:
                print(f"    📷 총 {len(all_images)}개 이미지 발견")

                # cafefile 또는 kakaocdn 이미지만 필터링 (이모티콘 제외)
                valid_images = []
                for idx, img in enumerate(all_images, 1):
                    try:
                        # src와 data-img-src 모두 확인
                        img_src = img.get_attribute('data-img-src') or img.get_attribute('src')

                        if img_src:
                            # 제외 패턴: 이모티콘, 아이콘, UI 이미지, 작은 썸네일
                            exclude_patterns = [
                                'emoticon', 'sticker', 'emoji', 'icon',
                                'btn', 'button', 'new.png', 'skin/',
                                'thumb/C90x90', 'thumb/C120x120', 'thumb/C150x150'
                            ]
                            if any(x in img_src.lower() for x in exclude_patterns):
                                continue

                            # 실제 첨부 이미지만 포함 (cafeattach가 가장 확실)
                            if 'cafeattach' in img_src:
                                valid_images.append(img_src)
                    except:
                        continue

                # 첫 번째 이미지만 썸네일로 사용
                if valid_images:
                    images = [valid_images[0]]  # 첫 번째만
                    print(f"    ✅ 썸네일 이미지 추출: {images[0][:80]}...")
                else:
                    print(f"    ❌ 유효한 이미지 없음")

                # 처음 3개 이미지 URL 출력
                for idx, img_url in enumerate(images[:3], 1):
                    print(f"      {idx}. {img_url[:80]}...")
            else:
                print(f"    ❌ 이미지 요소를 찾을 수 없음")

        except Exception as e:
            print(f"    ❌ 이미지 추출 오류: {e}")

        # 탭 닫고 원래 창으로 복귀
        try:
            driver.close()
            driver.switch_to.window(main_window)
            time.sleep(1)

            # iframe으로 다시 전환
            try:
                iframe = driver.find_element(By.ID, "down")
                driver.switch_to.frame(iframe)
                print(f"    ✅ 목록으로 복귀 완료")
            except Exception as iframe_error:
                print(f"    ⚠️ iframe 복귀 실패: {iframe_error}")
        except Exception as e:
            print(f"    ⚠️ 탭 닫기 오류: {e}")

    except Exception as e:
        print(f"    ❌ 상세 페이지 접근 실패: {e}")
        # 실패 시 탭 닫기 시도
        try:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
            time.sleep(1.5)

            # 목록 페이지의 iframe으로 다시 전환
            try:
                iframe = driver.find_element(By.ID, "down")
                driver.switch_to.frame(iframe)
            except:
                pass
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