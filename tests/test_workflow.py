import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.workflow_service import WorkflowService, workflows_db, content_db
from app.services.auth_service import AuthService, users_db
from app.models.workflow import WorkflowCreate, NodeCreate
from app.utils.enums import NodeStatus, ContentType

client = TestClient(app)


class TestWorkflow:
    def setup_method(self):
        """Reset test data before each test"""
        workflows_db.clear()
        content_db.clear()

    def test_create_workflow(self):
        """Test creating a new workflow"""
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            description="A test workflow",
            owner_id=1
        )
        
        workflow = WorkflowService.create_workflow(workflow_data)
        
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.owner_id == 1
        assert workflow.is_active is True
        assert len(workflow.nodes) == 0

    def test_get_workflow_by_id(self):
        """Test retrieving a workflow by ID"""
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            description="A test workflow",
            owner_id=1
        )
        created_workflow = WorkflowService.create_workflow(workflow_data)
        
        retrieved_workflow = WorkflowService.get_workflow_by_id(created_workflow.id)
        
        assert retrieved_workflow is not None
        assert retrieved_workflow.id == created_workflow.id
        assert retrieved_workflow.name == "Test Workflow"

    def test_get_nonexistent_workflow(self):
        """Test retrieving a non-existent workflow"""
        workflow = WorkflowService.get_workflow_by_id(999)
        assert workflow is None

    def test_add_node_to_workflow(self):
        """Test adding a node to a workflow"""
        # Create workflow
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            owner_id=1
        )
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Add node
        node_data = NodeCreate(
            name="Test Node",
            description="A test node",
            assigned_user_id=1
        )
        node = WorkflowService.add_node_to_workflow(workflow.id, node_data)
        
        assert node is not None
        assert node.name == "Test Node"
        assert node.status == NodeStatus.PENDING
        assert node.assigned_user_id == 1
        
        # Verify node was added to workflow
        updated_workflow = WorkflowService.get_workflow_by_id(workflow.id)
        assert len(updated_workflow.nodes) == 1
        assert updated_workflow.nodes[0].id == node.id

    def test_add_node_with_dependencies(self):
        """Test adding a node with dependencies"""
        # Create workflow
        workflow_data = WorkflowCreate(name="Test Workflow", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Add first node
        node1_data = NodeCreate(name="Node 1")
        node1 = WorkflowService.add_node_to_workflow(workflow.id, node1_data)
        
        # Add second node with dependency on first
        node2_data = NodeCreate(
            name="Node 2",
            dependencies=[node1.id]
        )
        node2 = WorkflowService.add_node_to_workflow(workflow.id, node2_data)
        
        assert node2 is not None
        assert node1.id in node2.dependencies

    def test_add_node_invalid_dependency(self):
        """Test adding a node with invalid dependency"""
        workflow_data = WorkflowCreate(name="Test Workflow", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        node_data = NodeCreate(
            name="Node with Invalid Dependency",
            dependencies=[999]  # Non-existent node ID
        )
        
        with pytest.raises(ValueError, match="Dependency node 999 does not exist"):
            WorkflowService.add_node_to_workflow(workflow.id, node_data)

    def test_update_node_status(self):
        """Test updating node status"""
        # Create workflow with node
        workflow_data = WorkflowCreate(name="Test Workflow", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        node_data = NodeCreate(name="Test Node")
        node = WorkflowService.add_node_to_workflow(workflow.id, node_data)
        
        # Update status
        success = WorkflowService.update_node_status(workflow.id, node.id, NodeStatus.IN_PROGRESS)
        assert success is True
        
        # Verify status was updated
        updated_workflow = WorkflowService.get_workflow_by_id(workflow.id)
        updated_node = next(n for n in updated_workflow.nodes if n.id == node.id)
        assert updated_node.status == NodeStatus.IN_PROGRESS

    def test_update_node_status_dependency_check(self):
        """Test that node status update respects dependencies"""
        workflow_data = WorkflowCreate(name="Test Workflow", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Add nodes with dependency
        node1_data = NodeCreate(name="Node 1")
        node1 = WorkflowService.add_node_to_workflow(workflow.id, node1_data)
        
        node2_data = NodeCreate(name="Node 2", dependencies=[node1.id])
        node2 = WorkflowService.add_node_to_workflow(workflow.id, node2_data)
        
        # Try to complete node2 while node1 is still pending
        with pytest.raises(ValueError, match="dependency .* is not completed"):
            WorkflowService.update_node_status(workflow.id, node2.id, NodeStatus.COMPLETED)
        
        # Complete node1 first
        WorkflowService.update_node_status(workflow.id, node1.id, NodeStatus.COMPLETED)
        
        # Now node2 should be updatable
        success = WorkflowService.update_node_status(workflow.id, node2.id, NodeStatus.COMPLETED)
        assert success is True

    def test_execute_workflow(self):
        """Test workflow execution"""
        workflow_data = WorkflowCreate(name="Test Workflow", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Add nodes
        node1_data = NodeCreate(name="Node 1")
        node1 = WorkflowService.add_node_to_workflow(workflow.id, node1_data)
        
        node2_data = NodeCreate(name="Node 2", dependencies=[node1.id])
        node2 = WorkflowService.add_node_to_workflow(workflow.id, node2_data)
        
        # Execute workflow
        result = WorkflowService.execute_workflow(workflow.id, 1)
        
        assert result["success"] is True
        assert node1.id in result["nodes_processed"]
        # Node 2 should not be processed yet due to dependency
        assert node2.id not in result["nodes_processed"]

    def test_get_workflow_statistics(self):
        """Test getting workflow statistics"""
        workflow_data = WorkflowCreate(name="Test Workflow", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Add nodes with different statuses
        node1_data = NodeCreate(name="Node 1")
        node1 = WorkflowService.add_node_to_workflow(workflow.id, node1_data)
        WorkflowService.update_node_status(workflow.id, node1.id, NodeStatus.COMPLETED)
        
        node2_data = NodeCreate(name="Node 2")
        node2 = WorkflowService.add_node_to_workflow(workflow.id, node2_data)
        WorkflowService.update_node_status(workflow.id, node2.id, NodeStatus.IN_PROGRESS)
        
        node3_data = NodeCreate(name="Node 3")
        WorkflowService.add_node_to_workflow(workflow.id, node3_data)
        
        stats = WorkflowService.get_workflow_statistics(workflow.id)
        
        assert stats["total_nodes"] == 3
        assert stats["completed_nodes"] == 1
        assert stats["in_progress_nodes"] == 1
        assert stats["pending_nodes"] == 1
        assert stats["rejected_nodes"] == 0
        assert stats["progress_percentage"] == 33.33
        assert stats["is_complete"] is False

    def test_workflow_api_endpoints(self):
        """Test workflow API endpoints"""
        # Test getting workflows (should return empty list initially)
        response = client.get("/api/workflows?user_id=1")
        assert response.status_code == 200
        assert response.json() == []
        
        # Test creating workflow
        response = client.post("/api/workflows?user_id=1", json={
            "name": "API Test Workflow",
            "description": "Created via API",
            "owner_id": 1
        })
        assert response.status_code == 200
        workflow_data = response.json()
        workflow_id = workflow_data["id"]
        
        # Test getting specific workflow
        response = client.get(f"/api/workflows/{workflow_id}?user_id=1")
        assert response.status_code == 200
        assert response.json()["name"] == "API Test Workflow"
        
        # Test getting workflow content
        response = client.get(f"/api/workflows/{workflow_id}/content?user_id=1")
        assert response.status_code == 200
        assert response.json() == []
        
        # Test getting workflow statistics
        response = client.get(f"/api/workflows/{workflow_id}/statistics?user_id=1")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_nodes"] == 0
        assert stats["progress_percentage"] == 0
