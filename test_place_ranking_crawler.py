"""
네이버 플레이스 순위 크롤러 테스트 스크립트
다양한 키워드와 옵션으로 크롤러를 테스트
"""

import asyncio
import argparse
import logging
from datetime import datetime
from typing import List

from src.crawler.naver_map_crawler import NaverMapCrawler, crawl_naver_map, crawl_multiple_keywords


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_keyword(keyword: str, max_results: int = 10):
    """단일 키워드 테스트"""
    logger.info(f"=== 단일 키워드 테스트: '{keyword}' ===")
    
    start_time = datetime.now()
    
    try:
        results = await crawl_naver_map(keyword, max_results)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"크롤링 완료: {len(results)}개 결과, {execution_time:.2f}초 소요")
        
        print(f"\n📍 키워드: {keyword}")
        print(f"🕐 실행시간: {execution_time:.2f}초")
        print(f"📊 결과 수: {len(results)}개")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. {result['name']}")
            if i <= 5:  # 상위 5개는 원시 텍스트도 표시
                raw_preview = result['raw_text'][:80] + "..." if len(result['raw_text']) > 80 else result['raw_text']
                print(f"    └─ {raw_preview}")
        print()
        
        return results
        
    except Exception as e:
        logger.error(f"단일 키워드 테스트 실패: {e}")
        return []


async def test_multiple_keywords(keywords: List[str], max_results: int = 10):
    """다중 키워드 테스트"""
    logger.info(f"=== 다중 키워드 테스트: {len(keywords)}개 키워드 ===")
    
    start_time = datetime.now()
    
    try:
        all_results = await crawl_multiple_keywords(keywords, max_results)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        total_results = sum(len(results) for results in all_results.values())
        
        logger.info(f"배치 크롤링 완료: {len(keywords)}개 키워드, {total_results}개 총 결과, {execution_time:.2f}초 소요")
        
        print(f"\n📍 배치 크롤링 결과")
        print(f"🕐 총 실행시간: {execution_time:.2f}초")
        print(f"📊 총 결과 수: {total_results}개")
        print("=" * 60)
        
        for keyword, results in all_results.items():
            avg_time = execution_time / len(keywords)
            print(f"\n🔍 {keyword}: {len(results)}개 결과 (평균 {avg_time:.1f}초)")
            
            for i, result in enumerate(results[:3], 1):  # 상위 3개만 표시
                print(f"  {i}. {result['name']}")
        
        return all_results
        
    except Exception as e:
        logger.error(f"다중 키워드 테스트 실패: {e}")
        return {}


async def test_detailed_crawler():
    """상세한 크롤러 테스트"""
    logger.info("=== 상세 크롤러 테스트 ===")
    
    crawler = NaverMapCrawler()
    
    try:
        # 브라우저 초기화
        await crawler.init_browser()
        logger.info("✅ 브라우저 초기화 완료")
        
        # 테스트 키워드
        test_keyword = "홍대 카페"
        max_results = 15
        
        logger.info(f"🔍 키워드 '{test_keyword}' 크롤링 시작...")
        
        start_time = datetime.now()
        results = await crawler.search_places(test_keyword, max_results)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ 크롤링 완료: {len(results)}개 결과")
        
        # 파일 저장 테스트
        csv_file = await crawler.save_results_to_csv(results, test_keyword)
        json_file = await crawler.save_results_to_json(results, test_keyword)
        
        logger.info(f"💾 CSV 파일 저장: {csv_file}")
        logger.info(f"💾 JSON 파일 저장: {json_file}")
        
        print(f"\n📍 상세 테스트 결과")
        print(f"🔍 키워드: {test_keyword}")
        print(f"🕐 실행시간: {execution_time:.2f}초")
        print(f"📊 결과 수: {len(results)}개")
        print(f"💾 저장 파일: {csv_file}, {json_file}")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. {result['name']}")
            if i <= 3:  # 상위 3개는 상세 정보 표시
                print(f"    📝 원시: {result['raw_text'][:100]}...")
                print(f"    🕐 추출: {result['extracted_at']}")
        
        return results
        
    except Exception as e:
        logger.error(f"상세 크롤러 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        await crawler.close()
        logger.info("🔧 브라우저 정리 완료")


async def run_benchmark_test():
    """벤치마크 테스트"""
    logger.info("=== 벤치마크 테스트 ===")
    
    test_cases = [
        ("강남 맛집", 10),
        ("홍대 술집", 15),
        ("신촌 카페", 20),
        ("이태원 클럽", 5),
        ("명동 쇼핑", 12)
    ]
    
    total_start = datetime.now()
    all_results = []
    
    for keyword, max_results in test_cases:
        print(f"\n🔍 테스트: {keyword} (최대 {max_results}개)")
        
        case_start = datetime.now()
        results = await test_single_keyword(keyword, max_results)
        case_time = (datetime.now() - case_start).total_seconds()
        
        all_results.append({
            'keyword': keyword,
            'max_results': max_results,
            'actual_results': len(results),
            'execution_time': case_time,
            'results_per_second': len(results) / case_time if case_time > 0 else 0
        })
        
        print(f"⚡ 성능: {len(results)}개 결과, {case_time:.2f}초 ({len(results)/case_time:.1f}개/초)")
    
    total_time = (datetime.now() - total_start).total_seconds()
    total_results = sum(r['actual_results'] for r in all_results)
    
    print(f"\n📊 벤치마크 요약")
    print("=" * 60)
    print(f"🔍 총 테스트 케이스: {len(test_cases)}개")
    print(f"📊 총 결과 수: {total_results}개")
    print(f"🕐 총 실행시간: {total_time:.2f}초")
    print(f"⚡ 평균 성능: {total_results/total_time:.1f}개/초")
    print()
    
    for result in all_results:
        print(f"• {result['keyword']}: {result['actual_results']}/{result['max_results']} "
              f"({result['execution_time']:.1f}초, {result['results_per_second']:.1f}개/초)")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="네이버 플레이스 순위 크롤러 테스트")
    
    parser.add_argument(
        "--keyword", 
        type=str, 
        help="테스트할 단일 키워드"
    )
    
    parser.add_argument(
        "--max-results", 
        type=int, 
        default=10, 
        help="최대 결과 수 (기본값: 10)"
    )
    
    parser.add_argument(
        "--test-type",
        choices=["single", "multiple", "detailed", "benchmark", "all"],
        default="single",
        help="테스트 유형 (기본값: single)"
    )
    
    parser.add_argument(
        "--keywords",
        nargs="+",
        help="다중 테스트용 키워드 목록"
    )
    
    args = parser.parse_args()
    
    async def run_tests():
        if args.test_type == "single" or args.test_type == "all":
            keyword = args.keyword or "강남 맛집"
            await test_single_keyword(keyword, args.max_results)
        
        if args.test_type == "multiple" or args.test_type == "all":
            keywords = args.keywords or ["강남 맛집", "홍대 카페", "신촌 술집"]
            await test_multiple_keywords(keywords, args.max_results)
        
        if args.test_type == "detailed" or args.test_type == "all":
            await test_detailed_crawler()
        
        if args.test_type == "benchmark" or args.test_type == "all":
            await run_benchmark_test()
    
    # 테스트 실행
    print("🚀 네이버 플레이스 순위 크롤러 테스트 시작")
    print("=" * 60)
    
    try:
        asyncio.run(run_tests())
        print("\n✅ 모든 테스트 완료")
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()