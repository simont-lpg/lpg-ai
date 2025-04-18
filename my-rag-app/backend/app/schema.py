from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, ConfigDict
import pandas as pd


class Document(BaseModel):
    """Custom Document class that mimics Haystack Document with proper Pydantic v2 configuration."""
    
    content: str
    content_type: str = "text"
    id: Optional[str] = None
    meta: Dict[str, Any] = {}
    score: Optional[float] = None
    embedding: Optional[Union[list, pd.DataFrame]] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 