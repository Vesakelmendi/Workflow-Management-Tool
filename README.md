# Workflow Assessment API

This is a workflow management system built with FastAPI. It handles user authentication, role-based permissions, and workflow execution with different types of nodes.

## What you need to install

You need Python 3.8+ and that's pretty much it. Here's how to get everything running:

## Setup

1. **Get the code**
   ```bash
   # Download or clone this project
   cd workflow-assessment
   ```

2. **Install the packages**
   ```bash
   # Option 1 - Using pipenv (recommended):
   pip install pipenv
   pipenv install
   pipenv shell
   
   # Option 2 - Using regular pip:
   pip install fastapi uvicorn pydantic email-validator
   ```
   
   **Yes, you need to install dependencies!** The code won't run without these packages.

3. **Run it**
   ```bash
   python main.py
   ```

That's it! The server starts at http://localhost:8000

You can check out the auto-generated docs at:
- http://localhost:8000/docs (Swagger)
- http://localhost:8000/redoc

## How to test all the endpoints (Postman style)

There's a default admin user already created:
- Username: `admin`
- Password: `admin123`

Here are all 14 endpoints tested, with the exact requests:

### 1. Login (POST /api/authenticate)
```
POST http://localhost:8000/api/authenticate
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

### 2. Register new user (POST /api/register)
```
POST http://localhost:8000/api/register
Content-Type: application/json

{
  "username": "alice",
  "email": "alice@example.com",
  "password": "password123"
}
```

### 3. Create workflow (POST /api/workflows)
```
POST http://localhost:8000/api/workflows?user_id=1
Content-Type: application/json

{
  "name": "My Test Workflow",
  "description": "Testing the workflow system",
  "owner_id": 1
}
```

### 4. Get all workflows (GET /api/workflows)
```
GET http://localhost:8000/api/workflows?user_id=1
```

### 5. Get specific workflow (GET /api/workflows/{id})
```
GET http://localhost:8000/api/workflows/1?user_id=1
```

### 6. Get workflow statistics (GET /api/workflows/{id}/statistics)
```
GET http://localhost:8000/api/workflows/1/statistics?user_id=1
```

### 7. Get workflow content (GET /api/workflows/{id}/content)
```
GET http://localhost:8000/api/workflows/1/content?user_id=1
```

### 8. Add content to workflow (POST /api/workflows/{id}/content)
```
POST http://localhost:8000/api/workflows/1/content?user_id=1&content_type=task
Content-Type: application/json

{
  "title": "Review documents",
  "assigneeId": "user123",
  "reporterId": "admin",
  "order": 1,
  "time": 1694673114,
  "priority": "HIGH"
}
```

### 9. Add node to workflow (POST /api/workflows/{id}/nodes)
```
POST http://localhost:8000/api/workflows/1/nodes?user_id=1
Content-Type: application/json

{
  "name": "Start Node",
  "type": "INIT",
  "description": "This is where everything begins",
  "dependencies": []
}
```

### 10. Execute workflow with John (success case)
```
POST http://localhost:8000/api/workflows/1/execute
Content-Type: application/json

{
  "user_id": 1,
  "trigger": {
    "userId": "John",
    "type": "user-message",
    "message": "Hello",
    "metadata": {}
  }
}
```

### 11. Execute workflow with Alice (failure case)
```
POST http://localhost:8000/api/workflows/1/execute
Content-Type: application/json

{
  "user_id": 1,
  "trigger": {
    "userId": "Alice",
    "type": "user-message",
    "message": "Hello",
    "metadata": {}
  }
}
```

### 12. Add CONDITION node
```
POST http://localhost:8000/api/workflows/1/nodes?user_id=1
Content-Type: application/json

{
  "name": "Check John",
  "type": "CONDITION",
  "description": "Check if user is John",
  "dependencies": [1]
}
```

### 13. Add MODIFY_MESSAGE node
```
POST http://localhost:8000/api/workflows/1/nodes?user_id=1
Content-Type: application/json

{
  "name": "Add Hello",
  "type": "MODIFY_MESSAGE",
  "description": "Append Hello to message",
  "dependencies": [2]
}
```

### 14. Update node status
```
PUT http://localhost:8000/api/workflows/1/nodes/1/status?user_id=1
Content-Type: application/json

{
  "status": "In Progress"
}
```

## Important notes

**Data doesn't persist!** Everything is stored in memory, so when you restart the server, all your workflows and users disappear (except the default admin).

The condition node only passes if the trigger userId is exactly "John" - any other name will fail the workflow.

## User roles explained

When you create a new user, they get the "Basic" role by default. Here's what each role can do:

- **Admin**: Can do everything on all workflows
- **Analyst**: Can read and write to workflows they have access to
- **Category Manager**: Same as Analyst basically
- **Basic**: Can only read workflows (no editing)

The admin user can always access everything. If you own a workflow, you can always access it regardless of your role.

## The 4 node types

- **INIT**: Every workflow needs exactly one of these. It just passes the message through.
- **CONDITION**: Only passes if the trigger userId is "John". Otherwise it fails the whole workflow.
- **MODIFY_MESSAGE**: Takes the message and adds " Hello" to the end.
- **STORE_MESSAGE**: Saves the message data (you'll see it in the execution results).

## What happens when you execute a workflow

The system starts with the INIT node, then follows the dependency chain. Each node processes the message and passes it to the next one. If any node fails (like the CONDITION node when userId isn't "John"), the workflow stops.

## Common issues

**"Workflow not found"** - You probably restarted the server. Remember, everything gets wiped when you restart.

**"Permission denied"** - Make sure you're using `user_id=1` (the admin) in your requests, or create a workflow with a user that has the right permissions.

**"Field required"** errors - Check that you're putting things like `content_type=task` in the URL parameters, not the JSON body.

**Port already in use** - Someone else might be running something on port 8000. Change the port in main.py or kill the other process.

## File structure

```
workflow-assessment/
├── app/
│   ├── models/      # The data structures (User, Workflow, etc.)
│   ├── routes/      # The API endpoints  
│   ├── services/    # The business logic
│   └── utils/       # Enums
├── main.py         # Starts the server
├── Pipfile         # Dependencies
└── README.md       # This guide
```

