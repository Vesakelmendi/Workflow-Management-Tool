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
