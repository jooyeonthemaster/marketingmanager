"""
네이버 플레이스 순위 크롤링 API 서버
FastAPI를 사용한 웹 API 서버 구현
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn

from src.crawler.naver_map_crawler import NaverMapCrawler, crawl_naver_map, crawl_multiple_keywords
from config.settings import is_production, get_all_settings


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 전역 크롤러 인스턴스 (재사용을 위해)
crawler_instance: Optional[NaverMapCrawler] = None
active_tasks: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # 시작 시
    logger.info("FastAPI 서버 시작")
    logger.info(f"환경: {'Production' if is_production() else 'Development'}")
    
    yield
    
    # 종료 시
    global crawler_instance
    if crawler_instance:
        await crawler_instance.close()
    logger.info("FastAPI 서버 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="네이버 플레이스 순위 크롤링 API",
    description="네이버 지도에서 키워드별 플레이스 순위를 크롤링하는 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not is_production() else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic 모델들
class CrawlRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100, description="검색할 키워드")
    max_results: int = Field(default=10, ge=1, le=50, description="최대 결과 수 (1-50)")
    save_format: str = Field(default="json", regex="^(json|csv|both)$", description="저장 형식")

class MultipleCrawlRequest(BaseModel):
    keywords: List[str] = Field(..., min_items=1, max_items=10, description="검색할 키워드 목록 (최대 10개)")
    max_results: int = Field(default=10, ge=1, le=30, description="키워드당 최대 결과 수")
    save_format: str = Field(default="json", regex="^(json|csv|both)$", description="저장 형식")

class PlaceResult(BaseModel):
    rank: int
    name: str
    raw_text: str
    keyword: str
    extracted_at: str

class CrawlResponse(BaseModel):
    success: bool
    keyword: str
    results: List[PlaceResult]
    total_count: int
    execution_time: float
    saved_files: List[str] = []

class MultipleCrawlResponse(BaseModel):
    success: bool
    results: Dict[str, List[PlaceResult]]
    total_keywords: int
    total_results: int
    execution_time: float
    saved_files: List[str] = []

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    keyword: Optional[str] = None
    keywords: Optional[List[str]] = None
    progress: int = 0  # 0-100
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# 유틸리티 함수들
def generate_task_id() -> str:
    """태스크 ID 생성"""
    return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"

async def save_results(results: List[Dict[str, Any]], keyword: str, save_format: str, crawler: NaverMapCrawler) -> List[str]:
    """결과 저장"""
    saved_files = []
    
    if save_format in ["json", "both"]:
        json_file = await crawler.save_results_to_json(results, keyword)
        saved_files.append(json_file)
    
    if save_format in ["csv", "both"]:
        csv_file = await crawler.save_results_to_csv(results, keyword)
        saved_files.append(csv_file)
    
    return saved_files


# API 엔드포인트들
@app.get("/", summary="API 정보")
async def root():
    """API 기본 정보"""
    return {
        "service": "네이버 플레이스 순위 크롤링 API",
        "version": "1.0.0",
        "status": "running",
        "environment": "production" if is_production() else "development",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", summary="헬스 체크")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "production" if is_production() else "development"
    }

@app.get("/settings", summary="설정 정보")
async def get_settings():
    """현재 설정 정보 반환"""
    settings = get_all_settings()
    # 민감한 정보 제외
    if "fallback_user_agents" in settings:
        settings["fallback_user_agents"] = f"{len(settings['fallback_user_agents'])}개 User Agent"
    
    return {
        "settings": settings,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/crawl", response_model=CrawlResponse, summary="단일 키워드 크롤링")
async def crawl_single_keyword(request: CrawlRequest):
    """단일 키워드에 대한 플레이스 순위 크롤링"""
    start_time = datetime.now()
    
    try:
        logger.info(f"단일 크롤링 요청: {request.keyword}")
        
        # 크롤링 실행
        results = await crawl_naver_map(request.keyword, request.max_results)
        
        # 크롤러 인스턴스로 파일 저장
        crawler = NaverMapCrawler()
        try:
            saved_files = await save_results(results, request.keyword, request.save_format, crawler)
        finally:
            await crawler.close()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        response = CrawlResponse(
            success=True,
            keyword=request.keyword,
            results=[PlaceResult(**result) for result in results],
            total_count=len(results),
            execution_time=execution_time,
            saved_files=saved_files
        )
        
        logger.info(f"크롤링 완료: {request.keyword} - {len(results)}개 결과")
        return response
        
    except Exception as e:
        logger.error(f"크롤링 실패: {request.keyword} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"크롤링 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/crawl/multiple", response_model=MultipleCrawlResponse, summary="다중 키워드 크롤링")
async def crawl_multiple_keywords_endpoint(request: MultipleCrawlRequest):
    """여러 키워드에 대한 배치 크롤링"""
    start_time = datetime.now()
    
    try:
        logger.info(f"다중 크롤링 요청: {len(request.keywords)}개 키워드")
        
        # 크롤링 실행
        all_results = await crawl_multiple_keywords(request.keywords, request.max_results)
        
        # 결과 변환
        converted_results = {}
        total_results = 0
        saved_files = []
        
        crawler = NaverMapCrawler()
        try:
            for keyword, results in all_results.items():
                converted_results[keyword] = [PlaceResult(**result) for result in results]
                total_results += len(results)
                
                # 파일 저장
                if results:  # 결과가 있는 경우만 저장
                    files = await save_results(results, keyword, request.save_format, crawler)
                    saved_files.extend(files)
        finally:
            await crawler.close()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        response = MultipleCrawlResponse(
            success=True,
            results=converted_results,
            total_keywords=len(request.keywords),
            total_results=total_results,
            execution_time=execution_time,
            saved_files=saved_files
        )
        
        logger.info(f"다중 크롤링 완료: {len(request.keywords)}개 키워드, {total_results}개 결과")
        return response
        
    except Exception as e:
        logger.error(f"다중 크롤링 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"다중 크롤링 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/crawl/async", summary="비동기 크롤링 시작")
async def start_async_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """비동기 크롤링 작업 시작"""
    task_id = generate_task_id()
    
    # 태스크 상태 초기화
    active_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "keyword": request.keyword,
        "progress": 0,
        "results": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }
    
    # 백그라운드 태스크 시작
    background_tasks.add_task(run_async_crawl, task_id, request)
    
    logger.info(f"비동기 크롤링 태스크 시작: {task_id}")
    return {"task_id": task_id, "status": "started"}

async def run_async_crawl(task_id: str, request: CrawlRequest):
    """비동기 크롤링 실행"""
    try:
        # 상태 업데이트: 실행 중
        active_tasks[task_id]["status"] = "running"
        active_tasks[task_id]["progress"] = 10
        
        # 크롤링 실행
        results = await crawl_naver_map(request.keyword, request.max_results)
        
        active_tasks[task_id]["progress"] = 80
        
        # 파일 저장
        crawler = NaverMapCrawler()
        try:
            saved_files = await save_results(results, request.keyword, request.save_format, crawler)
        finally:
            await crawler.close()
        
        # 완료 상태 업데이트
        active_tasks[task_id].update({
            "status": "completed",
            "progress": 100,
            "results": {
                "keyword": request.keyword,
                "total_count": len(results),
                "results": results,
                "saved_files": saved_files
            },
            "completed_at": datetime.now().isoformat()
        })
        
        logger.info(f"비동기 크롤링 완료: {task_id}")
        
    except Exception as e:
        # 실패 상태 업데이트
        active_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })
        
        logger.error(f"비동기 크롤링 실패: {task_id} - {str(e)}")

@app.get("/tasks/{task_id}", response_model=TaskStatus, summary="태스크 상태 조회")
async def get_task_status(task_id: str):
    """태스크 상태 조회"""
    if task_id not in active_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="태스크를 찾을 수 없습니다"
        )
    
    return TaskStatus(**active_tasks[task_id])

@app.get("/tasks", summary="모든 태스크 목록")
async def get_all_tasks():
    """모든 태스크 목록 조회"""
    return {
        "total_tasks": len(active_tasks),
        "tasks": list(active_tasks.values())
    }

@app.delete("/tasks/{task_id}", summary="태스크 삭제")
async def delete_task(task_id: str):
    """태스크 삭제"""
    if task_id not in active_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="태스크를 찾을 수 없습니다"
        )
    
    del active_tasks[task_id]
    return {"message": "태스크가 삭제되었습니다"}

@app.get("/files/{filename}", summary="결과 파일 다운로드")
async def download_file(filename: str):
    """결과 파일 다운로드"""
    file_path = os.path.join("output", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.get("/files", summary="저장된 파일 목록")
async def list_files():
    """저장된 결과 파일 목록"""
    output_dir = "output"
    if not os.path.exists(output_dir):
        return {"files": []}
    
    files = []
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            files.append({
                "filename": filename,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return {"files": files}


# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "내부 서버 오류가 발생했습니다"}
    )


# 서버 실행
if __name__ == "__main__":
    host = os.getenv("FASTAPI_HOST", "127.0.0.1")
    port = int(os.getenv("FASTAPI_PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=not is_production(),
        log_level="info" if not is_production() else "warning"
    )