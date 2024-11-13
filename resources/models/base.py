from pydantic import ConfigDict
from pydantic import BaseModel as PydanticBaseModel
from typing import Mapping, Any

class BaseModel(PydanticBaseModel, Mapping):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)
    
    def __len__(self) -> int:
        return len(self.model_dump())