#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
글러브 마켓 크롤러 - 간단 실행 스크립트
"""

import os
import sys
import subprocess

def print_menu():
    print("\n" + "="*60)
    print("⚾ 글러브 마켓 크롤러 시스템")
    print("="*60)
    print("\n작업을 선택하세요:")
    print("1. 웹 서버 실행 (로그인/대시보드)")
    print("2. Yahoo 크롤링 실행")
    print("3. 야용사 크롤링 실행 (수동 로그인)")
    print("4. 통합 대시보드 업데이트")
    print("5. 대시보드 열기 (브라우저)")
    print("0. 종료")

def main():
    while True:
        print_menu()
        choice = input("\n선택 (0-5): ").strip()

        if choice == "0":
            print("프로그램을 종료합니다.")
            break

        elif choice == "1":
            print("\n🌐 웹 서버를 실행합니다...")
            print("브라우저에서 http://localhost:5000 접속")
            print("로그인: admin / admin123")
            subprocess.run([sys.executable, "main_app.py"])

        elif choice == "2":
            print("\n🇯🇵 Yahoo Auction 크롤링을 시작합니다...")
            subprocess.run([sys.executable, "yahoo_crawler.py"])

        elif choice == "3":
            print("\n🇰🇷 야용사 카페 크롤링을 시작합니다...")
            print("수동 로그인이 필요합니다!")
            subprocess.run([sys.executable, "yayongsa_crawler.py"])

        elif choice == "4":
            print("\n📊 대시보드를 업데이트합니다...")
            subprocess.run([sys.executable, "update_dashboard.py"])

        elif choice == "5":
            print("\n🌐 대시보드를 브라우저에서 엽니다...")
            if os.path.exists("dashboards/integrated_full.html"):
                os.system("start dashboards/integrated_full.html")
            else:
                print("대시보드 파일이 없습니다. 먼저 업데이트하세요.")

        else:
            print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()