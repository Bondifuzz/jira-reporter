from __future__ import annotations
from typing import TYPE_CHECKING

from mqtransport import SQSApp

from .api_gateway import MC_DuplicateCrashFound, MC_UniqueCrashFound
from .api_gateway import MP_JiraReportUndelivered, MP_JiraIntegrationResult

from .internal import MP_VerifyJira, MC_VerifyJira
from jira_reporter.app.message_queue.state import MQAppState

if TYPE_CHECKING:
    from jira_reporter.app.settings import AppSettings
    from mqtransport import MQApp


class Producers:
    jira_report_undelivered: MP_JiraReportUndelivered
    jira_integration_result: MP_JiraIntegrationResult

    verify_jira: MP_VerifyJira


class MQAppInitializer:

    _settings: AppSettings
    _app: MQApp

    @property
    def app(self):
        return self._app

    def __init__(self, settings: AppSettings):
        self._settings = settings
        self._app = None

    async def do_init(self):

        self._app = await self._create_mq_app()
        self._app.state = MQAppState()

        try:
            await self._app.ping()
            await self._configure_channels()

        except:
            await self._app.shutdown()
            raise

    async def _create_mq_app(self):

        broker = self._settings.message_queue.broker.lower()
        settings = self._settings.message_queue

        if broker == "sqs":
            return await SQSApp.create(
                settings.username,
                settings.password,
                settings.region,
                settings.url,
            )

        raise ValueError(f"Unsupported message broker: {broker}")

    async def _create_own_channel(self):
        queues = self._settings.message_queue.queues
        ich = await self._app.create_consuming_channel(queues.jira_reporter)
        dlq = await self._app.create_producing_channel(queues.dlq)
        ich.use_dead_letter_queue(dlq)
        self._in_channel = ich

    async def _create_other_channels(self):
        queues = self._settings.message_queue.queues
        self._och_api_gateway = await self._app.create_producing_channel(queues.api_gateway)

        self._ich_internal = await self._app.create_consuming_channel(queues.jira_reporter_internal)
        self._och_internal = await self._app.create_producing_channel(queues.jira_reporter_internal)

    def _setup_internal_communication(self, producers: Producers):

        ich = self._ich_internal
        och = self._och_internal

        # Incoming messages
        ich.add_consumer(MC_VerifyJira())

        # Outcoming messages
        producers.verify_jira = MP_VerifyJira()
        och.add_producer(producers.verify_jira)

    def _setup_api_gateway_communication(self, producers: Producers):

        ich = self._in_channel
        och = self._och_api_gateway

        # Incoming messages
        ich.add_consumer(MC_UniqueCrashFound())
        ich.add_consumer(MC_DuplicateCrashFound())

        # Outcoming messages
        producers.jira_report_undelivered = MP_JiraReportUndelivered()
        producers.jira_integration_result = MP_JiraIntegrationResult()

        och.add_producer(producers.jira_report_undelivered)
        och.add_producer(producers.jira_integration_result)

    async def _configure_channels(self):
        await self._create_own_channel()
        await self._create_other_channels()

        state: MQAppState = self.app.state
        state.producers = Producers()

        self._setup_api_gateway_communication(state.producers)
        self._setup_internal_communication(state.producers)


async def mq_init(settings: AppSettings):
    initializer = MQAppInitializer(settings)
    await initializer.do_init()
    return initializer.app