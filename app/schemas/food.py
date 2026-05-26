from pydantic import BaseModel
from pydantic import Field

class MonCreate(BaseModel):

    ten_mon: str = Field(
        min_length=2,
        max_length=100
    )

    gia: float = Field(gt=0)