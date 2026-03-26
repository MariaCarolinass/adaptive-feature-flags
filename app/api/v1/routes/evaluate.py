from fastapi import APIRouter, HTTPException, status

from app.dependencies import evaluation_service
from app.schemas.evaluate import EvaluateRequest, EvaluateResponse

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest):
    try:
        return evaluation_service.evaluate(
            feature_key=request.feature_key,
            user=request.user,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{evaluation_id}", response_model=EvaluateResponse)
def retrieve(evaluation_id: str):
    try:
        return evaluation_service.get_evaluation_by_id(evaluation_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{evaluation_id}", response_model=EvaluateResponse)
def update(evaluation_id: str, request: EvaluateRequest):
    try:
        return evaluation_service.update_evaluation(evaluation_id, request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(evaluation_id: str):
    try:
        evaluation_service.delete_evaluation(evaluation_id)
        return {}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("", response_model=list[EvaluateResponse])
def list():
    try:
        return evaluation_service.list_evaluations()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))