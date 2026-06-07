from pydantic import BaseModel, Field, ValidationError
from typing import Dict,List, Tuple,Optional,Literal

class MoveArgs(BaseModel):
    dx: int = Field()
    dy: int = Field()

class MoveArgsResponse(BaseModel):
    path: str 

class PlantCropArgs(BaseModel):
    x: int = Field()
    y: int = Field()

class Crop(BaseModel):
    pos: list[int]
    needs_water: bool
    planted: bool

class GameState(BaseModel):
    grid_size: list[int]
    player_pos: list[int]
    crops: Dict[str, Crop]
    water_available: bool
    goal_completed: bool

class AStarRequest(BaseModel):
    start_px: Tuple[int, int] = Field(
        description="Starting pixel coordinates (x, y)"
    )
    goal_px: Tuple[int, int] = Field(
        description="Goal pixel coordinates (x, y)"
    )
    obstacles_px: List[Tuple[int, int]] = Field(
        default_factory=list,
        description="List of obstacle pixel coordinates"
    )
    grid_width: int = Field(
        default=800,
        ge=1,
        description="Grid width in pixels"
    )
    grid_height: int = Field(
        default=600,
        ge=1,
        description="Grid height in pixels"
    )

class AStarResponse(BaseModel):
    path: Optional[str] = None

# class AStarResponse(BaseModel):
#     path: List[Tuple[int, int]]



# class CollectWaterResponse(BaseModel):
#     status: Literal["true"]
#     action: Literal["collect water"]
#     water_available: bool



class CollectWaterResponse(BaseModel):
    status: bool
    action: str
    water_available: bool


class MoveResponse(BaseModel):
	status: bool
	action: str
	player_pos: tuple[int, int]
	error: Optional[str] = None

class WaterResponse(BaseModel):
    status: bool
    action: str
    message: str


class PlantCropResponse(BaseModel):
    status: bool
    action: str
    error: Optional[str] = ""
    position: tuple[int, int]

class CollectWaterRequest(BaseModel):
    pass

class WaterRequest(BaseModel):
    pass




# def collect_water() -> str:
#     state["water_available"] = True

#     response = CollectWaterResponse(
#         status="true",
#         action="collect water",
#         water_available=state["water_available"]
#     )

#     return response.model_dump_json()