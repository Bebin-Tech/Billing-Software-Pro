import logging
import time
from collections import defaultdict, deque
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.core.database import engine
from app.api.routes import router
from app.reports.sales import router as reports_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = FastAPI(title='GST Billing Pro', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(','), allow_credentials=True,
                   allow_methods=['GET','POST','PUT','DELETE'], allow_headers=['Authorization','Content-Type','X-Company-ID'])
app.include_router(router)
app.include_router(reports_router)
attempts = defaultdict(deque)


@app.middleware('http')
async def guards(request: Request, call_next):
    started = time.monotonic()
    if request.url.path.startswith('/api/v1/auth/') and request.method == 'POST':
        key = request.client.host if request.client else 'unknown'
        queue = attempts[key]
        while queue and started - queue[0] > 60: queue.popleft()
        if len(queue) >= 30:
            return JSONResponse({'detail': 'Too many requests; retry in one minute'}, status_code=429)
        queue.append(started)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Cache-Control'] = 'no-store'
    logging.info('%s %s %s %.3fs', request.method, request.url.path, response.status_code, time.monotonic()-started)
    return response


@app.exception_handler(IntegrityError)
async def conflict(request, exc):
    return JSONResponse({'detail': 'Duplicate record or invalid reference'}, status_code=409)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/health/ready')
def ready():
    try:
        with engine.connect() as connection: connection.execute(text('SELECT 1'))
        return {'status': 'ready'}
    except Exception:
        return JSONResponse({'status': 'database unavailable'}, status_code=503)
