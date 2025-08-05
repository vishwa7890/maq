import uvicorn
from app.main import app

if __name__ == "__main__":
    # Print all available routes
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"{route.path} - {route.methods}")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
