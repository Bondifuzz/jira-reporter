from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic import AnyHttpUrl, BaseModel
from typing import Optional


class ORMJiraConfig(BaseModel):
    id: Optional[str]
    update_rev: str

    url: AnyHttpUrl
    username: str
    password: str

    project: str
    issue_type: str
    priority: Optional[str]
    #assignee_id: Optional[int]

    
