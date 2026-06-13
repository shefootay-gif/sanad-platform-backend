from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import image_routes, pdf_routes
import os

app = FastAPI(
    title="Sanad Platform API",
    description="Backend API for Document and Image Processing",
    version="1.0.0"
)

# Security: Allow CORS strictly for the frontend domains (Next.js & Mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Ensure temp directory exists
os.makedirs("temp", exist_ok=True)

# Include routers
app.include_router(image_routes.router, prefix="/api/image", tags=["Image Services"])
app.include_router(pdf_routes.router, prefix="/api/pdf", tags=["PDF Services"])

@app.get("/")
async def root():
    return {"message": "Welcome to Sanad Platform API"}
