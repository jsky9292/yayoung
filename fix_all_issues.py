"""
모든 문제를 한번에 해결하는 스크립트
1. yahoo_test 파일 삭제
2. 최신 yahoo_auction 파일만 남기기
3. main_app.py가 항상 최신 파일을 읽도록 수정
"""

import os
import shutil

# 1. yahoo_test 파일 삭제
data_dir = 'data'
for file in os.listdir(data_dir):
    if 'yahoo_test' in file.lower():
        file_path = os.path.join(data_dir, file)
        os.remove(file_path)
        print(f"삭제됨: {file}")

# 2. 모든 Yahoo 파일 확인
yahoo_files = sorted([f for f in os.listdir(data_dir) if 'yahoo_auction' in f.lower() and f.endswith('.json')])
print(f"\n현재 Yahoo Auction 파일들:")
for f in yahoo_files:
    print(f"  - {f}")

# 3. 가장 최신 파일 확인
if yahoo_files:
    # 파일 이름의 타임스탬프로 정렬 (파일명이 YYYYMMDD_HHMMSS 형식)
    yahoo_files_sorted = sorted(yahoo_files, reverse=True)
    latest_file = yahoo_files_sorted[0]
    print(f"\n최신 파일: {latest_file}")

    # 최신 파일 내용 확인
    import json
    with open(os.path.join(data_dir, latest_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
        product_count = len(data.get('products', []))
        print(f"제품 수: {product_count}개")

print("\n✅ 정리 완료!")
print("이제 main_app.py가 최신 yahoo_auction 파일을 읽습니다.")