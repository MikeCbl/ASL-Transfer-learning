from fastapi import APIRouter, HTTPException
from model import AVAILABLE_MODELS, get_session

router = APIRouter(
    # prefix='/api',
    tags=['Classes'],
)

@router.get('/classes')
async def get_classes(model: str = "resnet18"):
    """Returns class list for the specified model."""
    if model not in AVAILABLE_MODELS:
        raise HTTPException(400, detail=f"Unknown model. Available: {AVAILABLE_MODELS}")
    _, class_names = get_session(model, False)
    return {"classes": class_names}
