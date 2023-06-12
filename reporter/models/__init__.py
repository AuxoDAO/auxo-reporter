"""
Types here are instantiated as subclasses of pydantic's `BaseModel`.
This means we get runtime deserialization and validation for free just by using type declarations
and a couple of pydantic helpers.

Use these in your code as python objects, then serialize to json by converting to a dict with `.dict()`
"""

from reporter.models.Account import *
from reporter.models.Claim import *
from reporter.models.Config import *
from reporter.models.ERC20 import *
from reporter.models.Redistribution import *
from reporter.models.Reward import *
from reporter.models.types import *
from reporter.models.Vote import *
from reporter.models.Writer import *
from reporter.models.RecipientWriter import *
from reporter.models.DB import DB
from reporter.models.SafeTx import *
