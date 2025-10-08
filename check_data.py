import json

# 최신 데이터 파일 읽기
with open('data/yahoo_auction_20250928_190949.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 통계 계산
brands = {}
positions = {}
conditions = {}

for p in data['products']:
    # 브랜드
    b = p.get('brand', 'その他')
    brands[b] = brands.get(b, 0) + 1

    # 포지션
    pos = p.get('position', '올라운드')
    positions[pos] = positions.get(pos, 0) + 1

    # 상태
    cond = p.get('condition', '중고')
    conditions[cond] = conditions.get(cond, 0) + 1

# 결과 출력
print(f"🎌 Yahoo Auction 크롤링 결과")
print(f"총 {len(data['products'])}개 제품 수집")
print()

print("📊 브랜드 분포:")
for k, v in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {k}: {v}개")

print("\n⚾ 포지션 분포:")
for k, v in sorted(positions.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k}: {v}개")

print("\n📦 상태 분포:")
for k, v in sorted(conditions.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k}: {v}개")

# 가격 분포
prices = [p.get('current_price', 0) for p in data['products']]
print(f"\n💴 가격 분포:")
print(f"  최저가: ¥{min(prices):,}")
print(f"  최고가: ¥{max(prices):,}")
print(f"  평균가: ¥{sum(prices)//len(prices):,}")