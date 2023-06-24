from typing import Any, Dict
from async_timeout import Optional
from contextlib import suppress
from pydantic import AnyHttpUrl, BaseSettings, BaseModel, EmailStr, Field, AnyUrl, root_validator

# fmt: off
with suppress(ModuleNotFoundError):
    import dotenv; dotenv.load_dotenv()
# fmt: on

class EnvironmentSettings(BaseSettings):
    name: str = Field(env="ENVIRONMENT", regex=r"^(dev|prod|test)$")
    shutdown_timeout: int = Field(env="SHUTDOWN_TIMEOUT")
    service_name: Optional[str] = Field(env="SERVICE_NAME")
    service_version: Optional[str] = Field(env="SERVICE_VERSION")
    commit_id: Optional[str] = Field(env="COMMIT_ID")
    build_date: Optional[str] = Field(env="BUILD_DATE")
    commit_date: Optional[str] = Field(env="COMMIT_DATE")
    git_branch: Optional[str] = Field(env="GIT_BRANCH")

    @root_validator(skip_on_failure=True)
    def check_values_for_production(cls, data: Dict[str, Any]):

        if data["name"] != "prod":
            return data

        vars = []
        for name, value in data.items():
            if value is None:
                vars.append(name.upper())

        if vars:
            raise ValueError(f"Variables must be set in production mode: {vars}")

        return data

class ShutdownSettings(BaseSettings):
    timeout: int

    class Config:
        env_prefix = "SHUTDOWN_"
        

class MessageQueues(BaseSettings):
    jira_reporter_internal: str
    jira_reporter: str
    api_gateway: str
    dlq: str

    class Config:
        env_prefix = "MQ_QUEUE_"


class MessageQueueSettings(BaseSettings):

    url: Optional[AnyUrl]
    broker: str = Field(regex="^sqs$")
    queues: MessageQueues
    username: str
    password: str
    region: str

    class Config:
        env_prefix = "MQ_"


class DatabaseSettings(BaseSettings):

    engine: str = Field(regex=r"^arangodb$")
    url: AnyHttpUrl
    username: str
    password: str
    name: str

    class Config:
        env_prefix = "DB_"


class CollectionSettings(BaseSettings):
    configs: str = "Configs"
    issues: str = "Issues"
    unsent_messages: str = "UnsentMessages"


class ServerSettings(BaseSettings):

    host: str = "0.0.0.0"
    port: str = "8080"

    class Config:
        env_prefix = "SERVER_"


class AppSettings(BaseModel):
    environment: EnvironmentSettings
    database: DatabaseSettings
    message_queue: MessageQueueSettings
    shutdown: ShutdownSettings
    collections: CollectionSettings
    server: ServerSettings
    

def load_app_settings():
    return AppSettings(
        environment=EnvironmentSettings(),
        database=DatabaseSettings(),
        message_queue=MessageQueueSettings(
            queues=MessageQueues(),
        ),
        shutdown=ShutdownSettings(),
        collections=CollectionSettings(),
        server=ServerSettings(),
    )
