from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool

from model import AVAILABLE_MODELS, run_predict, run_all
from upload import validate_content_type, stream_image_to_disk

router = APIRouter(tags=["Predict"])


@router.post("/predict")
async def predict(
    file: UploadFile = File(...),
    model: str = Form("mobilenetv2"),
    quantized: bool = Form(False),
):
    if model not in AVAILABLE_MODELS:
        raise HTTPException(400, detail=f"Unknown model. Available: {AVAILABLE_MODELS}")

    validate_content_type(file)                 # wczesny filtr
    dest = await stream_image_to_disk(file)     # streaming + limit + magic + bezpieczna sciezka
    try:
        data = dest.read_bytes()
        result = await run_in_threadpool(run_predict, data, model, quantized)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Prediction failed: {e}")
    finally:
        dest.unlink(missing_ok=True)             # sprzatamy upload

    return {**result, "model": model, "quantized": quantized}


@router.post("/compare")
async def compare(file: UploadFile = File(...)):
    validate_content_type(file)
    dest = await stream_image_to_disk(file)
    try:
        data = dest.read_bytes()
        results = await run_in_threadpool(run_all, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Compare failed: {e}")
    finally:
        dest.unlink(missing_ok=True)
    return {"results": results}