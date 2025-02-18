
from datetime import datetime, timedelta, UTC
from enum import Enum
from pydantic import BaseModel
from pydantic_core import ValidationError
from typing import Callable, Dict, List
import logging

logger = logging.getLogger()

class Procedure(str, Enum):
    HELLO_WORLD = 'hello_world'

class ProcedureArguments:

    class HelloWorld(BaseModel):
        sender: str

class LambdaEvent(BaseModel):
    procedure: Procedure
    arguments: dict = {}

class LambdaResponse(BaseModel):
    status_code: int = 200
    body: str = 'Success'

class LambdaProcedureMap(Dict[Procedure, Callable[[dict], LambdaResponse]]):

    def __init__(self):
        self[Procedure.HELLO_WORLD] = self.hello_world
    
    def hello_world(
        self, 
        arguments: dict,
    ) -> LambdaResponse:
        try:
            parsed_arguments = ProcedureArguments.HelloWorld(**arguments)

        except ValidationError as e:
            logger.error(e)

            return LambdaResponse(
                status_code=400, 
                body=str(e),
            )
    
        sender = parsed_arguments.sender

        return LambdaResponse(body=f'Hello from Lambda, {sender}!')
