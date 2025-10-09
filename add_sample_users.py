#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
샘플 사용자 3명 추가 스크립트
"""

from main_app import app, db, User
from werkzeug.security import generate_password_hash

def add_sample_users():
    with app.app_context():
        # 샘플 사용자 3명
        sample_users = [
            {
                'username': 'glove_collector_01',
                'email': 'collector01@example.com',
                'password': 'Baseball2024!',
                'is_approved': True
            },
            {
                'username': 'yayoung_buyer_02',
                'email': 'buyer02@example.com',
                'password': 'Glove#Market99',
                'is_approved': True
            },
            {
                'username': 'baseball_fan_03',
                'email': 'fan03@example.com',
                'password': 'CafeTest@2024',
                'is_approved': True
            }
        ]

        for user_data in sample_users:
            # 기존 사용자 확인
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if existing_user:
                print(f"⚠️ {user_data['username']} 이미 존재합니다.")
                continue

            # 새 사용자 생성
            new_user = User(
                username=user_data['username'],
                email=user_data['email'],
                password=generate_password_hash(user_data['password']),
                is_admin=False,
                is_approved=user_data['is_approved']
            )
            db.session.add(new_user)
            print(f"✅ {user_data['username']} 추가됨 (비밀번호: {user_data['password']})")

        db.session.commit()
        print("\n✅ 샘플 사용자 3명 추가 완료!")
        print("\n로그인 정보:")
        print("-" * 60)
        for user_data in sample_users:
            print(f"아이디: {user_data['username']}")
            print(f"패스워드: {user_data['password']}")
            print("-" * 60)

if __name__ == "__main__":
    add_sample_users()
