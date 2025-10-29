"""
Entry point for the Middleware Application
Run with: python run.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8001,
        reload=True,
        log_level="info"
    )
