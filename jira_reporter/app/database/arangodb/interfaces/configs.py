from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple

from jira_reporter.app.database.arangodb.interfaces.base import DBBase
from jira_reporter.app.database.errors import DBAlreadyExistsError, DBRecordNotFoundError
from jira_reporter.app.database.orm import ORMJiraConfig
from jira_reporter.app.database.abstract import IConfigs
from .util import (
    maybe_already_exists,
    maybe_not_found,
    maybe_unknown_error,
)

if TYPE_CHECKING:
    from aioarangodb.collection import StandardCollection
    from jira_reporter.app.settings import CollectionSettings
    from jira_reporter.app.database.arangodb.database import ArangoDB


class DBConfigs(DBBase, IConfigs):

    _col_configs: StandardCollection

    def __init__(
        self,
        db: ArangoDB,
        collections: CollectionSettings,
    ):
        self._col_configs = db._db[collections.configs]
        super().__init__(db, collections)

    @maybe_unknown_error
    async def get(self, config_id: str) -> Optional[ORMJiraConfig]:
        doc_dict = await self._col_configs.get(config_id)
        if doc_dict is None:
            return None
        doc_dict["id"] = doc_dict["_key"]
        return ORMJiraConfig(**doc_dict)

    @maybe_unknown_error
    @maybe_already_exists(DBAlreadyExistsError)
    async def insert(self, config: ORMJiraConfig) -> None:
        doc_dict = config.dict(exclude={"id"})
        if config.id is not None:
            doc_dict["_key"] = config.id
        res = await self._col_configs.insert(doc_dict)
        config.id = res['_key']

    # TODO: 
    @maybe_unknown_error
    @maybe_not_found(DBRecordNotFoundError)
    async def update(self, config: ORMJiraConfig) -> Tuple[ORMJiraConfig, ORMJiraConfig]:
        doc_dict = config.dict(exclude={"id"})
        doc_dict["_key"] = config.id
        res = await self._col_configs.update(
            doc_dict, 
            return_old=True, 
            return_new=True
        )
        return (
            ORMJiraConfig(**res['old']), 
            ORMJiraConfig(**res['new'])
        )

    @maybe_unknown_error
    @maybe_not_found(DBRecordNotFoundError)
    async def delete(self, config_id: str) -> None:
        await self._col_configs.delete(config_id)

