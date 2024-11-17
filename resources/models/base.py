from pydantic import ConfigDict, model_validator
from pydantic import BaseModel as PydanticBaseModel
from typing import Mapping, Any

from ..namespace import Namespace

class BaseModel(PydanticBaseModel, Mapping):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @model_validator(mode='before')
    def before(cls, values):
        values = Namespace(values)

        for key, field in cls.model_fields.items():
            if field.default_factory is not None and values.get(key, None) is None:
                values[key] = field.default_factory()

        return values

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)
    
    def __len__(self) -> int:
        return len(self.model_dump())