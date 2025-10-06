from enum import Enum

class ToolReturnType(str, Enum):
    """Enumeration for tool return formats"""
    JSON = "json"
    TEXT = "text"


class ToolReturnTarget(str, Enum):
    """Enumeration for tool return routing targets"""
    HUMAN = "human" #results sent to human directly
    LLM = "llm" #results sent to llm
    AGENT = "agent" #results sent to agent
    STEP = "step" #results are part of workflow step


class ToolType(str, Enum):
    """Enumeration for tool types"""
    FUNCTION = "function"
    HTTP = "http"
    DB = "db"


class ParameterType(str, Enum):
    """Enumeration for parameter types"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
