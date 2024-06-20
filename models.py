from pydantic import BaseModel


class BoxStage(BaseModel):
    id: str

class Box(BaseModel):
    id: str
    boxstage_set: list[BoxStage]