from pydantic import BaseModel, Field
from typing import Optional

class OnPublishItem(BaseModel):
    mediaServerId: str
    app: str
    stream: str
    params: str
    ip: str
    port: int
    vhost: str
    # Add other fields as necessary from ZLM documentation

class OnStreamChangedItem(BaseModel):
    mediaServerId: str
    app: str
    stream: str
    regist: bool
    schema_: str = Field(..., alias="schema") # 'schema' is a reserved keyword in some contexts, and aliased in Pydantic often if it conflicts or comes as 'schema'
    vhost: str

class OnRecordMp4Item(BaseModel):
    mediaServerId: str
    app: str
    stream: str
    file_path: str
    file_size: int
    folder: str
    start_time: int
    time_len: float
    url: str
    vhost: str

class HookResponse(BaseModel):
    code: int = 0
    msg: str = "success"
