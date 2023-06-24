import re
from typing import TYPE_CHECKING, Optional

from mqtransport.participants import Consumer, Producer
from mqtransport import MQApp
from pydantic import BaseModel, AnyHttpUrl, ConstrainedStr

from mqtransport.errors import ConsumeMessageError

from jira_reporter.app.jira_api import JiraError

if TYPE_CHECKING:
    from .state import MQAppState

class LabelStr(ConstrainedStr):
    min_length = 1
    curtail_length = 255


class DescriptionStr(ConstrainedStr):
    min_length = 1
    curtail_length = 28000


class CrashInfoStr(ConstrainedStr):
    min_length = 1
    curtail_length = 1000

class MC_DuplicateCrashFound(Consumer):

    """Send notification to jira that duplicate of crash is found"""

    name: str = "jira-reporter.crashes.duplicate"

    class Model(BaseModel):

        config_id: str
        """ Unique config id used to find integration """

        crash_id: str
        """ Unique id of crash """

        duplicate_count: int
        """ Count of similar crashes found (at least) """

    async def consume(self, msg: Model, app: MQApp):
        state: MQAppState = app.state

        config = await state.db.configs.get(msg.config_id)
        if config is None:
            self.logger.error(f"Can't find jira with id: {msg.config_id}")
            raise ConsumeMessageError()
        
        issue_id = await state.db.issues.get_issue(msg.crash_id)

        if issue_id is None:
            await state.producers.jira_report_undelivered.produce(
                config_id=config.id,
                update_rev=config.update_rev,
                error="Can't update duplicate count on non created issue!"
            )
            return
        
        try:
            description = await state.jira_api.get_issue_description(config, issue_id)
            print(description)
            description = re.sub(
                r"\*Duplicates\*: [0-9]+", 
                f"*Duplicates*: {msg.duplicate_count}",
                description
            )
            await state.jira_api.update_issue_description(config, issue_id, description)
        except JiraError as e:
            await state.producers.jira_report_undelivered.produce(
                config_id=msg.config_id,
                error=e.args[0]
            )
        


class MC_UniqueCrashFound(Consumer):

    """Send notification to jira that unique crash is found"""

    name: str = "jira-reporter.crashes.unique"

    class Model(BaseModel):

        config_id: str
        """ Unique config id used to find integration """

        crash_id: str
        """ Unique id of crash """

        crash_info: CrashInfoStr
        """ Short description for crash """

        crash_type: LabelStr
        """ Type of crash: crash, oom, timeout, leak, etc.. """

        crash_output: DescriptionStr
        """ Crash output (long multiline text) """

        crash_url: AnyHttpUrl # TODO: len
        """ URL can be opened to read crash information """

        project_name: LabelStr
        """ Name of project. Used for grouping JIRA issues """

        fuzzer_name: LabelStr
        """ Name of fuzzer. Used for grouping JIRA issues """

        revision_name: LabelStr
        """ Name of fuzzer revision. Used for grouping JIRA issues """

    async def consume(self, msg: Model, app: MQApp):
        state: MQAppState = app.state

        config = await state.db.configs.get(msg.config_id)
        if config is None:
            self.logger.error(f"Can't find jira with id: {msg.config_id}")
            raise ConsumeMessageError()

        self._logger.debug(("Consumed message:\ncrash_id: %s\n"
                           "crash url: %s\ncrash info: %s\n"
                           "crash type: %s\ncrash output: %s\n"
                           "project name: %s\nfuzzer name: %s\n"
                           "revision name: %s"),
                          msg.crash_id, msg.crash_url, msg.crash_info, 
                          msg.crash_type, msg.crash_output,
                          msg.project_name, msg.fuzzer_name,
                          msg.revision_name)

        description = f'''
        *Crash info*: {msg.crash_info}
        *Crash link*: {msg.crash_url}
        *Project name*: {msg.project_name}
        *Fuzzer name*: {msg.fuzzer_name}
        *Revision*: {msg.revision_name}
        *Duplicates*: 0
        {{noformat}}{msg.crash_output}{{noformat}}
        '''

        try:
            issue_id = await state.jira_api.create_issue(
                config=config,
                summary=msg.crash_info[:255],
                description=description,
                labels=[
                    msg.fuzzer_name,
                    msg.revision_name,
                    msg.crash_type
                ]
            )

            await state.db.issues.insert(msg.crash_id, issue_id)
        except JiraError as e:
            await state.producers.jira_report_undelivered.produce(
                config_id=msg.config_id,
                error=e.args[0]
            )


class MP_JiraIntegrationResult(Producer):
    name = "jira-reporter.integrations.result"

    class Model(BaseModel):
        config_id: str
        """ Unique config id used to find integration """

        error: Optional[str]
        """ Last error caused integration to fail """

        update_rev: str
        """ Update revision. Used to filter outdated messages """

class MP_JiraReportUndelivered(Producer):
    name = "jira-reporter.reports.undelivered"

    class Model(BaseModel):
        config_id: str
        """ Unique config id used to find integration """

        error: str
        """ Last error caused integration to fail """
