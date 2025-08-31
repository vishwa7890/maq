from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "message": "FastAPI app is running"}

@app.get("/test")
async def test():
    return {"status": "ok", "endpoint": "/test"}

@app.get("/ping")
async def ping():
    return {"status": "ok", "service": "Test API"}
