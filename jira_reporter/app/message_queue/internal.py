from pydantic import BaseModel

from mqtransport import MQApp
from mqtransport.participants import Consumer, Producer
from jira_reporter.app.jira_api import JiraError

from jira_reporter.app.message_queue.state import MQAppState

class MP_VerifyJira(Producer):
    name = "jira-reporter.internal.verify"
    class Model(BaseModel):
        config_id: str
        update_rev: str

class MC_VerifyJira(Consumer):
    name = "jira-reporter.internal.verify"
    class Model(BaseModel):
        config_id: str
        update_rev: str

    async def consume(self, msg: Model, app: MQApp):
        state: MQAppState = app.state
        config = await state.db.configs.get(msg.config_id)
        if config and config.update_rev == msg.update_rev:
            try:
                await state.jira_api.verify_jira(config)
                await state.producers.jira_integration_result.produce(
                    config_id=config.id,
                    update_rev=config.update_rev,
                    error=None
                )
            except JiraError as e:
                await state.producers.jira_integration_result.produce(
                    config_id=config.id,
                    update_rev=config.update_rev,
                    error=e.args[0]
                )
        # TODO: any reaction?
        #else:
        #    pass