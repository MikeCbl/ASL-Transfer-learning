from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from model import AVAILABLE_MODELS, get_session
from routes.predict import router as predict_router
from routes.classes import router as classes_router

production = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Rozgrzewka: wczytaj dostepne modele raz przy starcie.
    # try/except, zeby brak jednego pliku .onnx nie ubil calej aplikacji.
    for model_name in AVAILABLE_MODELS:
        for quantized in (False, True):
            try:
                get_session(model_name, quantized)
            except Exception as e:
                print(f"[warm-up] skipped model {model_name}, (quantized={quantized}): {e}")
    
    # app runs here
    yield 
    # cleanup if needed on shutdown

app = FastAPI(
    title="ASL Alphabet",
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else '/openapi.json',
    lifespan=lifespan
)


origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(classes_router)

@app.get('/health')
def health():
    """Health check endpoint to verify that the application is running."""
    return {'status': 'ok'}