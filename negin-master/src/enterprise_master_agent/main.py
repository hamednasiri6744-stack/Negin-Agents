import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "enterprise_master_agent.app:app",
        host=os.getenv("ema_host", "127.0.0.1"),
        port=int(os.getenv("ema_port", "8765")),
        reload=False,
    )
