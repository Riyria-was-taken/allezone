from typing import Union, List
from fastapi import FastAPI, Query, status
from pydantic import BaseModel, Field, validator
from enum import Enum
from fastapi.responses import HTMLResponse

app = FastAPI()

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
    #2022-03-22T12:15:00.000Z
    time: str
    cookie: str
    country: str
    device: Device
    action: Action
    origin: str
    product_info: ProductInfo

    @validator('time')
    def check_datetime_str(cls, time):
        dateutil.parser.parse(time)
        return time

class UserProfile(BaseModel):
    cookie: str
    views: List[UserTag]
    buys: List[UserTag]

class Statistics(BaseModel):
    columns: List[str]
    rows: List[List[str]]
    

@app.post("/user_tags", status_code=status.HTTP_204_NO_CONTENT)
def user_tag(tag: UserTag):
    return HTMLResponse(content="")


@app.post("/user_profiles/{cookie}", response_model=UserProfile)
def user_profile(cookie: str, time_range: str, result: UserProfile,
        limit: int = Query(default=200, ge=0, le=200)):
    return result


@app.post("/aggregates", response_model=Statistics)
def aggregate(time_range: str, action: Action, aggregates: List[Aggregate], result: Statistics,
        origin: str = None, brand_id: str = None, category_id: str = None):
    return result

