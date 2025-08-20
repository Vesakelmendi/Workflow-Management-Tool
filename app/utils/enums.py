from enum import Enum


class NodeStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    REJECTED = "Rejected"


class ContentType(str, Enum):
    TASK = "task"
    NOTE = "note"
    ATTACHMENT = "attachment"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NodeType(str, Enum):
    INIT = "INIT"
    CONDITION = "CONDITION"
    MODIFY_MESSAGE = "MODIFY_MESSAGE"
    STORE_MESSAGE = "STORE_MESSAGE"


class TriggerType(str, Enum):
    USER_MESSAGE = "user-message"