#!/usr/bin/env python3
import uvicorn
import os

if __name__ == "__main__":
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
