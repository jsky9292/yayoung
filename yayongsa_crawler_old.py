#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
야용사 카페 크롤러 - 수동 로그인 후 크롤링
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
import re

def search_yayongsa_gloves(user_dir='./'):
    """야용사 카페에서 글러브 검색 - 수동 로그인 후 크롤링"""

    print("\n" + "="*60)
    print("야용사 카페 크롤러 시작 (다음 카페)")
    print("="*60)

    # 크롬 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    # 창이 자동으로 닫히지 않도록 설정
    options.add_experimental_option("detach", True)

    # 브라우저 창 표시 (헤드리스 모드 OFF)
    print("📌 크롬 브라우저를 실행합니다...")
    print("   ⚠️ 창이 열리면 직접 로그인해주세요!")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    # 페이지 로드 시간 제한 설정
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)

    products = []

    try:
        # 야용사 카페로 바로 접속
        print("\n1. 야용사 카페 페이지로 이동합니다...")
        driver.get("https://cafe.daum.net/baseballsale")
        time.sleep(3)

        # 로그인 페이지로 이동할 수도 있음
        current_url = driver.current_url

        # 로그인이 필요한 경우 수동 로그인 대기
        if 'login' in current_url.lower() or 'accounts.kakao.com' in current_url:
            print("\n" + "="*60)
            print("🔐 로그인이 필요합니다!")
            print("="*60)
            print("지금 열린 Chrome 브라우저에서:")
            print("1. 카카오 계정으로 로그인")
            print("2. 2단계 인증 완료")
            print("3. 야용사 카페 가입 확인")
            print("\n⏰ 로그인 완료 후 Enter 키를 눌러주세요...")
            print("="*60)

            # 사용자가 수동으로 로그인할 때까지 대기
            print("\n🔄 로그인을 기다리는 중... (최대 30초)")

            # 로그인 완료 대기 (최대 30초)
            max_wait = 30
            wait_count = 0
            while wait_count < max_wait:
                time.sleep(5)
                wait_count += 5

                # 현재 URL 확인
                current = driver.current_url
                if 'login' not in current.lower() and 'accounts.kakao.com' not in current:
                    print("\n✅ 로그인 감지! 크롤링을 시작합니다...")
                    break

                print(f"⏳ 대기 중... ({wait_count}/{max_wait}초)")

            if wait_count >= max_wait:
                print("\n⏰ 시간 초과. 로그인을 다시 시도해주세요.")
                return []
        else:
            # 이미 로그인되어 있는 경우
            print("\n✅ 이미 로그인되어 있습니다!")
            print("\n5초 후 크롤링을 시작합니다...")
            time.sleep(5)

        # 게시판으로 이동하여 로그인 상태 재확인
        print("\n2. 로그인 상태 확인 중...")
        driver.get("https://cafe.daum.net/baseballsale/79XF")
        time.sleep(3)

        current_url = driver.current_url
        page_source = driver.page_source

        # 여전히 로그인이 안되어 있다면
        if 'login' in current_url.lower() or 'accounts.kakao.com' in current_url or '로그인' in page_source:
            print("\n❌ 로그인이 실패했습니다. 다시 시도해주세요.")
            print("브라우저를 닫고 다시 실행해주세요.")
            return []
        else:
            print("✅ 로그인 확인! 크롤링을 시작합니다...")

        # 크롤링할 게시판 목록
        boards = [
            {"name": "중고글러브벼룩시장", "id": "79XF", "board": "중고글러브벼룩시장"},
            {"name": "새제품 글러브 벼룩시장", "id": "2Fsn", "board": "새제품 글러브 벼룩시장"}
        ]

        # 각 게시판 크롤링
        for board_info in boards:
            print(f"\n3. {board_info['name']} 게시판으로 이동...")
            print(f"📅 최신 게시글 크롤링...")

            # 게시판 페이지를 최신순으로 정렬
            driver.get(f"https://cafe.daum.net/baseballsale/{board_info['id']}?sort=R")  # R=최신순
            time.sleep(3)

            # 페이지가 완전히 로드될 때까지 대기
            time.sleep(3)

            # iframe으로 전환 (다음 카페는 iframe 사용) - ID가 다를 수 있음
            iframe_found = False

            # iframe ID 다양한 시도
            iframe_ids = ["cafe_main", "down", "cafe_content"]

            for iframe_id in iframe_ids:
                try:
                    iframe = driver.find_element(By.ID, iframe_id)
                    driver.switch_to.frame(iframe)
                    print(f"   ✅ iframe 전환 성공: {iframe_id}")
                    iframe_found = True
                    time.sleep(1)
                    break
                except:
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

            # 게시글 목록 파싱
            print(f"\n4. {board_info['name']} 게시글 목록 파싱...")

            # 검색어로 필터링
            print("   '글러브' 관련 게시글만 수집합니다...")

            # 페이지네이션 - 3페이지까지
            max_pages = 3
            for page_num in range(1, max_pages + 1):
                print(f"\n   📄 {page_num}페이지 수집 중...")

                # 페이지 이동 (2페이지부터)
                if page_num > 1:
                    try:
                        # 페이지 번호 클릭
                        # 셀렉터 패턴: li:nth-child(페이지번호) > a > span
                        page_selector = f"#primaryContent > div.cont_boardlist > div.paging_g > div.inner_paging_number > ol > li:nth-child({page_num}) > a"
                        page_link = driver.find_element(By.CSS_SELECTOR, page_selector)
                        page_link.click()
                        time.sleep(2)  # 페이지 로드 대기
                        print(f"   ✅ {page_num}페이지로 이동")
                    except Exception as e:
                        print(f"   ⚠️ {page_num}페이지 이동 실패: {e}")
                        break  # 페이지가 없으면 중단

                # 다음 카페 게시글 목록 찾기
                articles = []

                # 다음 카페는 게시글이 tr로 구성됨
                # 실제 게시글 셀렉터 사용
                # 다음 카페는 보통 tbody > tr 구조로 되어 있음
                # 실제 테이블 클래스: tbl_board_g board_check
                articles = driver.find_elements(By.CSS_SELECTOR, "table.tbl_board_g tbody tr")

                if not articles:
                    # 대체 셀렉터 1: 클래스명 없는 테이블
                    articles = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

                if not articles:
                    # 대체 셀렉터 2: bbsList (이전 버전)
                    articles = driver.find_elements(By.CSS_SELECTOR, "table.bbsList tbody tr")

                if not articles:
                    # 대체 셀렉터 3: 모든 tr 찾고 필터링
                    articles = driver.find_elements(By.TAG_NAME, "tr")
                    # 헤더와 공지 제외 - 하지만 전체 수집
                    articles = [a for a in articles if a.text]

                # 디버깅: HTML 구조 확인
                if not articles:
                    print("\n   ⚠️ 게시글을 찾지 못했습니다. HTML 구조 확인 중...")

                # 페이지 소스 일부 출력
                page_source = driver.page_source[:2000]
                if 'bbsList' in page_source:
                    print("   - bbsList 클래스 발견")
                if 'listBody' in page_source:
                    print("   - listBody ID 발견")

                # 모든 테이블 찾기
                tables = driver.find_elements(By.TAG_NAME, "table")
                print(f"   - 전체 table 수: {len(tables)}")

                # 모든 tr 요소 찾기
                all_trs = driver.find_elements(By.TAG_NAME, "tr")
                print(f"   - 전체 tr 수: {len(all_trs)}")

                # 게시글 링크 직접 찾기
                post_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/baseballsale/']")
                print(f"   - 게시글 링크 수: {len(post_links)}")

                if post_links:
                    for i, link in enumerate(post_links[:3]):
                        print(f"   - 링크 {i+1}: {link.text[:50] if link.text else 'No text'}")

                # 링크 모드 확인용 변수
                use_link_mode = False

                print(f"발견된 게시글: {len(articles)}개")

                # 현재 페이지의 게시글 처리
                for idx, article in enumerate(articles[:50], 1):  # 최대 50개까지만
                    try:
                        product_data = {}
                        product_data['board'] = board_info['board']  # 게시판 정보 추가

                        # 공지사항 제외 - 첫 번째 TD에 공지/필독이 있으면 스킵
                        first_td = article.find_element(By.TAG_NAME, "td")
                        if first_td and ("공지" in first_td.text or "필독" in first_td.text):
                            continue

                        # 제목 찾기 - 다음 카페 구조에 맞게
                        title_found = False

                        # TD들을 먼저 찾기
                        tds = article.find_elements(By.TAG_NAME, "td")

                        # 두 번째 TD에 있는 a 태그가 제목 링크 (첫 번째는 필독/공지 표시)
                        if len(tds) >= 2:
                            try:
                                title_elem = tds[1].find_element(By.TAG_NAME, "a")
                                product_data['title'] = title_elem.text.strip()
                                product_data['url'] = title_elem.get_attribute('href')
                                title_found = True
                            except:
                                pass

                        # 대체 방법: a 태그 직접 찾기
                        if not title_found:
                            try:
                                title_elem = article.find_element(By.CSS_SELECTOR, "a[href*='bbs_read']")
                                product_data['title'] = title_elem.text.strip()
                                product_data['url'] = title_elem.get_attribute('href')
                                title_found = True
                            except:
                                product_data['title'] = ''
                                product_data['url'] = ''

                        # 제목이 없으면 스킵
                        if not product_data['title']:
                            continue

                    # 경식 글러브만 필터링 (일단 모든 글러브 수집)
                    # if '연식' in product_data['title'] or '소프트' in product_data['title']:
                    #     continue
                    # if '글러브' not in product_data['title'] and '글럽' not in product_data['title']:
                    #     continue

                    # 판매완료 상품 제외
                    sold_keywords = ['판매완료', '완료', '종료', 'sold', 'SOLD', '거래완료', '판완', '팔림', '예약완료']
                    if any(keyword in product_data['title'] for keyword in sold_keywords):
                        print(f"  ⏭️ 판매완료 상품 스킵: {product_data['title'][:30]}...")
                        continue

                    # 작성자 찾기
                    try:
                        author = article.find_element(By.CSS_SELECTOR, "td.writer").text.strip()
                        product_data['author'] = author
                    except:
                        try:
                            author = article.find_element(By.CSS_SELECTOR, "td.td_writer").text.strip()
                            product_data['author'] = author
                        except:
                            try:
                                # td의 순서로 찾기 (보통 3번째 td)
                                tds = article.find_elements(By.TAG_NAME, "td")
                                if len(tds) >= 3:
                                    product_data['author'] = tds[2].text.strip()
                                else:
                                    product_data['author'] = ''
                            except:
                                product_data['author'] = ''

                    # 작성일 찾기
                    try:
                        date = article.find_element(By.CSS_SELECTOR, "td.date").text.strip()
                        product_data['date'] = date
                    except:
                        try:
                            date = article.find_element(By.CSS_SELECTOR, "td.td_date").text.strip()
                            product_data['date'] = date
                        except:
                            try:
                                # td의 순서로 찾기 (보통 4번째 td)
                                tds = article.find_elements(By.TAG_NAME, "td")
                                if len(tds) >= 4:
                                    product_data['date'] = tds[3].text.strip()
                                else:
                                    product_data['date'] = ''
                            except:
                                product_data['date'] = ''

                    # 조회수 찾기
                    try:
                        views = article.find_element(By.CSS_SELECTOR, "td.view").text.strip()
                        product_data['views'] = views
                    except:
                        try:
                            views = article.find_element(By.CSS_SELECTOR, "td.td_view").text.strip()
                            product_data['views'] = views
                        except:
                            try:
                                # td의 순서로 찾기 (보통 5번째 td)
                                tds = article.find_elements(By.TAG_NAME, "td")
                                if len(tds) >= 5:
                                    product_data['views'] = tds[4].text.strip()
                                else:
                                    product_data['views'] = '0'
                            except:
                                product_data['views'] = '0'

                    # 상세 페이지에서 가격과 이미지 추출
                    price, images = extract_details_from_article(driver, product_data['url'])
                    product_data['price'] = price
                    product_data['images'] = images

                    # 지역 추출
                    location = '미상'
                    location_keywords = ['서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
                                       '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
                    for loc in location_keywords:
                        if loc in product_data['title']:
                            location = loc
                            break
                    product_data['location'] = location

                    # 브랜드 추출
                    brand = extract_brand_from_title(product_data['title'])
                    product_data['brand'] = brand

                    # 포지션 추출
                    position = extract_position_from_title(product_data['title'])
                    product_data['position'] = position

                    # 상태 추출
                    condition = '중고'
                    if '새상품' in title_lower or '신품' in title_lower or '미사용' in title_lower:
                        condition = '신품'
                    product_data['condition'] = condition

                    products.append(product_data)

                    print(f"  [{idx}] {product_data['title'][:40]}...")
                    if price_krw > 0:
                        print(f"      💰 가격: ₩{price_krw:,}")
                    print(f"      📍 지역: {location} | 🏷️ {brand} | 📅 {date}")

                except Exception as e:
                    print(f"  ❌ 게시글 {idx} 파싱 오류: {e}")
                    continue

            # iframe에서 벗어나기
            try:
                driver.switch_to.default_content()
            except:
                pass

    except Exception as e:
        print(f"\n❌ 크롤링 오류: {e}")

    finally:
        # 브라우저 닫기 (사용자가 직접 닫을 때까지 유지)
        # driver.quit()
        print("\n크롤링 완료. 브라우저는 열려 있습니다.")

    # 결과 저장
    if products:
        # 한국 시간으로 타임스탬프 생성
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst)
        timestamp = now.strftime('%Y%m%d_%H%M%S')

        print(f"\n📅 현재 시간: {now.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}")

        # 데이터 디렉토리 생성
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)

        # JSON 파일로 저장 (메타데이터 추가)
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

            # 가격 패턴 찾기 (만원, 원 등)
            price_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*만원',
                r'(\d{1,3}(?:,\d{3})*)\s*원',
                r'가격[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'판매가[:\s]*(\d{1,3}(?:,\d{3})*)',
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, content_text)
                if matches:
                    price_str = matches[0].replace(',', '')
                    price = int(price_str)
                    # 만원 단위면 10000 곱하기
                    if '만원' in content_text:
                        price *= 10000
                    break

        except Exception as e:
            print(f"    가격 추출 실패: {e}")

        # 이미지 추출
        try:
            # 여러 이미지 셀렉터 시도
            image_selectors = [
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

def collect_articles(driver, articles, board_name):
    """게시글 수집 함수 - step9 로직 사용"""
    products = []

    for idx, article in enumerate(articles[:10], 1):  # 테스트를 위해 10개만
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
            title_lower = product_data['title'].lower()
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

def extract_brand_from_title(title):
    """제목에서 브랜드 추출"""
    brands = {
        '미즈노': 'Mizuno',
        'mizuno': 'Mizuno',
        'MIZUNO': 'Mizuno',
        '윌슨': 'Wilson',
        'wilson': 'Wilson',
        'WILSON': 'Wilson',
        '롤링스': 'Rawlings',
        'rawlings': 'Rawlings',
        'RAWLINGS': 'Rawlings',
        '제트': 'ZETT',
        'zett': 'ZETT',
        'ZETT': 'ZETT',
        'SSK': 'SSK',
        'ssk': 'SSK',
        '아톰즈': 'ATOMS',
        'atoms': 'ATOMS',
        'ATOMS': 'ATOMS',
        '아식스': 'ASICS',
        'asics': 'ASICS',
        'ASICS': 'ASICS',
        '나이키': 'Nike',
        'nike': 'Nike',
        'NIKE': 'Nike',
        '아디다스': 'Adidas',
        'adidas': 'Adidas',
        '언더아머': 'Under Armour',
        'under armour': 'Under Armour',
        'underarmour': 'Under Armour',
        '44': '44글러브',
        'IP': 'IP Select',
        '아이피': 'IP Select',
    }

    title_lower = title.lower()
    for keyword, brand_name in brands.items():
        if keyword.lower() in title_lower:
            return brand_name

    return '기타'

def extract_position_from_title(title):
    """제목에서 포지션 추출"""
    positions = {
        '내야': '내야수',
        '외야': '외야수',
        '투수': '투수',
        '포수': '포수',
        '올라운드': '올라운드',
        '유격수': '내야수',
        '2루수': '내야수',
        '3루수': '내야수',
        '1루수': '내야수',
    }

    for keyword, position_name in positions.items():
        if keyword in title:
            return position_name

    return '올라운드'

if __name__ == "__main__":
    # 사용자 디렉토리 설정
    import sys
    user_dir = sys.argv[1] if len(sys.argv) > 1 else './'

    products = search_yayongsa_gloves(user_dir)
    print(f"\n총 {len(products)}개의 야용사 상품을 수집했습니다.")