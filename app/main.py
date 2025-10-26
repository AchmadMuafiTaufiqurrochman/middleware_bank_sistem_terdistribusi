"""
Middleware Bank System - Main Application
FastAPI application with smart transaction routing
"""

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from app.config import Config
from app.routes import transactions, accounts, health

# Load configuration
config = Config()

# Setup logging
import os
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename=config.LOG_FILE,
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Middleware Bank System",
    description="API Gateway & Transaction Router for MiniBank Distributed System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health & Monitoring"])
app.include_router(accounts.router, prefix="/core", tags=["Accounts"])
app.include_router(transactions.router, prefix="/api/v1", tags=["Transactions"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Middleware Bank System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == '__main__':
    logger.info('='*60)
    logger.info('Starting Middleware Bank System...')
    logger.info(f'Core Bank URL: {config.CORE_URL}')
    logger.info(f'External Banks: {list(config.EXTERNAL_BANKS.keys())}')
    logger.info(f'Rate Limit: {config.RATE_LIMIT} req/min')
    logger.info('='*60)
    
    import uvicorn
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=3000,
        log_level=config.LOG_LEVEL.lower()
    )
