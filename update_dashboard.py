#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
통합 대시보드 업데이트 스크립트
모든 크롤링 데이터를 수집하여 통합 대시보드 생성
"""

import json
import os
import glob
from datetime import datetime
from collections import defaultdict

def update_integrated_dashboard():
    """모든 JSON 파일의 데이터를 통합하여 대시보드 생성"""

    print("="*60)
    print("📊 통합 대시보드 업데이트")
    print("="*60)

    # 모든 Yahoo 데이터 수집
    yahoo_data = []
    yayongsa_data = []

    # 모든 위치에서 Yahoo 데이터 파일 찾기
    yahoo_patterns = [
        'yahoo_auction_*.json',
        'users/*/yahoo_auction_*.json',
        'users/*/data/yahoo_auction_*.json',
        'data/yahoo_auction_*.json'
    ]

    yahoo_files = []
    for pattern in yahoo_patterns:
        yahoo_files.extend(glob.glob(pattern, recursive=False))

    # 중복 제거
    yahoo_files = list(set(yahoo_files))

    print(f"\n📁 발견된 Yahoo 파일: {len(yahoo_files)}개")

    # 모든 Yahoo 파일 데이터 로드
    for file_path in yahoo_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    yahoo_data.extend(file_data)
                    print(f"  ✅ {os.path.basename(file_path)}: {len(file_data)}개 상품")
        except Exception as e:
            print(f"  ❌ {os.path.basename(file_path)} 로드 실패: {e}")

    # 야용사 데이터 파일 찾기
    yayongsa_patterns = [
        'yayongsa_*.json',
        'glove_data_*.json',
        'sample_yayongsa_data.json',
        'users/*/yayongsa_*.json',
        'users/*/data/yayongsa_*.json',
        'users/*/data/glove_data_*.json'
    ]

    yayongsa_files = []
    for pattern in yayongsa_patterns:
        yayongsa_files.extend(glob.glob(pattern, recursive=False))

    yayongsa_files = list(set(yayongsa_files))

    print(f"\n📁 발견된 야용사 파일: {len(yayongsa_files)}개")

    # 모든 야용사 파일 데이터 로드
    for file_path in yayongsa_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    yayongsa_data.extend(file_data)
                    print(f"  ✅ {os.path.basename(file_path)}: {len(file_data)}개 상품")
        except Exception as e:
            print(f"  ❌ {os.path.basename(file_path)} 로드 실패: {e}")

    print(f"\n📊 총계:")
    print(f"  Yahoo: {len(yahoo_data)}개 상품")
    print(f"  야용사: {len(yayongsa_data)}개 상품")
    print(f"  전체: {len(yahoo_data) + len(yayongsa_data)}개 상품")

    # 통계 계산
    yahoo_stats = calculate_stats(yahoo_data, 'yahoo')
    yayongsa_stats = calculate_stats(yayongsa_data, 'yayongsa')

    # HTML 대시보드 생성
    html_content = generate_dashboard_html(yahoo_data, yayongsa_data, yahoo_stats, yayongsa_stats)

    # 파일 저장
    os.makedirs('dashboards', exist_ok=True)
    dashboard_file = 'dashboards/integrated_full.html'

    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ 대시보드 생성 완료: {dashboard_file}")

    # admin 사용자 폴더에도 복사
    admin_dashboard_dir = 'users/admin/dashboards'
    if os.path.exists('users/admin'):
        os.makedirs(admin_dashboard_dir, exist_ok=True)
        admin_dashboard_file = f'{admin_dashboard_dir}/integrated_full.html'
        with open(admin_dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Admin 대시보드 업데이트: {admin_dashboard_file}")

    return dashboard_file

def calculate_stats(data, source):
    """데이터 통계 계산"""
    stats = {
        'total': len(data),
        'positions': defaultdict(int),
        'brands': defaultdict(int),
        'conditions': defaultdict(int),
        'price_ranges': defaultdict(int),
        'avg_price': 0
    }

    if not data:
        return stats

    total_price = 0
    valid_price_count = 0

    for item in data:
        # 포지션
        position = item.get('position', '올라운드')
        stats['positions'][position] += 1

        # 브랜드
        brand = item.get('brand', '기타')
        if brand and brand != 'unknown':
            stats['brands'][brand] += 1

        # 상태
        condition = item.get('condition', '미분류')
        stats['conditions'][condition] += 1

        # 가격
        if source == 'yahoo':
            price = item.get('total_cost_krw', 0)
        else:
            price = item.get('price', 0)

        if price > 0:
            total_price += price
            valid_price_count += 1

            # 가격대
            if price <= 100000:
                price_range = '~10만원'
            elif price <= 300000:
                price_range = '10~30만원'
            elif price <= 500000:
                price_range = '30~50만원'
            else:
                price_range = '50만원~'
            stats['price_ranges'][price_range] += 1

    if valid_price_count > 0:
        stats['avg_price'] = total_price / valid_price_count

    return stats

def generate_dashboard_html(yahoo_data, yayongsa_data, yahoo_stats, yayongsa_stats):
    """대시보드 HTML 생성"""

    # 상위 브랜드 추출
    top_yahoo_brands = dict(sorted(yahoo_stats['brands'].items(), key=lambda x: x[1], reverse=True)[:5])
    top_yayongsa_brands = dict(sorted(yayongsa_stats['brands'].items(), key=lambda x: x[1], reverse=True)[:5])

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>글러브 마켓 통합 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Noto Sans KR', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .dashboard {{
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}

        .summary-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}

        .summary-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}

        .summary-value {{
            font-size: 2.2em;
            font-weight: bold;
        }}

        .market-section {{
            margin-bottom: 40px;
        }}

        .market-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}

        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .chart-title {{
            font-weight: bold;
            color: #555;
            margin-bottom: 10px;
            text-align: center;
        }}

        canvas {{
            max-height: 250px !important;
        }}

        .products-section {{
            margin-top: 40px;
        }}

        .products-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .product-card {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 150px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .product-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            border-color: #667eea;
        }}

        .product-title {{
            font-weight: bold;
            margin-bottom: 10px;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            line-height: 1.3;
            min-height: 2.6em;
        }}

        .product-price {{
            color: #667eea;
            font-size: 1.3em;
            font-weight: bold;
            margin: 8px 0;
        }}

        .product-info {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
            border-top: 1px solid #f0f0f0;
            padding-top: 8px;
        }}

        .timestamp {{
            text-align: center;
            color: #999;
            margin-top: 30px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>⚾ 글러브 마켓 통합 대시보드</h1>

        <!-- 요약 섹션 -->
        <div class="summary-section">
            <div class="summary-card">
                <div class="summary-label">Yahoo 상품</div>
                <div class="summary-value">{yahoo_stats['total']:,}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">야용사 상품</div>
                <div class="summary-value">{yayongsa_stats['total']:,}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">전체 상품</div>
                <div class="summary-value">{yahoo_stats['total'] + yayongsa_stats['total']:,}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Yahoo 평균가</div>
                <div class="summary-value">₩{int(yahoo_stats['avg_price']):,}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">야용사 평균가</div>
                <div class="summary-value">₩{int(yayongsa_stats['avg_price']):,}</div>
            </div>
        </div>

        <!-- Yahoo Auction 섹션 -->
        <div class="market-section">
            <h2 class="market-title">🇯🇵 Yahoo Auction Japan ({yahoo_stats['total']}개)</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">포지션별 분포</div>
                    <canvas id="yahooPosition"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">가격대 분포</div>
                    <canvas id="yahooPrice"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">상태별 분포</div>
                    <canvas id="yahooCondition"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">브랜드 TOP 5</div>
                    <canvas id="yahooBrand"></canvas>
                </div>
            </div>
        </div>

        <!-- 야용사 섹션 -->
        <div class="market-section">
            <h2 class="market-title">🇰🇷 야용사 카페 ({yayongsa_stats['total']}개)</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">포지션별 분포</div>
                    <canvas id="yayongsaPosition"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">가격대 분포</div>
                    <canvas id="yayongsaPrice"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">상태별 분포</div>
                    <canvas id="yayongsaCondition"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">브랜드 TOP 5</div>
                    <canvas id="yayongsaBrand"></canvas>
                </div>
            </div>
        </div>

        <!-- 상품 미리보기 -->
        <div class="products-section">
            <h2 class="market-title">📦 최근 상품 미리보기</h2>
            <div class="products-grid">
"""

    # Yahoo 상품 카드 (최신순으로 정렬 후 최대 8개)
    # 타임스탬프가 있으면 정렬, 없으면 역순으로
    sorted_yahoo = sorted(yahoo_data, key=lambda x: x.get('timestamp', ''), reverse=True) if yahoo_data else []

    for item in sorted_yahoo[:8]:
        # 엔화 가격 사용 (1엔 = 약 9.2원)
        price_yen = item.get('current_price', 0)
        # total_cost_krw에는 배송비 포함된 가격이 있을 수 있음
        price_krw = item.get('total_cost_krw', 0)
        if not price_krw and price_yen:
            price_krw = price_yen * 9.2  # 환율 적용
        position = item.get('position', '올라운드')
        brand = item.get('brand', '기타')
        condition = item.get('condition', '미분류')

        html_content += f"""
                <div class="product-card" onclick="window.open('{item.get('url', '#')}', '_blank')">
                    <div class="product-title">{item.get('title', '')[:40]}...</div>
                    <div class="product-price">¥{price_yen:,}</div>
                    <div class="product-info" style="font-size: 0.85em; color: #888;">약 ₩{int(price_krw):,}</div>
                    <div class="product-info">Yahoo | {position} | {brand} | {condition}</div>
                </div>
"""

    # 야용사 상품 카드 (최신순으로 정렬 후 최대 4개)
    sorted_yayongsa = sorted(yayongsa_data, key=lambda x: x.get('date', ''), reverse=True) if yayongsa_data else []

    for item in sorted_yayongsa[:4]:
        price = item.get('price', 0)
        position = item.get('position', '올라운드')
        condition = item.get('condition', '중고')

        html_content += f"""
                <div class="product-card" onclick="window.open('{item.get('url', '#')}', '_blank')">
                    <div class="product-title">{item.get('title', '')[:40]}...</div>
                    <div class="product-price">₩{price:,}</div>
                    <div class="product-info" style="margin-top: 10px;">야용사 | {position} | {condition}</div>
                </div>
"""

    html_content += f"""
            </div>
        </div>

        <div class="timestamp">
            업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>

    <script>
        // Chart.js 기본 설정
        Chart.defaults.plugins.legend.position = 'bottom';

        // Yahoo 포지션 차트
        new Chart(document.getElementById('yahooPosition'), {{
            type: 'doughnut',
            data: {{
                labels: {list(yahoo_stats['positions'].keys())},
                datasets: [{{
                    data: {list(yahoo_stats['positions'].values())},
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
                }}]
            }}
        }});

        // Yahoo 가격대 차트
        new Chart(document.getElementById('yahooPrice'), {{
            type: 'bar',
            data: {{
                labels: ['~10만원', '10~30만원', '30~50만원', '50만원~'],
                datasets: [{{
                    label: '상품 수',
                    data: [{yahoo_stats['price_ranges'].get('~10만원', 0)},
                           {yahoo_stats['price_ranges'].get('10~30만원', 0)},
                           {yahoo_stats['price_ranges'].get('30~50만원', 0)},
                           {yahoo_stats['price_ranges'].get('50만원~', 0)}],
                    backgroundColor: '#667eea'
                }}]
            }},
            options: {{
                scales: {{ y: {{ beginAtZero: true }} }}
            }}
        }});

        // Yahoo 상태 차트
        new Chart(document.getElementById('yahooCondition'), {{
            type: 'pie',
            data: {{
                labels: {list(yahoo_stats['conditions'].keys())},
                datasets: [{{
                    data: {list(yahoo_stats['conditions'].values())},
                    backgroundColor: ['#4BC0C0', '#FFCE56', '#FF6384']
                }}]
            }}
        }});

        // Yahoo 브랜드 차트
        new Chart(document.getElementById('yahooBrand'), {{
            type: 'doughnut',
            data: {{
                labels: {list(top_yahoo_brands.keys())},
                datasets: [{{
                    data: {list(top_yahoo_brands.values())},
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
                }}]
            }}
        }});

        // 야용사 포지션 차트
        new Chart(document.getElementById('yayongsaPosition'), {{
            type: 'doughnut',
            data: {{
                labels: {list(yayongsa_stats['positions'].keys())},
                datasets: [{{
                    data: {list(yayongsa_stats['positions'].values())},
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
                }}]
            }}
        }});

        // 야용사 가격대 차트
        new Chart(document.getElementById('yayongsaPrice'), {{
            type: 'bar',
            data: {{
                labels: ['~10만원', '10~30만원', '30~50만원', '50만원~'],
                datasets: [{{
                    label: '상품 수',
                    data: [{yayongsa_stats['price_ranges'].get('~10만원', 0)},
                           {yayongsa_stats['price_ranges'].get('10~30만원', 0)},
                           {yayongsa_stats['price_ranges'].get('30~50만원', 0)},
                           {yayongsa_stats['price_ranges'].get('50만원~', 0)}],
                    backgroundColor: '#764ba2'
                }}]
            }},
            options: {{
                scales: {{ y: {{ beginAtZero: true }} }}
            }}
        }});

        // 야용사 상태 차트
        new Chart(document.getElementById('yayongsaCondition'), {{
            type: 'pie',
            data: {{
                labels: {list(yayongsa_stats['conditions'].keys())},
                datasets: [{{
                    data: {list(yayongsa_stats['conditions'].values())},
                    backgroundColor: ['#4BC0C0', '#FFCE56', '#FF6384']
                }}]
            }}
        }});

        // 야용사 브랜드 차트
        new Chart(document.getElementById('yayongsaBrand'), {{
            type: 'doughnut',
            data: {{
                labels: {list(top_yayongsa_brands.keys())},
                datasets: [{{
                    data: {list(top_yayongsa_brands.values())},
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
                }}]
            }}
        }});
    </script>
</body>
</html>
"""

    return html_content

if __name__ == "__main__":
    dashboard_file = update_integrated_dashboard()
    import webbrowser
    webbrowser.open(f'file:///{os.path.abspath(dashboard_file)}')