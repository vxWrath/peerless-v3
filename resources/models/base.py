
from pydantic import ConfigDict
from pydantic import BaseModel as PydanticBaseModel

class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)