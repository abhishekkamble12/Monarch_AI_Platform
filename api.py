"""
MonArch AI — FastAPI Server Launcher
Run with: python api.py
"""

import uvicorn

if __name__ == "__main__":
    print("Starting MonArch AI Incident Investigator API & Workstation...")
    print("Backend API Live at: http://127.0.0.1:8000")
    print("Swagger Docs at:    http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
