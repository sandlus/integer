# import os
# import uvicorn
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv

# from components.db import get_db_connection

# from components.chatbot import ChatRequest, ChatResponse, process_chat, router

# load_dotenv()

# app = FastAPI(title="Project Chatbot API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(router)
# @app.get("/")
# def root():
#     return {"status": "API is running"}


# @app.get("/health")
# def health():
#     return {"status": "healthy"}


# @app.get("/test-db")
# def test_db():
#     conn = None
#     try:
#         conn = get_db_connection()
#         if conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT NOW()")
#             result = cursor.fetchone()
#             cursor.close()
#             return {"db_status": "Connected", "current_time": str(result[0])}
#         return {"db_status": "Failed"}
#     except Exception as e:
#         return {"db_status": "Error", "details": str(e)}
#     finally:
#         if conn:
#             conn.close()


# @app.post("/chat", response_model=ChatResponse)
# def chat(request: ChatRequest):
#     try:
#         result = process_chat(request.query, request.session_id)
#         return ChatResponse(**result)
#     except Exception as e:
#         return ChatResponse(
#             responses=[f"❌ Error: {str(e)}"],
#             step=1.5,
#             lookup_type=None,
#             selected_ticket_id=None,
#             selected_site_id=None
#         )


# if __name__ == "__main__":
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)  

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from components.db import get_db_connection
from components.chatbot import ChatRequest, ChatResponse, process_chat, router

load_dotenv()

app = FastAPI(title="Project Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api")
def api_root():
    return {"status": "API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/test-db")
def test_db():
    conn = None
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT NOW()")
            result = cursor.fetchone()
            cursor.close()
            return {
                "db_status": "Connected",
                "current_time": str(result[0]),
            }

        return {"db_status": "Failed"}

    except Exception as e:
        return {"db_status": "Error", "details": str(e)}

    finally:
        if conn:
            conn.close()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = process_chat(request.query, request.session_id)
        return ChatResponse(**result)

    except Exception as e:
        return ChatResponse(
            responses=[f"❌ Error: {str(e)}"],
            step=1.5,
            lookup_type=None,
            selected_ticket_id=None,
            selected_site_id=None,
        )


BASE_DIR = Path(__file__).resolve().parent
BUILD_DIR = BASE_DIR / "build"

if BUILD_DIR.exists():
    static_dir = BUILD_DIR / "static"

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(BUILD_DIR / "index.html")

    @app.get("/{full_path:path}")
    def serve_react_routes(full_path: str):
        file_path = BUILD_DIR / full_path

        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(BUILD_DIR / "index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)