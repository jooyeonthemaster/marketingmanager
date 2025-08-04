"""
네이버 플레이스 순위 크롤링 시스템 설정
"""

import os
from typing import Dict, Any, List

# 브라우저 설정 (BROWSER_SETTINGS)
BROWSER_SETTINGS = {
    "headless": True if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT") else False,
    "viewport": {"width": 1920, "height": 1080},
    "timeout": 60000,  # 60초
    "channel": "chrome",  # Patchright 권장
    "slow_mo": 0 if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT") else 1000,
    "args": [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled", 
        "--disable-features=VizDisplayCompositor",
        "--disable-dev-shm-usage",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-web-security",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--disable-protocol-handlers",
        "--force-device-scale-factor=1",
        "--lang=ko",
        "--disable-gpu"
    ]
}

# 프로덕션 환경에서는 단일 프로세스 모드 사용
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT"):
    BROWSER_SETTINGS["args"].append("--single-process")

# 크롤링 설정 (CRAWLING_SETTINGS)
CRAWLING_SETTINGS = {
    "delay_between_requests": 3,  # 3초 간격
    "max_retries": 5,  # 최대 5회 재시도
    "max_places_per_search": 30,  # 검색당 최대 30개 장소
    "wait_for_selector_timeout": 30000,  # 30초
    "iframe_wait_timeout": 15000,  # iframe 로드 대기시간 15초
    "scroll_attempts": 5,  # 스크롤 시도 횟수
    "scroll_delay": 2000,  # 스크롤 간 대기시간 2초
}

# 스텔스 설정 (STEALTH_SETTINGS)
STEALTH_SETTINGS = {
    "user_agent_rotation": True,
    "viewport_randomization": True,
    "webgl_randomization": True,
    "isolated_context": True,
    "random_typing_delay": True,
    "random_mouse_movement": True,
    "random_wait_times": True,
}

# 출력 설정 (OUTPUT_SETTINGS)
OUTPUT_SETTINGS = {
    "output_directory": "output",
    "timestamp_format": "%Y%m%d_%H%M%S",
    "supported_formats": ["excel", "csv", "json"],
    "encoding": "utf-8-sig",  # CSV용 BOM 포함 UTF-8
}

# 네이버 지도 관련 설정
NAVER_MAP_SETTINGS = {
    "base_url": "https://map.naver.com/v5/search",
    "search_input_selector": ".input_search",
    "search_iframe_name": "searchIframe",
    "result_selectors": [
        "ul li", 
        "li", 
        ".YwYLL", 
        "._3XamX", 
        ".TYaxT", 
        ".CHC5F",
        "[data-id]", 
        "div[data-place-id]", 
        ".place_bluelink",
        ".item_name", 
        ".item", 
        ".result"
    ],
    "business_name_keywords": [
        "예약", "광고", "영업", "리뷰", "서울", "부산", "대구", "인천", 
        "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", 
        "전북", "전남", "경북", "경남", "제주", "네이버페이", "톡톡", 
        "별점", "현재", "위치", "거리", "출발", "도착", "상세주소", 
        "저장", "더보기"
    ],
    "max_business_name_length": 30
}

# 스텔스 유저 에이전트 목록 (데스크톱 강화 버전)
FALLBACK_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15'
]

# 뷰포트 랜덤화용 해상도 목록
VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]

# 디버깅 설정
DEBUG_SETTINGS = {
    "save_html": True,  # HTML 저장 여부
    "html_save_dir": "debug_html",
    "screenshot_on_error": True,
    "verbose_logging": True if not (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT")) else False,
}

def get_all_settings() -> Dict[str, Any]:
    """모든 설정을 반환하는 함수"""
    return {
        "browser": BROWSER_SETTINGS,
        "crawling": CRAWLING_SETTINGS,
        "stealth": STEALTH_SETTINGS,
        "output": OUTPUT_SETTINGS,
        "naver_map": NAVER_MAP_SETTINGS,
        "debug": DEBUG_SETTINGS,
        "fallback_user_agents": FALLBACK_USER_AGENTS,
        "viewport_sizes": VIEWPORT_SIZES,
    }

def is_production() -> bool:
    """프로덕션 환경인지 확인"""
    return bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT"))

def get_browser_args() -> List[str]:
    """환경에 따른 브라우저 인수 반환"""
    args = BROWSER_SETTINGS["args"].copy()
    if is_production():
        args.extend([
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",  # 프로덕션에서는 이미지 로드 비활성화
            "--disable-javascript",  # 필요한 경우만 활성화
        ])
    return args