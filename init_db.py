#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""데이터베이스 초기화 스크립트"""

from main_app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # 데이터베이스 테이블 생성
    db.create_all()

    # 관리자 계정 생성 (이미 있으면 스킵)
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            is_admin=True,
            is_approved=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ 관리자 계정 생성 완료")
        print("   ID: admin")
        print("   PW: admin123")
    else:
        print("✅ 관리자 계정이 이미 존재합니다")

    print("✅ 데이터베이스 초기화 완료")