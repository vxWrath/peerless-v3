from typing import Optional

from .base import BaseModel
from ..namespace import Namespace

class BeforeInteraction(BaseModel):
    defer: Optional[bool]=False
    ephemerally: Optional[bool]=False
    thinking: Optional[bool]=False
    league_data: Optional[bool]=False
    player_data: Optional[bool]=False

    is_modal_response: Optional[bool]=False

class BeforeView(BaseModel):
    all_components: Optional[BeforeInteraction] = None
    components: Optional[Namespace[str, BeforeInteraction]] = None