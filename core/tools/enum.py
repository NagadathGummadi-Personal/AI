from enum import Enum

from .constants import (
    JSON,
    TEXT,
    HUMAN,
    LLM,
    AGENT,
    STEP,
    FUNCTION,
    HTTP,
    DB,
    STRING,
    NUMBER,
    INTEGER,
    BOOLEAN,
    ARRAY,
    OBJECT,
)

class ToolReturnType(str, Enum):
    """Enumeration for tool return formats"""
    JSON = JSON
    TEXT = TEXT


class ToolReturnTarget(str, Enum):
    """Enumeration for tool return routing targets"""
    HUMAN = HUMAN #results sent to human directly
    LLM = LLM #results sent to llm
    AGENT = AGENT #results sent to agent
    STEP = STEP #results are part of workflow step


class ToolType(str, Enum):
    """Enumeration for tool types"""
    FUNCTION = FUNCTION
    HTTP = HTTP
    DB = DB


class ParameterType(str, Enum):
    """Enumeration for parameter types"""
    STRING = STRING
    NUMBER = NUMBER
    INTEGER = INTEGER
    BOOLEAN = BOOLEAN
    ARRAY = ARRAY
    OBJECT = OBJECT
