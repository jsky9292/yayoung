# Yahoo Auction Japan 크롤러
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import re
from datetime import datetime
import requests
import pytz

def setup_driver():
    """드라이버 설정 - 크롬 창 자동 열기"""
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-notifications')

    # 크롬 창이 항상 표시되도록 설정
    options.add_argument('--start-maximized')  # 창 최대화로 시작
    options.add_argument('--disable-gpu')  # GPU 가속 비활성화 (안정성)
    options.add_argument('--no-sandbox')  # 샌드박스 비활성화 (Windows 호환성)

    # User-Agent 설정 (일본 사이트 접속용)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver

def search_yahoo_auction(driver, keyword="", days=0, max_pages=3):
    """야후 옥션 검색 - 여러 페이지 크롤링

    Args:
        driver: 웹드라이버
        keyword: 검색 키워드 (비어있으면 카테고리 전체)
        days: 크롤링 기간 (0=전체, 1=오늘, 3=3일이내, 7=7일이내, 30=30일이내)
        max_pages: 크롤링할 최대 페이지 수
    """
    products = []

    try:
        # Yahoo Auction 야구 글러브 카테고리 직접 접근
        # 2084032394 = 야구 글러브 카테고리
        # 키워드 검색 없이 카테고리 페이지에서 직접 가져오기
        base_url = "https://auctions.yahoo.co.jp/category/list/2084032394/?n=100"

        # 날짜 필터 추가
        date_text = "전체 기간"
        if days > 0:
            if days == 1:
                base_url += "&new=1"  # 신규 출품 (24시간 이내)
                date_text = "오늘 (24시간 이내)"
            elif days == 3:
                base_url += "&etime=3"
                date_text = "3일 이내"
            elif days == 7:
                base_url += "&etime=7"
                date_text = "7일 이내"
            elif days == 30:
                date_text = "30일 이내"

        print(f"🔍 검색 중: {keyword}")
        print(f"📅 크롤링 기간: {date_text}")
        print(f"📄 최대 {max_pages}페이지까지 크롤링")

        # 여러 페이지 크롤링
        for page_num in range(1, max_pages + 1):
            # 페이지 URL 생성
            if page_num == 1:
                url = base_url
            else:
                # 페이지네이션: b 파라미터 사용 (100개씩)
                offset = (page_num - 1) * 100 + 1
                if '?' in base_url:
                    url = f"{base_url}&b={offset}"
                else:
                    url = f"{base_url}?b={offset}"

            print(f"\n📖 {page_num}페이지 크롤링 중...")
            print(f"   URL: {url}")

            driver.get(url)
            time.sleep(3)

            # 상품 목록 가져오기
            try:
                product_elements = driver.find_elements(By.CSS_SELECTOR, ".Product")
                if not product_elements:
                    product_elements = driver.find_elements(By.CSS_SELECTOR, "li.Product__item")

                print(f"   ✅ {len(product_elements)}개 상품 발견")

                if not product_elements:
                    print("   ⚠️ 더 이상 상품이 없습니다.")
                    break

                for idx, element in enumerate(product_elements, 1):
                    try:
                        product_data = {}

                        # 상품명
                        try:
                            title_elem = element.find_element(By.CSS_SELECTOR, ".Product__title")
                            product_data['title'] = title_elem.text.strip()
                        except:
                            product_data['title'] = ''

                        if not product_data['title']:
                            continue

                        title = product_data['title']
                        title_lower = title.lower()

                        # 가격
                        try:
                            price_elem = element.find_element(By.CSS_SELECTOR, ".Product__priceValue")
                            price_text = price_elem.text.strip()
                            price_text = price_text.replace(',', '').replace('円', '').replace('¥', '').replace(' ', '')
                            product_data['current_price'] = int(price_text) if price_text.isdigit() else 0
                        except:
                            product_data['current_price'] = 0

                        # 이미지
                        try:
                            img_elem = element.find_element(By.CSS_SELECTOR, "img.Product__imageData")
                            product_data['image_url'] = img_elem.get_attribute('src')
                        except:
                            product_data['image_url'] = ''

                        # URL
                        try:
                            link_elem = element.find_element(By.CSS_SELECTOR, "a.Product__titleLink")
                            product_data['url'] = link_elem.get_attribute('href')
                        except:
                            product_data['url'] = ''

                        # 입찰 수
                        try:
                            bid_elem = element.find_element(By.CSS_SELECTOR, ".Product__bid")
                            product_data['bids'] = bid_elem.text.strip()
                        except:
                            product_data['bids'] = '0'

                        # 남은 시간
                        try:
                            time_elem = element.find_element(By.CSS_SELECTOR, ".Product__time")
                            product_data['time_left'] = time_elem.text.strip()
                        except:
                            product_data['time_left'] = ''

                        # === 필터링 ===

                        # 1. 반드시 글러브 키워드가 있어야 함
                        glove_keywords = ['グローブ', 'グラブ', 'ミット', 'glove', 'Glove']
                        if not any(keyword in title for keyword in glove_keywords):
                            continue

                        # 2. 확실한 액세서리 제외
                        exclude_keywords = [
                            # 오일/왁스 단품
                            'スクワランオイル', 'ミンクオイル', 'メンテナンスオイル',
                            '艶出し', 'みつろう', 'ワックス',
                            # 끈 단품
                            'レースのみ', '紐のみ', 'グラブレース単品',
                            # 도구
                            'グラブピン', '紐通し', 'ニードル', '修理用',
                            # 타격 장갑
                            'バッティンググローブ', 'バッティング手袋', '守備用手袋',
                            # 기타
                            'サングラス', 'アームガード', '芯材のみ'
                        ]

                        # 확실한 액세서리는 제외
                        if any(keyword in title for keyword in exclude_keywords):
                            continue

                        # 3. 가격 필터 (3000엔 이상의 진짜 글러브만)
                        if product_data['current_price'] < 3000:
                            continue

                        # 3. 판매완료/종료 상품 제외
                        sold_keywords = ['終了', '売り切れ', '完売', 'SOLD', '落札', '売却済']
                        if any(word in title for word in sold_keywords):
                            continue

                        # 4. 남은시간 확인
                        time_left = product_data.get('time_left', '')
                        if time_left and any(term in time_left for term in ['終了', '落札']):
                            continue

                        # === 데이터 추출 ===

                        # 브랜드 추출
                        product_data['brand'] = extract_brand_from_title(title)

                        # 상태
                        if any(word in title for word in ['新品', '未使用', 'NEW']):
                            product_data['condition'] = '신품'
                        else:
                            product_data['condition'] = '중고'

                        # 포지션 (더 정확한 판별)
                        if any(word in title for word in ['投手', 'ピッチャー', 'pitcher', 'Pitcher']):
                            product_data['position'] = '투수'
                        elif any(word in title for word in ['捕手', 'キャッチャー', 'ミット', 'catcher', 'Catcher']):
                            product_data['position'] = '포수'
                        elif any(word in title for word in ['内野', '二塁', '三塁', '一塁', 'ショート', 'セカンド', 'サード', 'ファースト', 'infield']):
                            product_data['position'] = '내야수'
                        elif any(word in title for word in ['外野', 'アウトフィールド', 'outfield', 'Outfield']):
                            product_data['position'] = '외야수'
                        elif any(word in title for word in ['オールラウンド', 'オールポジション', 'all-round']):
                            product_data['position'] = '올라운드'
                        else:
                            # 기본값은 올라운드
                            product_data['position'] = '올라운드'

                        # 연령대
                        if any(word in title for word in ['キッズ', '少年', 'ジュニア', '子供']):
                            product_data['age_group'] = '어린이용'
                        elif any(word in title for word in ['大人', '一般', '成人', 'プロ']):
                            product_data['age_group'] = '성인용'
                        else:
                            product_data['age_group'] = '성인용'

                        # 원화 환산
                        exchange_rate = 9.2
                        product_data['price_krw'] = int(product_data['current_price'] * exchange_rate)
                        product_data['exchange_rate'] = exchange_rate

                        # 배송비 계산
                        weight_kg = 0.6  # 글러브 평균 무게
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

                        products.append(product_data)

                        # 출력
                        print(f"  [{page_num}-{idx}] (총 {len(products)}개) {title[:35]}...")
                        print(f"      💴 ¥{product_data['current_price']:,} (≈ ₩{product_data['price_krw']:,})")
                        print(f"      📦 {product_data['brand']} | {product_data['condition']} | {product_data['position']}")

                    except Exception as e:
                        continue

                # 상품이 100개 미만이면 마지막 페이지
                if len(product_elements) < 100:
                    print("\n📌 마지막 페이지입니다.")
                    break

            except Exception as e:
                print(f"❌ 페이지 {page_num} 오류: {e}")
                break

    except Exception as e:
        print(f"❌ 검색 오류: {e}")

    return products

def extract_brand_from_title(title):
    """제목에서 브랜드 추출"""
    brands = {
        'ミズノ': 'Mizuno', 'mizuno': 'Mizuno', 'MIZUNO': 'Mizuno',
        'ウィルソン': 'Wilson', 'wilson': 'Wilson', 'WILSON': 'Wilson',
        'ローリングス': 'Rawlings', 'rawlings': 'Rawlings', 'RAWLINGS': 'Rawlings',
        'ゼット': 'ZETT', 'zett': 'ZETT', 'ZETT': 'ZETT',
        'SSK': 'SSK',
        'アシックス': 'ASICS', 'asics': 'ASICS', 'ASICS': 'ASICS',
        '久保田': 'Kubota Slugger', 'kubota': 'Kubota Slugger',
        'ハタケヤマ': 'Hatakeyama',
        'アトムズ': 'ATOMS', 'atoms': 'ATOMS',
        'ザナックス': 'Xanax', 'xanax': 'Xanax',
        'アイピーセレクト': 'IP Select', 'ip select': 'IP Select',
        'デサント': 'Descente', 'descente': 'Descente',
        'アンダーアーマー': 'Under Armour', 'under armour': 'Under Armour', 'UA': 'Under Armour'
    }

    title_lower = title.lower() if title else ''

    for key, brand in brands.items():
        if key.lower() in title_lower:
            return brand

    return 'その他'

def save_yahoo_data(products):
    """데이터 저장"""
    # 한국 시간으로 설정
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    timestamp = now.strftime('%Y%m%d_%H%M%S')

    print(f"\n📅 현재 시간: {now.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}")

    # data 디렉토리 생성
    if not os.path.exists('data'):
        os.makedirs('data')

    # JSON 파일로 저장
    filename = f"data/yahoo_auction_{timestamp}.json"

    # 메타데이터 추가
    data = {
        'crawled_at': now.isoformat(),
        'crawled_date': now.strftime('%Y-%m-%d'),
        'crawled_time': now.strftime('%H:%M:%S'),
        'total_count': len(products),
        'products': products
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 데이터 저장: {filename}")

    # 이미지 다운로드 폴더 생성
    img_folder = f"data/yahoo_images_{timestamp}"
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)

    # 이미지 다운로드 (선택적)
    print(f"\n📷 이미지 다운로드 중...")
    for idx, product in enumerate(products[:20], 1):  # 처음 20개만
        if product.get('image_url'):
            try:
                response = requests.get(product['image_url'], timeout=5)
                if response.status_code == 200:
                    img_filename = f"{img_folder}/product_{idx}.jpg"
                    with open(img_filename, 'wb') as f:
                        f.write(response.content)
                    product['local_image'] = img_filename
            except:
                pass

    return filename, img_folder

def main():
    print("="*70)
    print("🎌 Yahoo Auction Japan 글러브 크롤러")
    print("="*70)

    driver = setup_driver()

    try:
        # 카테고리 페이지 직접 크롤링 (키워드 검색 대신)
        print("\n🔍 야후옥션 야구 글러브 카테고리 크롤링")
        print("📌 카테고리: 野球 > グローブ (2084032394)")

        # 카테고리에서 직접 크롤링 (키워드 없이)
        all_products = search_yahoo_auction(driver, keyword="", days=0, max_pages=5)  # 5페이지 크롤링
        print(f"   📊 총 {len(all_products)}개 수집")

        # 중복 제거
        unique_products = []
        seen_titles = set()
        for product in all_products:
            if product['title'] not in seen_titles:
                unique_products.append(product)
                seen_titles.add(product['title'])

        print(f"\n📊 수집 결과:")
        print(f"  총 {len(unique_products)}개 상품 (중복 제거)")

        if unique_products:
            # 상태별 분류
            new_products = [p for p in unique_products if p['condition'] == '신품']
            used_products = [p for p in unique_products if p['condition'] == '중고']

            print(f"\n📦 상태별 분류:")
            print(f"  신품: {len(new_products)}개")
            print(f"  중고: {len(used_products)}개")

            # 브랜드별 통계
            brand_stats = {}
            for product in unique_products:
                brand = product['brand']
                if brand not in brand_stats:
                    brand_stats[brand] = {'count': 0, 'total_price': 0}
                brand_stats[brand]['count'] += 1
                brand_stats[brand]['total_price'] += product['current_price']

            print("\n🏷️ 브랜드별 분포:")
            for brand, stats in sorted(brand_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
                avg_price = stats['total_price'] / stats['count'] if stats['count'] > 0 else 0
                print(f"  {brand}: {stats['count']}개 (평균 ¥{avg_price:,.0f})")

            # 데이터 저장
            filename, img_folder = save_yahoo_data(unique_products)

            print(f"\n✅ 크롤링 완료!")
            print(f"  데이터: {filename}")
            print(f"  이미지: {img_folder}/")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

    finally:
        print("\n10초 후 브라우저가 닫힙니다...")
        time.sleep(10)
        driver.quit()
        print("✅ 종료")

if __name__ == "__main__":
    main()