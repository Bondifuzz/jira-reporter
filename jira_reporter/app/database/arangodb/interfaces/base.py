from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jira_reporter.app.settings import CollectionSettings
    from jira_reporter.app.database.arangodb.database import ArangoDB


class DBBase:

    _db: ArangoDB
    _collections: CollectionSettings

    def __init__(self, db: ArangoDB, collections: CollectionSettings):
        self._collections = collections
        self._db = db
