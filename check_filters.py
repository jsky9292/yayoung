import json

# 최신 파일 읽기
with open('data/yahoo_auction_20250928_191547.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

products = data['products'][:5]  # 처음 5개만

print("제품 데이터 구조 확인:")
for i, p in enumerate(products, 1):
    print(f"\n제품 {i}:")
    print(f"  position: {p.get('position', '없음')}")
    print(f"  condition: {p.get('condition', '없음')}")
    print(f"  brand: {p.get('brand', '없음')}")
    print(f"  market: {p.get('market', '없음')}")

# 필터 값들 확인
positions = set()
conditions = set()
brands = set()

for p in data['products']:
    if p.get('position'):
        positions.add(p.get('position'))
    if p.get('condition'):
        conditions.add(p.get('condition'))
    if p.get('brand'):
        brands.add(p.get('brand'))

print("\n\n필터 값들:")
print(f"포지션: {positions}")
print(f"상태: {conditions}")
print(f"브랜드 (상위 10개): {list(brands)[:10]}")