"""
스텔스 크롤링을 위한 유틸리티 클래스
안티봇 시스템 우회를 위한 다양한 기법들을 구현
"""

import random
import time
import asyncio
from typing import Dict, List, Tuple, Optional
from fake_useragent import UserAgent
from config.settings import FALLBACK_USER_AGENTS, VIEWPORT_SIZES


class StealthUtils:
    """스텔스 크롤링을 위한 유틸리티 클래스"""
    
    def __init__(self):
        """StealthUtils 초기화"""
        self.ua = UserAgent()
        self.used_user_agents = set()
        
    def get_random_user_agent(self) -> str:
        """랜덤 User Agent 반환"""
        try:
            # fake_useragent 라이브러리 사용 시도
            user_agent = self.ua.random
            
            # 이미 사용한 User Agent는 피하기
            attempts = 0
            while user_agent in self.used_user_agents and attempts < 10:
                user_agent = self.ua.random
                attempts += 1
                
            self.used_user_agents.add(user_agent)
            return user_agent
            
        except Exception:
            # fallback to predefined agents
            available_agents = [
                agent for agent in FALLBACK_USER_AGENTS 
                if agent not in self.used_user_agents
            ]
            
            if not available_agents:
                # 모든 에이전트를 사용했다면 리셋
                self.used_user_agents.clear()
                available_agents = FALLBACK_USER_AGENTS
                
            user_agent = random.choice(available_agents)
            self.used_user_agents.add(user_agent)
            return user_agent
    
    def get_random_viewport(self) -> Dict[str, int]:
        """랜덤 뷰포트 크기 반환"""
        return random.choice(VIEWPORT_SIZES)
    
    async def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """랜덤 대기 시간"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def human_like_typing(self, page, selector: str, text: str) -> None:
        """인간과 같은 타이핑 패턴으로 텍스트 입력"""
        # 입력 필드 클릭
        await page.click(selector)
        await self.random_delay(0.2, 0.5)
        
        # 기존 텍스트 모두 선택 후 삭제
        await page.keyboard.press("Control+a")
        await self.random_delay(0.1, 0.3)
        await page.keyboard.press("Delete")
        await self.random_delay(0.2, 0.4)
        
        # 한 글자씩 타이핑
        for char in text:
            await page.keyboard.type(char)
            # 글자 간 랜덤 간격
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # 타이핑 완료 후 잠시 대기
        await self.random_delay(0.3, 0.7)
    
    async def random_mouse_movement(self, page) -> None:
        """랜덤 마우스 움직임"""
        viewport = page.viewport_size
        if not viewport:
            return
            
        # 현재 위치에서 랜덤하게 이동
        current_x = random.randint(100, viewport['width'] - 100)
        current_y = random.randint(100, viewport['height'] - 100)
        
        # 여러 단계로 나누어서 자연스럽게 이동
        for _ in range(random.randint(2, 5)):
            target_x = current_x + random.randint(-100, 100)
            target_y = current_y + random.randint(-50, 50)
            
            # 범위 내로 제한
            target_x = max(50, min(viewport['width'] - 50, target_x))
            target_y = max(50, min(viewport['height'] - 50, target_y))
            
            await page.mouse.move(target_x, target_y)
            await self.random_delay(0.1, 0.3)
            
            current_x, current_y = target_x, target_y
    
    async def random_scroll(self, page, iframe=None) -> None:
        """랜덤 스크롤 동작"""
        try:
            target = iframe if iframe else page
            
            # 페이지가 닫혔는지 확인
            if page.is_closed():
                return
            
            # 스크롤 방향과 거리 랜덤 결정
            scroll_direction = random.choice(['up', 'down'])
            scroll_distance = random.randint(200, 800)
            
            if scroll_direction == 'down':
                await target.mouse.wheel(0, scroll_distance)
            else:
                await target.mouse.wheel(0, -scroll_distance)
            
            await self.random_delay(0.5, 1.5)
        except Exception as e:
            # 브라우저가 닫혔거나 다른 오류 발생 시 무시
            pass
    
    async def simulate_reading_behavior(self, page, iframe=None) -> None:
        """읽기 행동 시뮬레이션"""
        try:
            target = iframe if iframe else page
            
            # 페이지가 닫혔는지 확인
            if page.is_closed():
                return
            
            # 페이지를 여러 번 스크롤하며 읽는 행동 시뮬레이션
            for _ in range(random.randint(2, 4)):
                if page.is_closed():
                    break
                    
                # 아래로 스크롤
                await target.mouse.wheel(0, random.randint(300, 600))
                await self.random_delay(1.0, 2.5)  # 읽는 시간
                
                # 가끔 위로 다시 스크롤 (재확인하는 행동)
                if random.random() < 0.3 and not page.is_closed():
                    await target.mouse.wheel(0, -random.randint(100, 300))
                    await self.random_delay(0.5, 1.0)
        except Exception as e:
            # 브라우저가 닫혔거나 다른 오류 발생 시 무시
            pass
    
    def get_random_headers(self) -> Dict[str, str]:
        """랜덤 HTTP 헤더 생성"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice([
                'ko-KR,ko;q=0.9,en;q=0.8',
                'ko,en-US;q=0.9,en;q=0.8',
                'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # 가끔 추가 헤더 포함
        if random.random() < 0.5:
            headers['Sec-CH-UA'] = '"Google Chrome";v="122", "Chromium";v="122", "Not=A?Brand";v="99"'
            headers['Sec-CH-UA-Mobile'] = '?0'
            headers['Sec-CH-UA-Platform'] = '"Windows"'
        
        return headers
    
    async def add_stealth_to_page(self, page) -> None:
        """페이지에 스텔스 기법 적용"""
        # JavaScript 실행하여 webdriver 속성 숨기기
        await page.add_init_script("""
            // webdriver 속성 제거
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // plugins 배열 추가
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // languages 속성 설정
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en'],
            });
            
            // permissions 권한 설정
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // chrome 객체 추가
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // WebGL 벤더 정보 랜덤화
            const getParameter = WebGLRenderingContext.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) Iris(TM) Graphics 6100';
                }
                return getParameter(parameter);
            };
        """)
        
        # 추가 스텔스 스크립트
        await page.add_init_script("""
            // iframe 감지 방지
            Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                get: function() {
                    return window;
                }
            });
            
            // 자동화 감지 방지
            Object.defineProperty(window, 'outerHeight', {
                get: () => window.innerHeight,
            });
            
            Object.defineProperty(window, 'outerWidth', {
                get: () => window.innerWidth,
            });
        """)
    
    def get_random_timing_pattern(self) -> Tuple[float, float, float]:
        """랜덤 타이밍 패턴 반환 (클릭 전 대기, 클릭 후 대기, 페이지 로드 대기)"""
        pre_click_delay = random.uniform(0.5, 1.5)
        post_click_delay = random.uniform(1.0, 2.5)
        page_load_delay = random.uniform(2.0, 4.0)
        
        return pre_click_delay, post_click_delay, page_load_delay
    
    async def simulate_human_interaction_pattern(self, page, iframe=None) -> None:
        """인간의 상호작용 패턴 시뮬레이션"""
        # 1. 마우스 움직임
        await self.random_mouse_movement(page)
        
        # 2. 짧은 대기
        await self.random_delay(0.3, 0.8)
        
        # 3. 스크롤 행동
        await self.random_scroll(page, iframe)
        
        # 4. 읽기 행동 시뮬레이션
        await self.simulate_reading_behavior(page, iframe)
        
        # 5. 최종 대기
        await self.random_delay(1.0, 2.0)