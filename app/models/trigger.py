from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..utils.enums import TriggerType


class Trigger(BaseModel):
    userId: str
    type: TriggerType
    message: str
    metadata: Optional[Dict[str, Any]] = {}
