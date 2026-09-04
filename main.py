from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# WARNING: allow_origins=["*"] is permissive. Lock this down to your frontend domain in production.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Hello from Rezpharma-Data. Service is running."}

@app.get("/health")
async def health():
    return {"status": "ok"}
