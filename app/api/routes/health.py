from typing import Any

from fastapi import APIRouter

router = APIRouter(include_in_schema=False)


@router.get("/health")
async def _():
    print("healthy")
