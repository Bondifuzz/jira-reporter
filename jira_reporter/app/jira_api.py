from __future__ import annotations
from logging import Logger
import logging
from typing import TYPE_CHECKING

from contextlib import suppress
import json
import aiohttp

from jira_reporter.app.database.orm import ORMJiraConfig

if TYPE_CHECKING:
    from jira_reporter.app.database.abstract import IDatabase
    from typing import List


class JiraError(Exception):
    pass

class JiraConnectionError(JiraError):
    pass

class JiraAuthError(JiraError):
    pass


class JiraApi:
    _db: IDatabase
    _logger: Logger

    def __init__(self, db: IDatabase):
        self._db = db
        self._logger = logging.getLogger('JiraApi')

    async def verify_jira(self, config: ORMJiraConfig):
        issue_id = await self.create_issue(
            config, 
            "Test issue, please remove", 
            "Test issue, please remove", 
            []
        )

        # ignore if can't delete test issue
        with suppress(JiraError):
            await self.delete_issue(config, issue_id)
    
    async def delete_issue(self, config: ORMJiraConfig, issue_id: int):

        async with aiohttp.ClientSession() as client:
            try:
                async with await client.delete(
                    url=f"{config.url}/rest/api/2/issue/{issue_id}",
                    auth=aiohttp.BasicAuth(
                        config.username, 
                        config.password
                    ),
                ) as resp:

                    if resp.status == 401:
                        raise JiraAuthError('Invalid login or token!')
                    elif resp.status == 500:
                        raise JiraError('Server error!')
                    
                    elif resp.status == 400:
                        raise JiraError('Error occurred while deleting issue!')
                    elif resp.status == 403:
                        raise JiraError('User does not have permission to delete the issue!')
                    elif resp.status == 404:
                        raise JiraError('Issue not found!')
                    
                    elif resp.status != 204:
                        raise JiraError(f'Invalid response code({resp.status})!')

            except aiohttp.ClientConnectionError as e:
                raise JiraConnectionError("Can't connect to jira!")
            except aiohttp.ClientError as e:
                raise JiraError("Error in request: " + str(e))

    async def get_issue_description(self, config: ORMJiraConfig, issue_id: int) -> str:
        
        async with aiohttp.ClientSession() as client:
            try:
                async with await client.get(
                    url=f"{config.url}/rest/api/2/issue/{issue_id}",
                    auth=aiohttp.BasicAuth(
                        config.username, 
                        config.password
                    ),
                ) as resp:

                    if resp.status == 401:
                        raise JiraAuthError('Invalid login or token!')
                    elif resp.status == 500:
                        raise JiraError('Server error!')

                    elif resp.status == 404:
                        raise JiraError('Issue not found!')
                    
                    elif resp.status != 200:
                        raise JiraError(f'Invalid response code({resp.status})!')

                    else:
                        content = await resp.content.read()
                        issue_info = json.loads(content)
                        return issue_info['fields']['description']

            except aiohttp.ClientConnectionError as e:
                raise JiraConnectionError("Can't connect to jira!")
            except aiohttp.ClientError as e:
                raise JiraError("Error in request: " + str(e))

    async def update_issue_description(self, config: ORMJiraConfig, issue_id: int, description: str):
        
        async with aiohttp.ClientSession() as client:
            try:                
                async with await client.put(
                    url=f"{config.url}/rest/api/2/issue/{issue_id}",
                    auth=aiohttp.BasicAuth(
                        config.username, 
                        config.password
                    ),
                    json=dict(
                        fields=dict(
                            description=description
                        )
                    )
                ) as resp:

                    if resp.status == 401:
                        raise JiraAuthError('Invalid login or token!')
                    elif resp.status == 500:
                        raise JiraError('Server error!')

                    elif resp.status == 404:
                        raise JiraError('Issue not found!')
                    elif resp.status == 400:
                        err = (await resp.content.read()).decode()
                        self._logger.error('Failed to update issue. Reason - %s', err)
                        raise JiraError('Error occurred while updating issue!')
                    
                    elif resp.status != 204:
                        raise JiraError(f'Invalid response code({resp.status})!')

            except aiohttp.ClientConnectionError as e:
                raise JiraConnectionError("Can't connect to jira!")
            except aiohttp.ClientError as e:
                raise JiraError("Error in request: " + str(e))

    async def create_issue(self, config: ORMJiraConfig, summary: str, description: str, labels: List[str]) -> int:

        fields = dict(
            project={'key': config.project},
            issuetype={'name': config.issue_type},
            summary=summary,
            description=description,
            labels=labels,
        )

        if config.priority is not None:
            fields.update(
                priority={'name': config.priority},
            )

        #if config.assignee_id is not None:
        #    fields['assignee'] = {
        #        'id': config.assignee_id
        #    }

        async with aiohttp.ClientSession() as client:
            try:
                async with await client.post(
                    url=f"{config.url}/rest/api/2/issue",
                    auth=aiohttp.BasicAuth(
                        config.username, 
                        config.password
                    ),
                    json=dict(
                        fields=fields
                    )
                ) as resp:

                    if resp.status == 401:
                        raise JiraAuthError('Invalid login or token!')
                    elif resp.status == 500:
                        raise JiraError('Server error!')

                    elif resp.status == 400:
                        content = await resp.content.read()
                        errors: dict = json.loads(content)['errors']
                        raise JiraError(
                            "Wrong values in fields: " + ", ".join(errors.keys())
                        )

                    elif resp.status != 201:
                        raise JiraError(f'Invalid response code({resp.status})!')
                    
                    else: # resp.status == 201
                        content = await resp.content.read()
                        issue_info = json.loads(content)
                        return int(issue_info['id'])

            except aiohttp.ClientConnectionError as e:
                raise JiraConnectionError("Can't connect to jira!")
            except aiohttp.ClientError as e:
                raise JiraError("Error in request: " + str(e))

