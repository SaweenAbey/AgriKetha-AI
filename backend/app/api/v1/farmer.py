from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
import httpx
from app.core.database import get_db
from app.core.config import settings
from app.core.logging_config import logger
from app.schemas.farm import FarmOut, FarmCreate, FarmUpdate, CropCreate, CropItem
from app.api.deps import require_farmer_or_admin

router = APIRouter(prefix="/farmer", tags=["Farmer Operations"])


@router.get("/profile", response_model=FarmOut)
async def get_farmer_farm_profile(
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Returns the farm profile associated with the current farmer.
    """
    user_id_str = current_user["id"]
    farm = await db.farms.find_one({"user_id": user_id_str})

    if not farm:
        # Create default farm if not found
        now = datetime.now(timezone.utc)
        farm_dict = {
            "user_id": user_id_str,
            "farm_name": f"{current_user.get('full_name', 'Farmer')}'s Farm",
            "district": current_user.get("district") or "Western",
            "area_or_village": None,
            "total_land_size_acres": 1.0,
            "soil_type": None,
            "irrigation_source": "Rainfed",
            "crops": [],
            "created_at": now,
            "updated_at": now
        }
        res = await db.farms.insert_one(farm_dict)
        farm = await db.farms.find_one({"_id": res.inserted_id})

    farm["id"] = str(farm["_id"])
    return FarmOut(**farm)


@router.put("/profile", response_model=FarmOut)
async def update_farmer_farm_profile(
    farm_in: FarmUpdate,
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Updates the farmer's farm profile and land details.
    """
    user_id_str = current_user["id"]
    update_data = {k: v for k, v in farm_in.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)

    await db.farms.update_one(
        {"user_id": user_id_str},
        {"$set": update_data},
        upsert=True
    )

    farm = await db.farms.find_one({"user_id": user_id_str})
    farm["id"] = str(farm["_id"])
    logger.info("Farmer %s updated farm profile", current_user["email"])
    return FarmOut(**farm)


@router.get("/crops", response_model=List[CropItem])
async def get_my_crops(
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Returns the list of crops registered for this farmer's farm.
    """
    user_id_str = current_user["id"]
    farm = await db.farms.find_one({"user_id": user_id_str})
    if not farm:
        return []
    return farm.get("crops", [])


@router.post("/crops", response_model=List[CropItem])
async def add_crop_to_farm(
    crop_in: CropCreate,
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Adds a new crop to the farmer's active cultivation list.
    """
    user_id_str = current_user["id"]
    crop_dict = crop_in.model_dump()

    await db.farms.update_one(
        {"user_id": user_id_str},
        {
            "$push": {"crops": crop_dict},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        upsert=True
    )

    farm = await db.farms.find_one({"user_id": user_id_str})
    logger.info("Farmer %s added crop '%s'", current_user["email"], crop_in.name)
    return farm.get("crops", [])


@router.delete("/crops/{crop_name}", response_model=List[CropItem])
async def remove_crop_from_farm(
    crop_name: str,
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Removes a crop from the farmer's cultivation list.
    """
    user_id_str = current_user["id"]
    await db.farms.update_one(
        {"user_id": user_id_str},
        {
            "$pull": {"crops": {"name": crop_name}},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )

    farm = await db.farms.find_one({"user_id": user_id_str})
    logger.info("Farmer %s removed crop '%s'", current_user["email"], crop_name)
    return farm.get("crops", []) if farm else []


@router.get("/queries")
async def get_my_queries(
    limit: int = 20,
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Returns past agricultural queries and diagnostic sessions submitted by this farmer.
    """
    user_id_str = current_user["id"]
    cursor = db.farmer_queries.find({"user_id": user_id_str}).sort("created_at", -1).limit(limit)
    queries = []
    async for q in cursor:
        q["id"] = str(q["_id"])
        del q["_id"]
        queries.append(q)
    return queries


@router.post("/query-agent")
async def ask_query_agent(
    question: str,
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db)
):
    """
    Sends farmer query to the Query Analysis AI Agent microservice and saves the record in MongoDB.
    """
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    now = datetime.now(timezone.utc)
    agent_response = None
    agent_status = "offline"

    # Forward to query agent service if running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(
                f"{settings.QUERY_AGENT_URL}/analyze",
                json={"question": question}
            )
            if res.status_code == 200:
                agent_response = res.json()
                agent_status = "success"
    except Exception as e:
        logger.warning("Could not reach AI Query Agent at %s: %s", settings.QUERY_AGENT_URL, e)
        agent_response = {
            "note": "AI Query Agent service is currently in background or offline.",
            "error": str(e)
        }

    # Record history in MongoDB
    record = {
        "user_id": current_user["id"],
        "farmer_name": current_user["full_name"],
        "question": question,
        "agent_status": agent_status,
        "agent_response": agent_response,
        "created_at": now
    }
    insert_res = await db.farmer_queries.insert_one(record)
    record["id"] = str(insert_res.inserted_id)
    del record["_id"]

    return record
