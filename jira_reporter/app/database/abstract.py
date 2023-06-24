from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from abc import abstractmethod, ABCMeta
from ..util import testing_only

if TYPE_CHECKING:
    from ..settings import AppSettings
    from .orm import ORMJiraConfig


class IConfigs(metaclass=ABCMeta):
    @abstractmethod
    async def get(self, config_id: str) -> Optional[ORMJiraConfig]:
        pass

    @abstractmethod
    async def insert(self, config: ORMJiraConfig) -> None:
        pass

    @abstractmethod
    async def update(self, config: ORMJiraConfig) -> Tuple[ORMJiraConfig, ORMJiraConfig]:
        pass

    @abstractmethod
    async def delete(self, config_id: str) -> None:
        pass

class IIssues(metaclass=ABCMeta):
    @abstractmethod
    async def get_issue(self, crash_id: str) -> Optional[int]:
        pass

    @abstractmethod
    async def insert(self, crash_id: str, issue_id: int) -> None:
        pass

class IUnsentMessages(metaclass=ABCMeta):

    """
    Used for saving/loading MQ unsent messages from database.
    """

    @abstractmethod
    async def save_unsent_messages(self, messages: Dict[str, list]):
        pass

    @abstractmethod
    async def load_unsent_messages(self) -> Dict[str, list]:
        pass

class IDatabase(metaclass=ABCMeta):

    """Used for managing database"""

    @classmethod
    @abstractmethod
    async def create(cls, settings: AppSettings):
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @property
    @abstractmethod
    def configs(self) -> IConfigs:
        pass

    @property
    @abstractmethod
    def issues(self) -> IIssues:
        pass

    @property
    @abstractmethod
    def unsent_mq(self) -> IUnsentMessages:
        pass

    @abstractmethod
    @testing_only
    async def truncate_all_collections(self) -> None:
        pass
