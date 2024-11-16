from typing import Optional

from .base import BaseModel
from ..namespace import Namespace

class BeforeInteraction(BaseModel):
    defer: bool = False
    ephemerally: bool = False
    thinking: bool = False
    league_data: bool = False
    player_data: bool = False

    is_modal_response: bool = False

class BeforeView(BaseModel):
    all_components: Optional[BeforeInteraction] = None
    components: Optional[Namespace[str, BeforeInteraction]] = None