#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
글러브 마켓 크롤러 웹 애플리케이션
사용자 관리, 권한 시스템, 크롤링 인터페이스 제공
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import pandas as pd
from io import BytesIO
import xlsxwriter

# 한국 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))

def get_kst_now():
    return datetime.now(KST)
import os
import json
import secrets
import threading
import subprocess
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 데이터베이스 모델
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    kakao_id = db.Column(db.String(200))
    kakao_password = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(KST))
    last_crawl = db.Column(db.DateTime)
    crawl_count = db.Column(db.Integer, default=0)

class CrawlHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')
    item_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(KST))
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

# 데이터베이스 초기화
with app.app_context():
    db.create_all()
    # 기본 관리자 계정 생성 (더 강력한 비밀번호)
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@glovemarket.com',
            password=generate_password_hash('admin123'),  # 비밀번호
            is_admin=True,
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ 관리자 계정 생성 완료")
        print("   ID: admin")
        print("   PW: admin123")
        print("   로그인 정보: admin / admin123")

# 로그인 필요 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 관리자 권한 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('관리자 권한이 필요합니다.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# 승인된 사용자 데코레이터
def approved_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_approved:
            flash('관리자 승인을 기다려주세요.', 'info')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# 라우트
@app.route('/')
def index():
    """메인 페이지"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """회원가입"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # 중복 확인
        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 사용자명입니다.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('이미 등록된 이메일입니다.', 'danger')
            return render_template('register.html')

        # 사용자 생성
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_approved=False  # 관리자 승인 대기
        )
        db.session.add(user)
        db.session.commit()

        flash('회원가입이 완료되었습니다. 관리자 승인을 기다려주세요.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'환영합니다, {user.username}님!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard/products')
@login_required
def dashboard_products():
    """크롤링 제품 대시보드"""
    user = User.query.get(session['user_id'])
    products = []

    # 소스 필터링 파라미터 가져오기
    source_filter = request.args.get('source', 'all').lower()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')

    yahoo_count = 0
    yayongsa_count = 0
    yahoo_avg = 0
    yayongsa_avg = 0

    # 모든 JSON 파일 처리
    if os.path.exists(data_dir):
        # 가장 최신 Yahoo 파일 찾기 (yahoo_auction 파일만 선택, yahoo_test 제외)
        yahoo_files = sorted([f for f in os.listdir(data_dir) if 'yahoo_auction' in f.lower() and f.endswith('.json')], reverse=True)
        yayongsa_files = sorted([f for f in os.listdir(data_dir) if 'yayongsa' in f.lower() and f.endswith('.json')], reverse=True)

        # Yahoo 파일들 처리 (source 필터에 따라)
        if source_filter in ['all', 'yahoo']:
            # 정확히 최신 파일 사용 (20250928_191547 파일)
            if yahoo_files:
                filename = yahoo_files[0]  # 가장 최신 파일
                filepath = os.path.join(data_dir, filename)
                print(f"Loading Yahoo file: {filename}")  # 디버깅용
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if isinstance(data, dict) and 'products' in data:
                        items = data['products']
                    else:
                        items = data if isinstance(data, list) else []

                    yahoo_total = 0
                    for item in items:
                        # 판매 완료 상품 및 취소된 경매 제외
                        time_left = item.get('time_left', '')
                        if any(term in time_left for term in ['終了', '落札', '取消', 'キャンセル', '売却済']):
                            continue
                        # 가격이 0인 경우도 제외
                        if item.get('current_price', 0) == 0:
                            continue

                        product = {
                            'title': item.get('title', ''),
                            'price': f"¥{item.get('current_price', 0):,}",
                            'price_krw': f"₩{item.get('price_krw', 0):,}" if item.get('price_krw') else '',
                            'url': item.get('url', '#'),
                            'image': item.get('image', item.get('image_url', '')),  # image 먼저, 없으면 image_url
                            'market': 'Yahoo',
                            'brand': item.get('brand', '기타'),
                            'position': item.get('position', '올라운드'),
                            'condition': item.get('condition', '중고'),
                            'bids': item.get('bids', '0'),
                            'time_left': item.get('time_left', '')
                        }
                        products.append(product)
                        yahoo_total += item.get('current_price', 0)

                    yahoo_count = len([p for p in products if p['market'] == 'Yahoo'])
                    if yahoo_count > 0:
                        yahoo_avg = yahoo_total // yahoo_count

                    print(f"Loaded {yahoo_count} Yahoo products from {filename}")

                except Exception as e:
                    print(f"Error loading Yahoo file {filename}: {e}")

        # Yayongsa 파일 처리 (source 필터에 따라)
        if source_filter in ['all', 'yayongsa']:
            for filename in yayongsa_files[:1]:  # 최신 1개만
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if isinstance(data, dict) and 'products' in data:
                        items = data['products']
                    else:
                        items = data if isinstance(data, list) else []

                    yayongsa_total = 0
                    for item in items:
                        if item.get('price', 0) == 0:
                            continue

                        # 이미지 URL 처리 - 두 번째 이미지 사용 (첫 번째는 썸네일)
                        images = item.get('images', [])
                        image_url = images[1] if len(images) > 1 else (images[0] if images else '')

                        product = {
                            'title': item.get('title', ''),
                            'price': f"₩{item.get('price', 0):,}",
                            'url': item.get('url', '#'),
                            'image': image_url,  # 야용사 이미지 추가
                            'market': 'Yayongsa',
                            'location': item.get('location', ''),
                            'brand': item.get('brand', '기타'),
                            'position': item.get('position', '올라운드'),
                            'condition': item.get('condition', '중고'),
                            'author': item.get('author', ''),
                            'date': item.get('date', ''),
                            'views': item.get('views', '0')
                        }
                        products.append(product)
                        yayongsa_total += item.get('price', 0)

                    # 야용사 카운트를 바로 계산
                    yayongsa_products_in_list = [p for p in products if p['market'] == 'Yayongsa']
                    yayongsa_count = len(yayongsa_products_in_list)
                    if yayongsa_count > 0:
                        yayongsa_avg = yayongsa_total // yayongsa_count

                    print(f"Loaded {yayongsa_count} Yayongsa products from {filename}")

                except Exception as e:
                    print(f"Error loading Yayongsa file {filename}: {e}")

    # 최종 카운트 다시 계산 (모든 파일 로드 후)
    yahoo_count = len([p for p in products if p['market'] == 'Yahoo'])
    yayongsa_count = len([p for p in products if p['market'] == 'Yayongsa'])
    total_count = len(products)

    # 평균가격 재계산
    if yahoo_count > 0:
        yahoo_products = [p for p in products if p['market'] == 'Yahoo']
        yahoo_prices = []
        for p in yahoo_products:
            try:
                # 가격 문자열에서 숫자만 추출
                price_str = p['price'].replace('¥', '').replace(',', '')
                yahoo_prices.append(int(price_str))
            except:
                pass
        if yahoo_prices:
            yahoo_avg = sum(yahoo_prices) // len(yahoo_prices)

    if yayongsa_count > 0:
        yayongsa_products = [p for p in products if p['market'] == 'Yayongsa']
        yayongsa_prices = []
        for p in yayongsa_products:
            try:
                # 가격 문자열에서 숫자만 추출
                price_str = p['price'].replace('₩', '').replace(',', '')
                yayongsa_prices.append(int(price_str))
            except:
                pass
        if yayongsa_prices:
            yayongsa_avg = sum(yayongsa_prices) // len(yayongsa_prices)

    print(f"Total products to display: {total_count}")
    print(f"Yahoo: {yahoo_count}, Yayongsa: {yayongsa_count}")

    return render_template('product_dashboard.html',
                         yahoo_count=yahoo_count,
                         yayongsa_count=yayongsa_count,
                         yahoo_avg=yahoo_avg,
                         yayongsa_avg=yayongsa_avg,
                         products=products,
                         total_count=total_count)

@app.route('/dashboard/statistics')
def dashboard_statistics():
    """통계 대시보드 페이지 - 로그인 없이 접근 가능"""
    products = []
    yahoo_count = 0
    yayongsa_count = 0
    yahoo_avg = 0
    yayongsa_avg = 0

    # 데이터 디렉토리에서 JSON 파일 읽기
    data_dir = 'data'
    if os.path.exists(data_dir):
        # Yahoo 데이터 로드 - 최신 파일만
        yahoo_files = sorted([f for f in os.listdir(data_dir) if 'yahoo_auction' in f.lower() and f.endswith('.json')], reverse=True)
        if yahoo_files:
            file = yahoo_files[0]  # 최신 파일만 사용
            try:
                with open(os.path.join(data_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = data.get('products', [])  # products 필드 사용
                    for item in items:
                        # 판매 완료 상품 제외
                        time_left = item.get('time_left', '')
                        if any(term in time_left for term in ['終了', '落札', '取消', 'キャンセル', '売却済']):
                            continue
                        if item.get('current_price', 0) == 0:
                            continue

                        # 통일된 형식으로 변환
                        product = {
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'image': item.get('image', item.get('image_url', '/static/images/no-image.png')),
                            'current_price': item.get('current_price', 0),
                            'price': item.get('current_price', 0),
                            'brand': item.get('brand', '기타'),
                            'position': item.get('position', '올라운드'),
                            'condition': item.get('condition', '중고'),
                            'type': 'hardball',
                            'market': 'Yahoo'
                        }
                        products.append(product)
                        yahoo_count += 1
            except Exception as e:
                print(f"Error loading Yahoo file {file}: {e}")

        # 야용사 데이터 로드 - 최신 파일만
        yayongsa_files = sorted([f for f in os.listdir(data_dir) if 'yayongsa' in f.lower() and f.endswith('.json')], reverse=True)
        if yayongsa_files:
            file = yayongsa_files[0]  # 최신 파일만 사용
            try:
                with open(os.path.join(data_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = data.get('products', [])
                    for item in items:
                        # 가격 처리
                        price_value = item.get('price', 0)
                        if isinstance(price_value, str):
                            price_value = int(''.join(filter(str.isdigit, price_value)) or 0)

                        if price_value == 0:
                            continue

                        # 이미지 처리
                        images = item.get('images', [])
                        # 야용사는 두 번째 이미지를 썸네일로 사용
                        image_url = images[1] if len(images) > 1 else (images[0] if images else '/static/images/no-image.png')

                        product = {
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'image': image_url,
                            'current_price': price_value,
                            'price': price_value,
                            'brand': item.get('brand', '기타'),
                            'position': item.get('position', '올라운드'),
                            'condition': item.get('condition', '중고'),
                            'type': 'hardball',
                            'market': 'Yayongsa'
                        }
                        products.append(product)
                        yayongsa_count += 1
            except Exception as e:
                print(f"Error loading Yayongsa file {file}: {e}")

    # 평균 가격 계산
    yahoo_prices = [p['current_price'] for p in products if p['market'] == 'Yahoo' and p['current_price'] > 0]
    if yahoo_prices:
        yahoo_avg = sum(yahoo_prices) / len(yahoo_prices)

    yayongsa_prices = [p['current_price'] for p in products if p['market'] == 'Yayongsa' and p['current_price'] > 0]
    if yayongsa_prices:
        yayongsa_avg = sum(yayongsa_prices) / len(yayongsa_prices)

    print(f"Statistics Dashboard - Total products: {len(products)}, Yahoo: {yahoo_count}, Yayongsa: {yayongsa_count}")

    return render_template('statistics_dashboard.html',
                           products=products,
                           yahoo_count=yahoo_count,
                           yayongsa_count=yayongsa_count,
                           yahoo_avg=int(yahoo_avg),
                           yayongsa_avg=int(yayongsa_avg))

@app.route('/dashboard/stats')
@app.route('/dashboard/analysis')
@login_required
def dashboard_analysis():
    """통계 분석 대시보드"""
    user = User.query.get(session['user_id'])
    stats = get_user_stats(user.username)

    # 데이터 파일들 로드하여 상세 통계 계산
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')

    brand_stats = {}
    position_stats = {}
    condition_stats = {'new': 0, 'used': 0}
    price_ranges = {'0-20k': 0, '20-40k': 0, '40-60k': 0, '60k+': 0}

    if os.path.exists(data_dir):
        # 최신 Yahoo 파일 처리
        for file in os.listdir(data_dir):
            if file.endswith('.json') and 'yahoo' in file.lower():
                filepath = os.path.join(data_dir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'products' in data:
                            for product in data['products']:
                                # 브랜드 통계
                                brand = product.get('brand', '기타')
                                if brand not in brand_stats:
                                    brand_stats[brand] = {'count': 0, 'total_price': 0}
                                brand_stats[brand]['count'] += 1
                                brand_stats[brand]['total_price'] += product.get('current_price', 0)

                                # 포지션 통계
                                position = product.get('position', '올라운드')
                                position_stats[position] = position_stats.get(position, 0) + 1

                                # 상태 통계
                                if product.get('condition') == '신품':
                                    condition_stats['new'] += 1
                                else:
                                    condition_stats['used'] += 1

                                # 가격대 통계
                                price = product.get('current_price', 0)
                                if price < 20000:
                                    price_ranges['0-20k'] += 1
                                elif price < 40000:
                                    price_ranges['20-40k'] += 1
                                elif price < 60000:
                                    price_ranges['40-60k'] += 1
                                else:
                                    price_ranges['60k+'] += 1
                        break  # 최신 파일만 처리
                except Exception as e:
                    print(f"Error processing stats: {e}")

    return render_template('stats_dashboard.html',
                         stats=stats,
                         brand_stats=brand_stats,
                         position_stats=position_stats,
                         condition_stats=condition_stats,
                         price_ranges=price_ranges)

@app.route('/dashboard')
@login_required
def dashboard():
    """대시보드"""
    user = User.query.get(session['user_id'])

    # 최근 크롤링 기록
    recent_crawls = CrawlHistory.query.filter_by(user_id=user.id)\
                    .order_by(CrawlHistory.created_at.desc()).limit(10).all()

    # 통계 데이터 로드
    stats = get_user_stats(user.username)

    # 평균 가격은 이미 stats에 포함되어 있음
    yahoo_avg_price = stats.get('yahoo_avg_price', 0)
    yayongsa_avg_price = stats.get('yayongsa_avg_price', 0)

    # 최근 크롤링 시간
    last_crawl = None
    if recent_crawls:
        last_crawl = recent_crawls[0].created_at.strftime('%Y-%m-%d %H:%M')

    return render_template('dashboard.html',
                         current_user=user,
                         yahoo_count=stats['yahoo_items'],
                         yayongsa_count=stats['yayongsa_items'],
                         total_count=stats['total_items'],
                         yahoo_avg_price=yahoo_avg_price,
                         yayongsa_avg_price=yayongsa_avg_price,
                         last_crawl=last_crawl,
                         user=user,
                         recent_crawls=recent_crawls,
                         stats=stats)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
@approved_required
def settings():
    """설정 페이지"""
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        kakao_id = request.form.get('kakao_id')
        kakao_password = request.form.get('kakao_password')

        # 암호화해서 저장 (실제로는 더 안전한 방법 사용 필요)
        if kakao_id:
            user.kakao_id = kakao_id
        if kakao_password:
            user.kakao_password = kakao_password

        db.session.commit()
        flash('설정이 저장되었습니다.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('settings.html', user=user)

@app.route('/crawl/<market>')
@app.route('/crawl/<market>/<int:days>')
@login_required
@approved_required
def crawl(market, days=3):
    """크롤링 실행 (기본 3일치)"""
    user = User.query.get(session['user_id'])

    if not user.kakao_id and market == 'yayongsa':
        flash('야용사 크롤링을 위해 카카오 계정 정보를 먼저 입력해주세요.', 'warning')
        return redirect(url_for('settings'))

    # 크롤링 기록 생성
    history = CrawlHistory(
        user_id=user.id,
        market=market,
        status='running',
        created_at=datetime.now(KST)
    )
    db.session.add(history)
    user.last_crawl = datetime.now(KST)
    db.session.commit()

    # 백그라운드로 크롤링 실행
    threading.Thread(target=run_crawling,
                    args=(app, user.username, market, history.id, days,
                          user.kakao_id, user.kakao_password)).start()

    flash(f'{market} {days}일치 크롤링이 시작되었습니다. 약 2-3분 후 결과를 확인해주세요.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/users/<username>/dashboards/<filename>')
def serve_dashboard(username, filename):
    """대시보드 파일 제공"""
    # 로그인 확인
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 사용자 권한 확인 (자신의 대시보드 또는 관리자)
    current_user = User.query.get(session['user_id'])
    if current_user.username != username and not current_user.is_admin:
        flash('권한이 없습니다.', 'danger')
        return redirect(url_for('dashboard'))

    # 파일 경로
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'users', username, 'dashboards', filename)

    # 파일 존재 확인
    if not os.path.exists(file_path):
        return "대시보드를 찾을 수 없습니다.", 404

    # HTML 파일 반환
    return send_file(file_path)

@app.route('/admin')
@admin_required
def admin_panel():
    """관리자 패널"""
    pending_users = User.query.filter_by(is_approved=False).all()
    approved_users = User.query.filter_by(is_approved=True).all()

    # 전체 통계
    total_crawls = CrawlHistory.query.count()
    today_crawls = CrawlHistory.query.filter(
        CrawlHistory.created_at >= datetime.now().date()
    ).count()

    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/approve/<int:user_id>')
@admin_required
def approve_user(user_id):
    """사용자 승인"""
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()

    # 사용자 디렉토리 생성
    create_user_directory(user.username)

    flash(f'{user.username}님을 승인했습니다.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/revoke/<int:user_id>')
@admin_required
def revoke_user(user_id):
    """사용자 권한 취소"""
    user = User.query.get_or_404(user_id)

    if user.is_admin:
        flash('관리자 권한은 취소할 수 없습니다.', 'danger')
    else:
        user.is_approved = False
        db.session.commit()
        flash(f'{user.username}님의 권한을 취소했습니다.', 'warning')

    return redirect(url_for('admin_panel'))

@app.route('/admin/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    """사용자 삭제"""
    user = User.query.get_or_404(user_id)

    if user.is_admin:
        flash('관리자 계정은 삭제할 수 없습니다.', 'danger')
        return redirect(url_for('admin_panel'))

    # 사용자 데이터 디렉토리 삭제
    user_dir = f"./users/{user.username}"
    if os.path.exists(user_dir):
        import shutil
        shutil.rmtree(user_dir)

    # 사용자 크롤링 기록 삭제
    CrawlHistory.query.filter_by(user_id=user.id).delete()

    # 사용자 삭제
    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'{username}님의 계정이 완전히 삭제되었습니다.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/make_admin/<int:user_id>')
@admin_required
def make_admin(user_id):
    """사용자를 관리자로 승급"""
    user = User.query.get_or_404(user_id)

    if user.is_admin:
        flash(f'{user.username}님은 이미 관리자입니다.', 'info')
    else:
        user.is_admin = True
        user.is_approved = True
        db.session.commit()
        flash(f'{user.username}님을 관리자로 승급했습니다.', 'success')

    return redirect(url_for('admin_panel'))

@app.route('/admin/stats')
@admin_required
def admin_stats():
    """관리자 통계 페이지"""
    # 전체 통계
    total_users = User.query.count()
    approved_users = User.query.filter_by(is_approved=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()

    # 오늘 통계
    today = datetime.now().date()
    today_signups = User.query.filter(db.func.date(User.created_at) == today).count()
    today_crawls = CrawlHistory.query.filter(db.func.date(CrawlHistory.created_at) == today).count()

    # 크롤링 통계
    total_crawls = CrawlHistory.query.count()
    yahoo_crawls = CrawlHistory.query.filter_by(market='yahoo').count()
    yayongsa_crawls = CrawlHistory.query.filter_by(market='yayongsa').count()

    stats = {
        'total_users': total_users,
        'approved_users': approved_users,
        'admin_users': admin_users,
        'today_signups': today_signups,
        'today_crawls': today_crawls,
        'total_crawls': total_crawls,
        'yahoo_crawls': yahoo_crawls,
        'yayongsa_crawls': yayongsa_crawls
    }

    return render_template('admin_stats.html', stats=stats)

@app.route('/api/crawl/yahoo', methods=['POST'])
@login_required
def api_crawl_yahoo():
    """Yahoo 크롤링 API"""
    try:
        # 크롤링을 백그라운드에서 실행
        import subprocess
        import threading

        def run_crawler():
            try:
                # Chrome 창이 열리는 크롤러 실행
                result = subprocess.run(['python', 'run_yahoo_crawler.py'],
                                       capture_output=True, text=True, encoding='utf-8')
                if result.returncode != 0:
                    print(f"크롤러 오류: {result.stderr}")
                else:
                    print(f"크롤러 성공: {result.stdout[-500:]}")  # 마지막 500자만 출력
            except Exception as e:
                print(f"크롤러 실행 오류: {str(e)}")

        # 별도 스레드에서 크롤러 실행
        crawler_thread = threading.Thread(target=run_crawler)
        crawler_thread.start()

        return jsonify({
            'status': 'success',
            'message': 'Yahoo Auction 크롤링이 시작되었습니다.\nChrome 창이 자동으로 열립니다.\n완료까지 약 1-2분 소요됩니다.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/crawl/yayongsa', methods=['POST'])
@login_required
def api_crawl_yayongsa():
    """야용사 크롤링 API - 수동 로그인 안내"""
    try:
        import subprocess
        import threading

        def run_yayongsa_crawler():
            try:
                # Chrome 창이 열리면서 수동 로그인 대기
                result = subprocess.run(['python', 'yayongsa_crawler.py'],
                                       capture_output=True, text=True, encoding='utf-8')
                if result.returncode != 0:
                    print(f"야용사 크롤러 오류: {result.stderr}")
                else:
                    print(f"야용사 크롤러 성공: {result.stdout[-500:]}")
            except Exception as e:
                print(f"야용사 크롤러 실행 오류: {str(e)}")

        # 별도 스레드에서 크롤러 실행
        crawler_thread = threading.Thread(target=run_yayongsa_crawler)
        crawler_thread.start()

        return jsonify({
            'status': 'success',
            'message': '야용사 크롤링이 시작되었습니다.\nChrome 창이 열리면 수동으로 로그인해주세요.\n로그인 후 자동으로 크롤링이 진행됩니다.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/dashboard/update', methods=['POST'])
@login_required
def api_dashboard_update():
    """대시보드 업데이트 API"""
    try:
        import subprocess
        subprocess.run(['python', 'update_dashboard.py'])
        return jsonify({'status': 'success', 'message': '대시보드가 업데이트되었습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/crawl_status/<int:history_id>')
@login_required
def crawl_status(history_id):
    """크롤링 상태 확인 API"""
    history = CrawlHistory.query.get_or_404(history_id)

    # 권한 확인
    if history.user_id != session['user_id'] and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify({
        'status': history.status,
        'item_count': history.item_count,
        'error': history.error_message
    })

# 헬퍼 함수
def create_user_directory(username):
    """사용자 디렉토리 생성"""
    user_dir = f"./users/{username}"
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(f"{user_dir}/data", exist_ok=True)
    os.makedirs(f"{user_dir}/images", exist_ok=True)
    os.makedirs(f"{user_dir}/dashboards", exist_ok=True)

def get_user_stats(username):
    """사용자 통계 가져오기 - 메인 data 폴더에서 최신 데이터만"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    stats = {
        'total_items': 0,
        'yahoo_items': 0,
        'yayongsa_items': 0,
        'last_crawl': None,
        'yahoo_avg_price': 0,
        'yayongsa_avg_price': 0
    }

    # 메인 data 폴더에서 최신 파일만 찾기
    data_dir = os.path.join(base_dir, 'data')
    if not os.path.exists(data_dir):
        return stats

    # 최신 파일 찾기 (yahoo_auction 파일만)
    latest_yahoo = None
    latest_yayongsa = None

    for file in os.listdir(data_dir):
        if not file.endswith('.json'):
            continue
        if 'yahoo_auction' in file.lower():
            if not latest_yahoo or file > latest_yahoo:
                latest_yahoo = file
        elif 'yayongsa' in file.lower():
            if not latest_yayongsa or file > latest_yayongsa:
                latest_yayongsa = file

    # Yahoo 데이터 처리
    if latest_yahoo:
        filepath = os.path.join(data_dir, latest_yahoo)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'products' in data:
                    products = data['products']
                    stats['yahoo_items'] = len(products)
                    # 평균 가격 계산
                    total_price = sum(p.get('current_price', 0) for p in products if p.get('current_price', 0) > 0)
                    count = len([p for p in products if p.get('current_price', 0) > 0])
                    if count > 0:
                        stats['yahoo_avg_price'] = total_price // count
                elif isinstance(data, list):
                    stats['yahoo_items'] = len(data)
                stats['last_crawl'] = latest_yahoo.split('_')[1] if '_' in latest_yahoo else None
        except Exception as e:
            print(f"Error loading Yahoo stats: {e}")

    # Yayongsa 데이터 처리
    if latest_yayongsa:
        filepath = os.path.join(data_dir, latest_yayongsa)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'products' in data:
                    products = data['products']
                    stats['yayongsa_items'] = len(products)
                    # 평균 가격 계산
                    total_price = sum(p.get('price', 0) for p in products if p.get('price', 0) > 0)
                    count = len([p for p in products if p.get('price', 0) > 0])
                    if count > 0:
                        stats['yayongsa_avg_price'] = total_price // count
                elif isinstance(data, list):
                    stats['yayongsa_items'] = len(data)
        except Exception as e:
            print(f"Error loading Yayongsa stats: {e}")

    stats['total_items'] = stats['yahoo_items'] + stats['yayongsa_items']
    return stats

def run_crawling(app, username, market, history_id, days=3, kakao_id=None, kakao_password=None):
    """백그라운드 크롤링 실행"""
    with app.app_context():
        history = CrawlHistory.query.get(history_id)
        try:
            # 절대 경로 사용
            base_dir = os.path.dirname(os.path.abspath(__file__))
            user_dir = os.path.join(base_dir, 'users', username)

            # 사용자 디렉토리가 없으면 생성
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
                os.makedirs(os.path.join(user_dir, 'data'))
                os.makedirs(os.path.join(user_dir, 'images'))
                os.makedirs(os.path.join(user_dir, 'dashboards'))

            # 사용자 설정 파일 생성
            if market == 'yayongsa' and kakao_id and kakao_password:
                config_file = os.path.join(user_dir, 'config.py')
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write(f'''
KAKAO_ID = "{kakao_id}"
KAKAO_PASSWORD = "{kakao_password}"
WAIT_TIME = 30
CRAWL_DAYS = {days}

BOARDS = {{
    "중고글러브벼룩시장": {{
        "url": "https://cafe.daum.net/baseballsale/79XF",
        "enabled": True
    }},
    "새제품 글러브 벼룩시장": {{
        "url": "https://cafe.daum.net/baseballsale/2Fsn",
        "enabled": True
    }}
}}
''')

            # 현재 디렉토리 저장
            original_dir = os.getcwd()

            # 크롤러 실행
            os.chdir(user_dir)

            if market == 'yahoo':
                # Yahoo 크롤러를 사용자 디렉토리에서 실행
                crawler_path = os.path.join(base_dir, 'yahoo_crawler.py')
                result = subprocess.run(['python', crawler_path],
                                      cwd=user_dir,  # 사용자 디렉토리에서 실행
                                      capture_output=True, text=True, encoding='utf-8')
            else:  # yayongsa
                # 수동 로그인을 위한 Jupyter 크롤러 사용
                crawler_path = os.path.join(base_dir, 'yayongsa_jupyter_crawler.py')
                result = subprocess.run(['python', crawler_path],
                                      cwd=user_dir,  # 사용자 디렉토리에서 실행
                                      capture_output=True, text=True, encoding='utf-8')

            # 원래 디렉토리로 복귀
            os.chdir(original_dir)

            # 결과 업데이트
            if history:
                history.status = 'completed' if result.returncode == 0 else 'failed'
                history.completed_at = datetime.now(KST)

                # 수집된 아이템 수 계산
                stats = get_user_stats(username)
                history.item_count = stats[f'{market}_items']

                if result.returncode != 0:
                    history.error_message = result.stderr[:500] if result.stderr else 'Unknown error'

                db.session.commit()

            # 대시보드 생성
            dashboard_path = os.path.join(base_dir, 'enhanced_dashboard.py')
            if os.path.exists(dashboard_path):
                subprocess.run(['python', dashboard_path], cwd=user_dir)

            # 제품 대시보드 생성
            product_dashboard_path = os.path.join(base_dir, 'product_dashboard.py')
            if os.path.exists(product_dashboard_path):
                subprocess.run(['python', product_dashboard_path], cwd=user_dir)

        except Exception as e:
            try:
                os.chdir(original_dir)
            except:
                pass

            history = CrawlHistory.query.get(history_id)
            if history:
                history.status = 'failed'
                history.error_message = str(e)
                history.completed_at = datetime.now(KST)
                db.session.commit()

@app.route('/dashboard/export')
@login_required
def export_products():
    """크롤링된 제품 데이터를 Excel로 다운로드"""
    user = User.query.get(session['user_id'])
    products = []

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')

    # 모든 JSON 파일 처리
    if os.path.exists(data_dir):
        # 가장 최신 Yahoo 파일 찾기 (yahoo_auction 파일만 선택, yahoo_test 제외)
        yahoo_files = sorted([f for f in os.listdir(data_dir) if 'yahoo_auction' in f.lower() and f.endswith('.json')], reverse=True)
        yayongsa_files = sorted([f for f in os.listdir(data_dir) if 'yayongsa' in f.lower() and f.endswith('.json')], reverse=True)

        # Yahoo 파일들 처리
        for filename in yahoo_files[:1]:  # 최신 1개만
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and 'products' in data:
                    items = data['products']
                else:
                    items = data if isinstance(data, list) else []

                for item in items:
                    # 판매 완료 상품 및 취소된 경매 제외
                    time_left = item.get('time_left', '')
                    if any(term in time_left for term in ['終了', '落札', '取消', 'キャンセル', '売却済']):
                        continue
                    # 가격이 0인 경우도 제외
                    if item.get('current_price', 0) == 0:
                        continue

                    products.append({
                        'Title': item.get('title', ''),
                        'Price (JPY)': item.get('current_price', 0),
                        'Price (KRW)': item.get('price_krw', 0),
                        'Brand': item.get('brand', '기타'),
                        'Position': item.get('position', '올라운드'),
                        'Condition': item.get('condition', '중고'),
                        'Bids': item.get('bids', '0'),
                        'Time Left': item.get('time_left', ''),
                        'Market': 'Yahoo Auction',
                        'URL': item.get('url', '#'),
                        'Total Cost (JPY)': item.get('total_cost_jpy', 0),
                        'Total Cost (KRW)': item.get('total_cost_krw', 0)
                    })
            except Exception as e:
                print(f"Error loading Yahoo file {filename}: {e}")

        # Yayongsa 파일들 처리
        for filename in yayongsa_files[:1]:  # 최신 1개만
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and 'products' in data:
                    items = data['products']
                else:
                    items = data if isinstance(data, list) else []

                for item in items:
                    products.append({
                        'Title': item.get('title', ''),
                        'Price (JPY)': 0,
                        'Price (KRW)': item.get('price', 0),
                        'Brand': item.get('brand', '기타'),
                        'Position': item.get('position', '올라운드'),
                        'Condition': item.get('condition', '중고'),
                        'Bids': '0',
                        'Time Left': 'N/A',
                        'Market': '야용사 카페',
                        'URL': item.get('url', '#'),
                        'Total Cost (JPY)': 0,
                        'Total Cost (KRW)': item.get('price', 0)
                    })
            except Exception as e:
                print(f"Error loading Yayongsa file {filename}: {e}")

    # Create Excel file
    output = BytesIO()

    # Create a Pandas DataFrame
    df = pd.DataFrame(products)

    # Create Excel writer object with xlsxwriter engine
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write dataframe to excel
        df.to_excel(writer, sheet_name='Products', index=False)

        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Products']

        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'bg_color': '#4CAF50',
            'font_color': 'white',
            'border': 1
        })

        # Write header row with formatting
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Adjust column widths
        worksheet.set_column('A:A', 40)  # Title
        worksheet.set_column('B:C', 15)  # Prices
        worksheet.set_column('D:F', 12)  # Brand, Position, Condition
        worksheet.set_column('G:H', 10)  # Bids, Time
        worksheet.set_column('I:I', 15)  # Market
        worksheet.set_column('J:J', 50)  # URL
        worksheet.set_column('K:L', 15)  # Total costs

    output.seek(0)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'glove_products_{timestamp}.xlsx'

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)