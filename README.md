# 글러브 마켓 크롤러 시스템

야구 글러브 시장 분석을 위한 크롤링 및 대시보드 시스템

## 🚀 빠른 시작

```bash
python simple_run.py
```

## 📁 파일 구조

```
yayoung/
├── data/                   # 크롤링 데이터 저장
├── dashboards/            # 생성된 대시보드 HTML
├── users/                 # 사용자별 데이터
├── config.py              # 설정 파일 (카카오 로그인 정보)
├── simple_run.py          # 간단 실행 메뉴
├── main_app.py            # 웹 애플리케이션
├── yahoo_crawler.py       # Yahoo Auction 크롤러
├── yayongsa_crawler.py    # 야용사 카페 크롤러
└── update_dashboard.py    # 대시보드 업데이트

```

## 🔧 주요 기능

1. **웹 애플리케이션**
   - 로그인 시스템 (admin/admin123)
   - 실시간 대시보드
   - 크롤링 관리

2. **Yahoo Auction 크롤링**
   - 자동 크롤링
   - 환율 적용 (1엔 = 9.2원)
   - 포지션/브랜드/가격 분석

3. **야용사 카페 크롤링**
   - 수동 로그인 방식
   - 중고글러브벼룩시장 게시판
   - 가격/포지션 자동 추출

4. **통합 대시보드**
   - 실시간 통계
   - 차트 시각화
   - 제품 링크 연동

## 📊 현재 데이터
- Yahoo: 1,215개 상품
- 야용사: 수동 크롤링 가능

## 💻 실행 방법

### 메뉴 시스템
```bash
python simple_run.py
# 1. 웹 서버 실행
# 2. Yahoo 크롤링
# 3. 야용사 크롤링
# 4. 대시보드 업데이트
```

### 개별 실행
```bash
python main_app.py          # 웹 서버
python yahoo_crawler.py     # Yahoo 크롤링
python update_dashboard.py  # 대시보드 생성
```

## 🌐 웹 접속
http://localhost:5000
- ID: admin
- PW: admin123