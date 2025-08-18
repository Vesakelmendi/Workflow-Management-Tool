from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.workflow import Workflow, WorkflowCreate, Node, NodeCreate
from ..models.content import Content, Task, Note, Attachment
from ..utils.enums import NodeStatus, ContentType


# In-memory storage
workflows_db: List[Workflow] = []
content_db: List[Content] = []
next_workflow_id = 1
next_node_id = 1
next_content_id = 1


class WorkflowService:
    @staticmethod
    def create_workflow(workflow_data: WorkflowCreate) -> Workflow:
        """Create a new workflow"""
        global next_workflow_id
        
        workflow = Workflow(
            id=next_workflow_id,
            name=workflow_data.name,
            description=workflow_data.description,
            owner_id=workflow_data.owner_id,
            nodes=[]
        )
        
        workflows_db.append(workflow)
        next_workflow_id += 1
        
        return workflow

    @staticmethod
    def get_workflow_by_id(workflow_id: int) -> Optional[Workflow]:
        """Get workflow by ID"""
        return next((w for w in workflows_db if w.id == workflow_id), None)

    @staticmethod
    def get_workflows_by_user(user_id: int) -> List[Workflow]:
        """Get all workflows owned by a user"""
        return [w for w in workflows_db if w.owner_id == user_id]

    @staticmethod
    def get_all_workflows() -> List[Workflow]:
        """Get all workflows"""
        return workflows_db.copy()

    @staticmethod
    def update_workflow(workflow_id: int, updates: Dict[str, Any]) -> Optional[Workflow]:
        """Update workflow details"""
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return None
        
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.now()
        return workflow

    @staticmethod
    def delete_workflow(workflow_id: int) -> bool:
        """Delete a workflow"""
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if workflow:
            workflows_db.remove(workflow)
            # Also remove associated content
            global content_db
            content_db = [c for c in content_db if c.workflow_id != workflow_id]
            return True
        return False

    @staticmethod
    def add_node_to_workflow(workflow_id: int, node_data: NodeCreate) -> Optional[Node]:
        """Add a node to a workflow"""
        global next_node_id
        
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return None
        
        # Validate dependencies exist in the workflow
        existing_node_ids = [n.id for n in workflow.nodes]
        for dep_id in node_data.dependencies:
            if dep_id not in existing_node_ids:
                raise ValueError(f"Dependency node {dep_id} does not exist in workflow")
        
        node = Node(
            id=next_node_id,
            name=node_data.name,
            description=node_data.description,
            dependencies=node_data.dependencies,
            assigned_user_id=node_data.assigned_user_id,
            metadata=node_data.metadata
        )
        
        workflow.nodes.append(node)
        workflow.updated_at = datetime.now()
        next_node_id += 1
        
        return node

    @staticmethod
    def update_node_status(workflow_id: int, node_id: int, status: NodeStatus) -> bool:
        """Update the status of a node"""
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return False
        
        node = next((n for n in workflow.nodes if n.id == node_id), None)
        if not node:
            return False
        
        # Check if dependencies are satisfied for non-pending status
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
    def execute_workflow(workflow_id: int, user_id: int) -> Dict[str, Any]:
        """Execute a workflow by processing nodes"""
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return {"success": False, "message": "Workflow not found"}
        
        if not workflow.is_active:
            return {"success": False, "message": "Workflow is not active"}
        
        execution_result = {
            "workflow_id": workflow_id,
            "executed_by": user_id,
            "execution_time": datetime.now(),
            "nodes_processed": [],
            "nodes_failed": [],
            "success": True
        }
        
        # Find nodes that can be executed (dependencies satisfied)
        executable_nodes = []
        for node in workflow.nodes:
            if node.status == NodeStatus.PENDING:
                # Check if all dependencies are completed
                dependencies_met = True
                for dep_id in node.dependencies:
                    dep_node = next((n for n in workflow.nodes if n.id == dep_id), None)
                    if not dep_node or dep_node.status != NodeStatus.COMPLETED:
                        dependencies_met = False
                        break
                
                if dependencies_met:
                    executable_nodes.append(node)
        
        # Execute eligible nodes
        for node in executable_nodes:
            try:
                # Simulate node execution
                WorkflowService.update_node_status(workflow_id, node.id, NodeStatus.IN_PROGRESS)
                
                # Here you would implement actual node execution logic
                # For now, we'll just mark as completed
                WorkflowService.update_node_status(workflow_id, node.id, NodeStatus.COMPLETED)
                
                execution_result["nodes_processed"].append(node.id)
            except Exception as e:
                WorkflowService.update_node_status(workflow_id, node.id, NodeStatus.REJECTED)
                execution_result["nodes_failed"].append({"node_id": node.id, "error": str(e)})
                execution_result["success"] = False
        
        return execution_result

    @staticmethod
    def get_workflow_content(workflow_id: int) -> List[Content]:
        """Get all content associated with a workflow"""
        return [c for c in content_db if c.workflow_id == workflow_id]

    @staticmethod
    def add_content_to_workflow(workflow_id: int, content_type: ContentType, 
                              data: Dict[str, Any], created_by: int, 
                              node_id: Optional[int] = None) -> Content:
        """Add content (task, note, or attachment) to a workflow"""
        global next_content_id
        
        content = Content(
            id=next_content_id,
            content_type=content_type,
            workflow_id=workflow_id,
            node_id=node_id,
            data=data,
            created_by=created_by
        )
        
        content_db.append(content)
        next_content_id += 1
        
        return content

    @staticmethod
    def get_node_by_id(workflow_id: int, node_id: int) -> Optional[Node]:
        """Get a specific node from a workflow"""
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            return None
        
        return next((n for n in workflow.nodes if n.id == node_id), None)

    @staticmethod
    def get_workflow_statistics(workflow_id: int) -> Dict[str, Any]:
        """Get statistics for a workflow"""
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
            "content_count": len([c for c in content_db if c.workflow_id == workflow_id])
        }
