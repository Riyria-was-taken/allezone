from typing import Union, List
from pydantic import BaseModel, Field, validator
from enum import Enum
from dateutil.parser import parse
from datetime import datetime

class Device(str, Enum):
    PC = "PC"
    MOBILE = "MOBILE"
    TV = "TV"

class Action(str, Enum):
    VIEW = "VIEW"
    BUY = "BUY"

class Aggregate(str, Enum):
    COUNT = "COUNT"
    SUM_PRICE = "SUM_PRICE"

class ProductInfo(BaseModel):
    product_id: str
    brand_id: str
    category_id: str
    price: int = Field(ge=0)

class UserTag(BaseModel):
    time: str
    cookie: str
    country: str
    device: Device
    action: Action
    origin: str
    product_info: ProductInfo

    @validator('time')
    # TODO: it doesn't validate 2022-03-22T12:15:00.000Z
    def check_datetime_str(cls, time):
        parse(time)
        return time

class UserProfile(BaseModel):
    cookie: str
    views: List[UserTag]
    buys: List[UserTag]

class Statistics(BaseModel):
    columns: List[str]
    rows: List[List[str]]

class TimeRange:
    start: datetime
    end: datetime

###############################################################################

def parse_time_range(time_range: str):
    #TODO: validate
    parts = time_range.split(separator='_')
    ret = TimeRange()
    ret.start = parse(parts[0])
    ret.end = parts(parts[1])
    return ret
