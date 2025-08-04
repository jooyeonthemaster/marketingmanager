"""
네이버 지도 플레이스 순위 크롤러
Playwright를 사용하여 네이버 지도에서 키워드 검색 결과의 순위를 크롤링
"""

import os
import re
import random
import asyncio
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Playwright
from bs4 import BeautifulSoup

from config.settings import (
    BROWSER_SETTINGS, CRAWLING_SETTINGS, NAVER_MAP_SETTINGS,
    OUTPUT_SETTINGS, DEBUG_SETTINGS, get_browser_args, is_production
)
from src.crawler.stealth_utils import StealthUtils


# 로깅 설정
logging.basicConfig(
    level=logging.INFO if DEBUG_SETTINGS["verbose_logging"] else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NaverMapCrawler:
    """네이버 지도 크롤러 클래스"""
    
    def __init__(self):
        """크롤러 초기화"""
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.stealth_utils = StealthUtils()
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_SETTINGS["output_directory"], exist_ok=True)
        os.makedirs(DEBUG_SETTINGS["html_save_dir"], exist_ok=True)
    
    async def init_browser(self) -> None:
        """브라우저 초기화"""
        try:
            logger.info("브라우저 초기화 시작...")
            
            self.playwright = await async_playwright().start()
            
            # 브라우저 설정
            browser_args = get_browser_args()
            user_agent = self.stealth_utils.get_random_user_agent()
            viewport = self.stealth_utils.get_random_viewport()
            
            logger.info(f"브라우저 설정: headless={BROWSER_SETTINGS['headless']}, viewport={viewport}")
            
            # 브라우저 실행
            self.browser = await self.playwright.chromium.launch(
                headless=BROWSER_SETTINGS["headless"],
                args=browser_args,
                slow_mo=BROWSER_SETTINGS["slow_mo"]
            )
            
            # 컨텍스트 생성
            context_options = {
                "viewport": viewport,
                "user_agent": user_agent,
                "extra_http_headers": self.stealth_utils.get_random_headers(),
                "ignore_https_errors": True,
                "java_script_enabled": True,
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # 페이지 생성
            self.page = await self.context.new_page()
            
            # 스텔스 기법 적용
            await self.stealth_utils.add_stealth_to_page(self.page)
            
            # 명시적으로 데스크톱 User-Agent 설정
            desktop_ua = self.stealth_utils.get_random_user_agent()
            await self.page.set_extra_http_headers({
                'User-Agent': desktop_ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            logger.info(f"User-Agent 설정: {desktop_ua[:50]}...")
            
            # 타임아웃 설정
            self.page.set_default_timeout(BROWSER_SETTINGS["timeout"])
            self.page.set_default_navigation_timeout(BROWSER_SETTINGS["timeout"])
            
            logger.info("브라우저 초기화 완료")
            
        except Exception as e:
            logger.error(f"브라우저 초기화 실패: {e}")
            await self.close()
            raise
    
    async def search_places(self, keyword: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """네이버 지도에서 장소 검색"""
        try:
            logger.info(f"키워드 '{keyword}' 검색 시작 (최대 {max_results}개)")
            
            # 네이버 지도 페이지 이동
            await self._navigate_to_naver_map()
            
            # 검색어 입력
            await self._input_search_keyword(keyword)
            
            # 검색 결과 대기 및 iframe 접근
            iframe = await self._wait_for_search_iframe()
            
            # 검색 결과 추출
            results = await self._extract_search_results(iframe, keyword, max_results)
            
            logger.info(f"검색 완료: {len(results)}개 결과 추출")
            return results
            
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}")
            if DEBUG_SETTINGS["screenshot_on_error"] and self.page:
                await self._save_error_screenshot(keyword)
            raise
    
    async def _navigate_to_naver_map(self) -> None:
        """네이버 지도 메인 페이지로 이동"""
        logger.info("네이버 지도 페이지 이동 중...")
        
        # 인간적인 행동 시뮬레이션
        await self.stealth_utils.random_delay(1.0, 2.0)
        
        # 페이지 이동
        response = await self.page.goto(
            NAVER_MAP_SETTINGS["base_url"],
            wait_until="networkidle",
            timeout=BROWSER_SETTINGS["timeout"]
        )
        
        if not response or response.status != 200:
            raise Exception(f"네이버 지도 페이지 로드 실패: {response.status if response else 'No response'}")
        
        # 페이지 로드 완료 대기
        await self.stealth_utils.random_delay(2.0, 3.0)
        
        # 디버깅: 현재 URL과 페이지 제목 확인
        current_url = self.page.url
        title = await self.page.title()
        logger.info(f"페이지 로드 상태 - URL: {current_url}, 제목: {title}")
        
        # 디버깅: 스크린샷 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_screenshot_path = f"debug_html/debug_page_load_{timestamp}.png"
        try:
            await self.page.screenshot(path=debug_screenshot_path, full_page=True)
            logger.info(f"디버그 스크린샷 저장: {debug_screenshot_path}")
        except Exception as e:
            logger.warning(f"스크린샷 저장 실패: {e}")
        
        # 앱 리다이렉트 확인
        if "appLink" in current_url or "app=Y" in current_url or "네이버 지도앱" in title:
            logger.warning(f"앱 리다이렉트 감지! URL: {current_url}, 제목: {title}")
            # 웹 버전으로 강제 이동
            await self.page.goto("https://map.naver.com/", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            current_url = self.page.url
            logger.info(f"웹 버전 강제 이동 완료: {current_url}")
        
        # 인간적인 상호작용 시뮬레이션 (브라우저가 닫히지 않도록 조심스럽게)
        try:
            await self.stealth_utils.simulate_human_interaction_pattern(self.page)
        except Exception as e:
            logger.warning(f"상호작용 시뮬레이션 중 오류: {e}")
        
        logger.info("네이버 지도 페이지 로드 완료")
    
    async def _input_search_keyword(self, keyword: str) -> None:
        """검색어 입력 및 검색 실행"""
        logger.info(f"검색어 '{keyword}' 입력 중...")
        
        try:
            # 검색 입력창 대기 - 여러 선택자 시도 (최신 네이버 지도)
            search_selectors = [
                "input[placeholder*='검색']",
                ".input_search", 
                "#query",
                "input[type='search']",
                "input[type='text']",
                ".search_input",
                "[data-testid='search-input']",
                ".header_search input",
                ".search_bar input",
                ".topbar_search input"
            ]
            
            search_element = None
            for selector in search_selectors:
                try:
                    search_element = await self.page.wait_for_selector(
                        selector,
                        timeout=5000  # 5초씩 시도
                    )
                    if search_element:
                        logger.info(f"검색 입력창 찾음: {selector}")
                        break
                except Exception as e:
                    logger.warning(f"선택자 {selector} 실패: {e}")
                    continue
            
            if not search_element:
                raise Exception("검색 입력창을 찾을 수 없습니다")
                
            # 인간적인 타이핑으로 검색어 입력 - 발견된 선택자 사용
            await search_element.click()
            await self.stealth_utils.random_delay(0.2, 0.5)
            
            # 기존 텍스트 삭제
            await self.page.keyboard.press("Control+a")
            await self.page.keyboard.press("Delete")
            await self.stealth_utils.random_delay(0.2, 0.4)
            
            # 키워드 입력
            for char in keyword:
                await self.page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            await self.stealth_utils.random_delay(0.3, 0.7)
            
            # Enter 키 입력
            await self.page.keyboard.press("Enter")
            
            # 검색 실행 후 대기
            await self.stealth_utils.random_delay(2.0, 4.0)
            
            logger.info("검색어 입력 및 검색 실행 완료")
            
        except Exception as e:
            logger.error(f"검색어 입력 실패: {e}")
            raise
    
    async def _wait_for_search_iframe(self):
        """검색 결과 iframe 대기 및 접근"""
        logger.info("검색 결과 iframe 대기 중...")
        
        # 여러 방법으로 iframe 접근 시도
        iframe_selectors = [
            f'iframe[name="{NAVER_MAP_SETTINGS["search_iframe_name"]}"]',
            'iframe[src*="search"]',
            'iframe[src*="place"]',
            '#searchIframe'
        ]
        
        iframe = None
        
        for selector in iframe_selectors:
            try:
                logger.info(f"iframe 선택자 시도: {selector}")
                
                # iframe 요소 대기
                iframe_element = await self.page.wait_for_selector(
                    selector,
                    timeout=CRAWLING_SETTINGS["iframe_wait_timeout"]
                )
                
                if iframe_element:
                    iframe = await iframe_element.content_frame()
                    if iframe:
                        logger.info(f"iframe 접근 성공: {selector}")
                        break
                        
            except Exception as e:
                logger.warning(f"iframe 선택자 {selector} 실패: {e}")
                continue
        
        if not iframe:
            # 디버그용 HTML 저장
            if DEBUG_SETTINGS["save_html"]:
                await self._save_debug_html("iframe_not_found")
            raise Exception("검색 결과 iframe을 찾을 수 없습니다")
        
        # iframe 로드 완료 대기
        await self.stealth_utils.random_delay(1.0, 2.0)
        
        return iframe
    
    async def _extract_search_results(self, iframe, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """검색 결과 추출"""
        logger.info("검색 결과 추출 시작...")
        
        results = []
        
        # 여러 선택자로 검색 결과 요소 찾기
        result_elements = None
        best_selector = None
        
        for selector in NAVER_MAP_SETTINGS["result_selectors"]:
            try:
                elements = await iframe.query_selector_all(selector)
                if len(elements) >= 3:  # 3개 이상의 결과가 있는 선택자 우선
                    result_elements = elements
                    best_selector = selector
                    logger.info(f"선택자 '{selector}'로 {len(elements)}개 요소 발견")
                    break
            except Exception as e:
                logger.warning(f"선택자 '{selector}' 실패: {e}")
                continue
        
        if not result_elements:
            # 디버그용 HTML 저장
            if DEBUG_SETTINGS["save_html"]:
                await self._save_debug_html("no_results", iframe)
            logger.warning("검색 결과를 찾을 수 없습니다")
            return results
        
        # 스크롤하여 추가 결과 로딩
        await self._scroll_for_more_results(iframe)
        
        # 결과 요소들 다시 조회 (스크롤 후 추가 요소들)
        result_elements = await iframe.query_selector_all(best_selector)
        logger.info(f"스크롤 후 총 {len(result_elements)}개 요소")
        
        # 각 결과 요소에서 정보 추출
        for idx, element in enumerate(result_elements[:max_results]):
            try:
                # 요소의 텍스트 추출
                raw_text = await element.text_content()
                if not raw_text or len(raw_text.strip()) < 2:
                    continue
                
                # 업체명 추출
                business_name = self.extract_business_name(raw_text)
                if not business_name:
                    continue
                
                result = {
                    'rank': idx + 1,
                    'name': business_name,
                    'raw_text': raw_text.strip(),
                    'keyword': keyword,
                    'extracted_at': datetime.now().isoformat()
                }
                
                results.append(result)
                logger.debug(f"순위 {idx + 1}: {business_name}")
                
            except Exception as e:
                logger.warning(f"결과 {idx + 1} 추출 실패: {e}")
                continue
        
        return results
    
    async def _scroll_for_more_results(self, iframe) -> None:
        """스크롤하여 추가 검색 결과 로딩"""
        logger.info("스크롤하여 추가 결과 로딩 중...")
        
        for i in range(CRAWLING_SETTINGS["scroll_attempts"]):
            # 아래로 스크롤
            await iframe.mouse.wheel(0, 500)
            await asyncio.sleep(CRAWLING_SETTINGS["scroll_delay"] / 1000)
            
            # 인간적인 행동 시뮬레이션
            if i % 2 == 0:
                await self.stealth_utils.simulate_reading_behavior(self.page, iframe)
        
        # 최종 대기
        await self.stealth_utils.random_delay(1.0, 2.0)
    
    def extract_business_name(self, raw_text: str) -> str:
        """원시 텍스트에서 업체명 추출"""
        if not raw_text:
            return ""
        
        # 키워드들로 텍스트 분리
        keywords = NAVER_MAP_SETTINGS["business_name_keywords"]
        
        # 첫 번째 키워드가 나오기 전까지의 텍스트를 업체명으로 간주
        for keyword in keywords:
            if keyword in raw_text:
                business_name = raw_text.split(keyword)[0].strip()
                if business_name:
                    # 최대 길이 제한
                    max_length = NAVER_MAP_SETTINGS["max_business_name_length"]
                    if len(business_name) > max_length:
                        business_name = business_name[:max_length]
                    return business_name
        
        # 키워드가 없으면 전체 텍스트의 첫 부분 사용
        lines = raw_text.split('\n')
        if lines:
            business_name = lines[0].strip()
            max_length = NAVER_MAP_SETTINGS["max_business_name_length"]
            if len(business_name) > max_length:
                business_name = business_name[:max_length]
            return business_name
        
        return raw_text.strip()[:NAVER_MAP_SETTINGS["max_business_name_length"]]
    
    async def _save_debug_html(self, filename_suffix: str, iframe=None) -> None:
        """디버깅용 HTML 저장"""
        try:
            timestamp = datetime.now().strftime(OUTPUT_SETTINGS["timestamp_format"])
            filename = f"debug_{filename_suffix}_{timestamp}.html"
            filepath = os.path.join(DEBUG_SETTINGS["html_save_dir"], filename)
            
            if iframe:
                content = await iframe.content()
            else:
                content = await self.page.content()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"디버그 HTML 저장: {filepath}")
            
        except Exception as e:
            logger.warning(f"디버그 HTML 저장 실패: {e}")
    
    async def _save_error_screenshot(self, keyword: str) -> None:
        """에러 발생 시 스크린샷 저장"""
        try:
            timestamp = datetime.now().strftime(OUTPUT_SETTINGS["timestamp_format"])
            filename = f"error_{keyword}_{timestamp}.png"
            filepath = os.path.join(DEBUG_SETTINGS["html_save_dir"], filename)
            
            await self.page.screenshot(path=filepath, full_page=True)
            logger.info(f"에러 스크린샷 저장: {filepath}")
            
        except Exception as e:
            logger.warning(f"스크린샷 저장 실패: {e}")
    
    async def save_results_to_csv(self, results: List[Dict[str, Any]], keyword: str) -> str:
        """결과를 CSV 파일로 저장"""
        timestamp = datetime.now().strftime(OUTPUT_SETTINGS["timestamp_format"])
        safe_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_')
        filename = f"naver_place_ranking_{safe_keyword}_{timestamp}.csv"
        filepath = os.path.join(OUTPUT_SETTINGS["output_directory"], filename)
        
        with open(filepath, 'w', newline='', encoding=OUTPUT_SETTINGS["encoding"]) as f:
            if results:
                fieldnames = ['rank', 'name', 'raw_text', 'keyword', 'extracted_at']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        
        logger.info(f"CSV 파일 저장: {filepath}")
        return filepath
    
    async def save_results_to_json(self, results: List[Dict[str, Any]], keyword: str) -> str:
        """결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime(OUTPUT_SETTINGS["timestamp_format"])
        safe_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_')
        filename = f"naver_place_ranking_{safe_keyword}_{timestamp}.json"
        filepath = os.path.join(OUTPUT_SETTINGS["output_directory"], filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON 파일 저장: {filepath}")
        return filepath
    
    async def close(self) -> None:
        """브라우저 리소스 정리"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("브라우저 리소스 정리 완료")
            
        except Exception as e:
            logger.warning(f"브라우저 정리 중 오류: {e}")


# 편의 함수
async def crawl_naver_map(keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """간단한 크롤링 함수"""
    crawler = NaverMapCrawler()
    try:
        await crawler.init_browser()
        results = await crawler.search_places(keyword, max_results)
        return results
    finally:
        await crawler.close()


async def crawl_multiple_keywords(keywords: List[str], max_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """여러 키워드 배치 크롤링"""
    crawler = NaverMapCrawler()
    all_results = {}
    
    try:
        await crawler.init_browser()
        
        for keyword in keywords:
            try:
                logger.info(f"키워드 '{keyword}' 크롤링 시작...")
                results = await crawler.search_places(keyword, max_results)
                all_results[keyword] = results
                
                # 키워드 간 대기
                await crawler.stealth_utils.random_delay(
                    CRAWLING_SETTINGS["delay_between_requests"],
                    CRAWLING_SETTINGS["delay_between_requests"] + 2
                )
                
            except Exception as e:
                logger.error(f"키워드 '{keyword}' 크롤링 실패: {e}")
                all_results[keyword] = []
        
        return all_results
        
    finally:
        await crawler.close()


if __name__ == "__main__":
    # 테스트 실행
    async def test_crawler():
        results = await crawl_naver_map("강남 맛집", 10)
        for result in results:
            print(f"{result['rank']}. {result['name']}")
    
    asyncio.run(test_crawler())