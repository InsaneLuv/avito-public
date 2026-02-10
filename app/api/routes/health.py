from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def _():
    print("healthy")
