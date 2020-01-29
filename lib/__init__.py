from lib.mappings import *
from lib.services import *
import datetime


def get_result_message(message: str):
    return {
        "message": message,
        "timestamp": str(datetime.datetime.now()),
    }
