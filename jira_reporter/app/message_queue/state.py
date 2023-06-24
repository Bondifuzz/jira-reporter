from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..jira_api import JiraApi
    from jira_reporter.app.settings import AppSettings
    from jira_reporter.app.database.abstract import IDatabase
    from jira_reporter.app.message_queue.instance import Producers



class MQAppState:
    jira_api: JiraApi
    db: IDatabase
    settings: AppSettings
    producers: Producers