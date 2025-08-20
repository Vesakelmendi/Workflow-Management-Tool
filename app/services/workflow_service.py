from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.workflow import Workflow, WorkflowCreate, Node, NodeCreate
from ..models.content import Content, ContentType
from ..models.trigger import Trigger
from ..utils.enums import NodeStatus, NodeType
from .permission_service import PermissionService

# In-memory storage 
workflows_db: List[Workflow] = []
content_db: List[Content] = []
next_workflow_id = 1
next_node_id = 1
next_content_id = 1
class WorkflowService:

    @staticmethod
    def create_workflow(workflow_data: WorkflowCreate, read_roles: Optional[List[str]] = None, write_roles: Optional[List[str]] = None) -> Workflow:
        global next_workflow_id
        workflow = Workflow(
            id=next_workflow_id,
            name=workflow_data.name,
            description=workflow_data.description,
            owner_id=workflow_data.owner_id,
            nodes=[],
            read_roles=read_roles or ["Analyst", "Category Manager"],
            write_roles=write_roles or ["Admin", "Category Manager"]
        )
        workflows_db.append(workflow)
        next_workflow_id += 1
        return workflow

    @staticmethod
    def get_workflow_by_id(workflow_id: int) -> Optional[Workflow]:
        return next((w for w in workflows_db if w.id == workflow_id), None)

    @staticmethod
    def get_workflows_by_user(user_id: int) -> List[Workflow]:
        # Filter workflows by read access
        return [w for w in workflows_db if PermissionService.check_read_permission(user_id, w.id)]

    @staticmethod
    def get_all_workflows() -> List[Workflow]:
        return workflows_db.copy()


    # Node Management
    @staticmethod
    def add_node_to_workflow(workflow_id: int, node_data: NodeCreate) -> Optional[Node]:
        global next_node_id
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return None

        existing_node_ids = [n.id for n in workflow.nodes]
        for dep_id in node_data.dependencies:
            if dep_id not in existing_node_ids:
                raise ValueError(f"Dependency node {dep_id} does not exist in workflow")

        node = Node(
            id=next_node_id,
            name=node_data.name,
            type=node_data.type,
            description=node_data.description,
            dependencies=node_data.dependencies,
            assigned_user_id=node_data.assigned_user_id,
            metadata=node_data.metadata,
            status=NodeStatus.PENDING
        )
        workflow.nodes.append(node)
        workflow.updated_at = datetime.now()
        next_node_id += 1
        return node

    @staticmethod
    def update_node_status(workflow_id: int, node_id: int, status: NodeStatus) -> bool:
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return False
        node = next((n for n in workflow.nodes if n.id == node_id), None)
        if not node:
            return False
        if status != NodeStatus.PENDING:
            for dep_id in node.dependencies:
                dep_node = next((n for n in workflow.nodes if n.id == dep_id), None)
                if not dep_node or dep_node.status != NodeStatus.COMPLETED:
                    raise ValueError(f"Cannot update node status: dependency {dep_id} is not completed")
        node.status = status
        node.updated_at = datetime.now()
        workflow.updated_at = datetime.now()
        return True

    @staticmethod
    def get_node_by_id(workflow_id: int, node_id: int) -> Optional[Node]:
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return None
        return next((n for n in workflow.nodes if n.id == node_id), None)


    @staticmethod
    def execute_workflow(workflow_id: int, user_id: int, trigger: Optional[Trigger] = None) -> Dict[str, Any]:
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return {"success": False, "message": "Workflow not found"}

        # Check write/execute permission
        if not PermissionService.check_write_permission(user_id, workflow_id):
            return {"success": False, "message": "User does not have permission to execute this workflow"}

        if not workflow.is_active:
            return {"success": False, "message": "Workflow is not active"}

        execution_result = {
            "workflow_id": workflow_id,
            "executed_by": user_id,
            "execution_time": datetime.now(),
            "trigger": trigger.dict() if trigger else None,
            "nodes_processed": [],
            "nodes_failed": [],
            "message_flow": [],
            "success": True,
        }

        # Validate workflow structure
        init_nodes = [n for n in workflow.nodes if n.type == NodeType.INIT.value]
        if not init_nodes:
            return {"success": False, "message": "No INIT node found in workflow"}
        if len(init_nodes) > 1:
            return {"success": False, "message": "Multiple INIT nodes found - only one allowed"}

        current_message = trigger.message if trigger else ""
        
        # Execute nodes in dependency order starting from INIT
        processed_nodes = set()
        
        def execute_node(node: Node, message: str) -> tuple[bool, str]:
            """Execute a single node and return (success, processed_message)"""
            try:
                WorkflowService.update_node_status(workflow_id, node.id, NodeStatus.IN_PROGRESS)
                
                if node.type == NodeType.INIT.value:
                    # INIT node just passes message through
                    result_message = message
                    
                elif node.type == NodeType.CONDITION.value:
                    # Check if username is "John"
                    username = trigger.userId if trigger else ""
                    if username != "John":
                        raise Exception(f"Condition failed: username '{username}' is not 'John'")
                    result_message = message
                    
                elif node.type == NodeType.MODIFY_MESSAGE.value:
                    # Append "Hello" to the message
                    result_message = f"{message} Hello"
                    
                elif node.type == NodeType.STORE_MESSAGE.value:
                    # Store the message
                    stored_data = {
                        "userId": trigger.userId if trigger else user_id,
                        "type": "user-message", 
                        "message": message,
                        "stored_at": datetime.now().isoformat()
                    }
                    execution_result["message_flow"].append({
                        "node_id": node.id,
                        "action": "stored",
                        "data": stored_data
                    })
                    result_message = message
                    
                else:
                    # Generic node - just pass message through
                    result_message = message

                WorkflowService.update_node_status(workflow_id, node.id, NodeStatus.COMPLETED)
                execution_result["nodes_processed"].append({
                    "node_id": node.id,
                    "type": node.type,
                    "input_message": message,
                    "output_message": result_message
                })
                processed_nodes.add(node.id)
                return True, result_message
                
            except Exception as e:
                WorkflowService.update_node_status(workflow_id, node.id, NodeStatus.REJECTED)
                execution_result["nodes_failed"].append({
                    "node_id": node.id, 
                    "type": node.type,
                    "error": str(e)
                })
                return False, message


        init_node = init_nodes[0]
        success, current_message = execute_node(init_node, current_message)
        
        if not success:
            execution_result["success"] = False
            return execution_result

        # Execute remaining nodes in dependency order
        remaining_nodes = [n for n in workflow.nodes if n.id != init_node.id]
        
        while remaining_nodes:
            executed_in_round = False
            
            for node in remaining_nodes[:]:
                # Only execute nodes whose dependencies are complete
                dependencies_met = all(dep_id in processed_nodes for dep_id in node.dependencies)
                
                if dependencies_met:
                    success, current_message = execute_node(node, current_message)
                    remaining_nodes.remove(node)
                    executed_in_round = True
                    
                    if not success:
                        execution_result["success"] = False
                        break
            
            # If no nodes were executed in this round, we can't resolve any more dependencies
            if not executed_in_round:
                for node in remaining_nodes:
                    execution_result["nodes_failed"].append({
                        "node_id": node.id,
                        "type": node.type, 
                        "error": "Unresolvable dependencies"
                    })
                execution_result["success"] = False
                break

        execution_result["final_message"] = current_message
        return execution_result


    @staticmethod
    def add_content(workflow_id: int, content_type: ContentType, data: Dict[str, Any], created_by: int, node_id: Optional[int] = None) -> Content:
        global next_content_id
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")

        content = Content(
            id=next_content_id,
            content_type=content_type,
            workflow_id=workflow_id,
            node_id=node_id,
            data=data,
            created_by=created_by,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        content_db.append(content)
        next_content_id += 1
        return content

    @staticmethod
    def get_workflow_content(workflow_id: int, user_id: int) -> List[Content]:
        # Verify user has read access
        if not PermissionService.check_read_permission(user_id, workflow_id):
            raise PermissionError("User does not have read access to this workflow")
        return [c for c in content_db if c.workflow_id == workflow_id]

    # Workflow statistics
    @staticmethod
    def get_workflow_statistics(workflow_id: int) -> Dict[str, Any]:
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return {}

        total_nodes = len(workflow.nodes)
        completed_nodes = len([n for n in workflow.nodes if n.status == NodeStatus.COMPLETED])
        in_progress_nodes = len([n for n in workflow.nodes if n.status == NodeStatus.IN_PROGRESS])
        pending_nodes = len([n for n in workflow.nodes if n.status == NodeStatus.PENDING])
        rejected_nodes = len([n for n in workflow.nodes if n.status == NodeStatus.REJECTED])

        progress_percentage = (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0

        return {
            "workflow_id": workflow_id,
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "in_progress_nodes": in_progress_nodes,
            "pending_nodes": pending_nodes,
            "rejected_nodes": rejected_nodes,
            "progress_percentage": round(progress_percentage, 2),
            "is_complete": total_nodes > 0 and completed_nodes == total_nodes,
            "content_count": len([c for c in content_db if c.workflow_id == workflow_id]),
        }
