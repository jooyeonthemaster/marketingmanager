"""
간단한 네이버 플레이스 순위 크롤링 테스트
빠른 테스트와 검증을 위한 심플한 스크립트
"""

import asyncio
import logging
from datetime import datetime

from src.crawler.naver_map_crawler import crawl_naver_map


# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def simple_test():
    """간단한 크롤링 테스트"""
    print("🚀 간단한 네이버 플레이스 크롤링 테스트")
    print("=" * 50)
    
    # 테스트 키워드들
    test_keywords = [
        "강남 맛집",
        "홍대 카페", 
        "신촌 술집"
    ]
    
    all_results = {}
    
    for keyword in test_keywords:
        print(f"\n🔍 '{keyword}' 크롤링 중...")
        
        start_time = datetime.now()
        
        try:
            # 크롤링 실행
            results = await crawl_naver_map(keyword, max_results=5)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            print(f"✅ 완료: {len(results)}개 결과 ({execution_time:.1f}초)")
            print("-" * 30)
            
            # 결과 출력
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['name']}")
            
            all_results[keyword] = results
            
            # 키워드 간 잠시 대기
            if keyword != test_keywords[-1]:  # 마지막이 아니면
                print("⏳ 잠시 대기...")
                await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ 실패: {str(e)}")
            all_results[keyword] = []
    
    # 전체 결과 요약
    print("\n" + "=" * 50)
    print("📊 크롤링 결과 요약")
    print("=" * 50)
    
    total_results = 0
    for keyword, results in all_results.items():
        count = len(results)
        total_results += count
        status = "✅" if count > 0 else "❌"
        print(f"{status} {keyword}: {count}개")
    
    print(f"\n🎯 총 {total_results}개 결과 수집")
    
    # 상위 결과들 표시
    if total_results > 0:
        print("\n🏆 각 키워드별 1위 업체:")
        for keyword, results in all_results.items():
            if results:
                print(f"• {keyword}: {results[0]['name']}")


async def quick_single_test(keyword: str = "강남 맛집"):
    """빠른 단일 키워드 테스트"""
    print(f"⚡ 빠른 테스트: '{keyword}'")
    print("-" * 30)
    
    start_time = datetime.now()
    
    try:
        results = await crawl_naver_map(keyword, max_results=3)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ {len(results)}개 결과 ({execution_time:.1f}초)")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['name']}")
    
    except Exception as e:
        print(f"❌ 오류: {str(e)}")


def main():
    """메인 실행 함수"""
    print("🎯 네이버 플레이스 크롤링 간단 테스트")
    print("선택하세요:")
    print("1. 간단한 다중 키워드 테스트")
    print("2. 빠른 단일 키워드 테스트") 
    print("3. 직접 입력")
    
    try:
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == "1":
            print("\n다중 키워드 테스트를 시작합니다...")
            asyncio.run(simple_test())
            
        elif choice == "2":
            print("\n빠른 단일 테스트를 시작합니다...")
            asyncio.run(quick_single_test())
            
        elif choice == "3":
            keyword = input("검색할 키워드를 입력하세요: ").strip()
            if keyword:
                print(f"\n'{keyword}' 크롤링을 시작합니다...")
                asyncio.run(quick_single_test(keyword))
            else:
                print("❌ 키워드가 입력되지 않았습니다.")
                
        else:
            print("❌ 잘못된 선택입니다. 기본 테스트를 실행합니다.")
            asyncio.run(simple_test())
            
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")


if __name__ == "__main__":
    main()