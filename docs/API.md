# Agentic Research Copilot API Documentation

## Overview

The Agentic Research Copilot provides a comprehensive REST API for multi-agent AI research assistance, developer copilot features, and system management. The API is built with FastAPI and includes real-time WebSocket support.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API uses JWT (JSON Web Token) based authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "user-001",
    "username": "your-username",
    "role": "researcher",
    "permissions": ["read_documents", "use_agents", ...]
  }
}
```

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/login
Authenticate user and receive access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "remember_me": false
}
```

#### POST /api/auth/logout
Logout current user and invalidate token.

**Headers:** `Authorization: Bearer <token>`

#### GET /api/auth/me
Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "user_id": "user-001",
  "username": "researcher",
  "role": "researcher",
  "permissions": ["read_documents", "use_agents"],
  "token_expires": "2024-01-01T12:00:00Z"
}
```

### Agent Management Endpoints

#### POST /api/agents/coordinate
Coordinate multi-agent task execution.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "task": "Analyze the latest trends in AI research",
  "context": {
    "domain": "artificial_intelligence",
    "time_range": "last_6_months"
  },
  "agents": ["researcher", "analyzer"],
  "max_iterations": 5
}
```

**Response:**
```json
{
  "task_id": "task-12345",
  "status": "in_progress",
  "agents_assigned": ["researcher", "analyzer"],
  "estimated_completion": "2024-01-01T12:05:00Z"
}
```

#### GET /api/agents/tasks/{task_id}
Get task status and results.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "task_id": "task-12345",
  "status": "completed",
  "progress": 100,
  "results": {
    "summary": "Analysis of AI research trends...",
    "citations": [
      {
        "source": "Nature AI Journal",
        "title": "Recent Advances in Machine Learning",
        "url": "https://example.com/paper",
        "confidence": 0.95
      }
    ],
    "insights": ["Key finding 1", "Key finding 2"]
  },
  "execution_time": 45.2,
  "agents_used": ["researcher", "analyzer"]
}
```

### Memory Management Endpoints

#### POST /api/memory/conversations
Store conversation message.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "role": "user",
  "content": "What are the latest developments in quantum computing?",
  "timestamp": "2024-01-01T12:00:00Z",
  "metadata": {
    "session_id": "session-123",
    "context": "research_query"
  }
}
```

#### GET /api/memory/conversations
Retrieve conversation history.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit`: Number of messages to retrieve (default: 50)
- `offset`: Number of messages to skip (default: 0)
- `session_id`: Filter by session ID

**Response:**
```json
{
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "content": "What are the latest developments in quantum computing?",
      "timestamp": "2024-01-01T12:00:00Z",
      "metadata": {
        "session_id": "session-123"
      }
    }
  ],
  "total": 1,
  "has_more": false
}
```

### RAG (Retrieval-Augmented Generation) Endpoints

#### POST /api/rag/query
Perform RAG query with citations.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "query": "What are the benefits of transformer architectures?",
  "max_results": 10,
  "include_citations": true,
  "filters": {
    "domain": "machine_learning",
    "date_range": {
      "start": "2023-01-01",
      "end": "2024-01-01"
    }
  }
}
```

**Response:**
```json
{
  "answer": "Transformer architectures offer several key benefits...",
  "citations": [
    {
      "source": "Attention Is All You Need",
      "authors": ["Vaswani et al."],
      "url": "https://arxiv.org/abs/1706.03762",
      "confidence": 0.98,
      "excerpt": "The Transformer model architecture..."
    }
  ],
  "confidence_score": 0.92,
  "processing_time": 1.2
}
```

#### POST /api/rag/documents
Upload document for indexing.

**Headers:** `Authorization: Bearer <token>`

**Request:** Multipart form data with file upload

**Response:**
```json
{
  "document_id": "doc-12345",
  "filename": "research_paper.pdf",
  "status": "processing",
  "estimated_completion": "2024-01-01T12:02:00Z"
}
```

### Performance Monitoring Endpoints

#### GET /api/performance/metrics
Get current performance metrics.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "status": "success",
  "data": {
    "cache_stats": {
      "default": {
        "hits": 1250,
        "misses": 150,
        "hit_rate": 0.89,
        "size": 500,
        "max_size": 1000
      }
    },
    "system_resources": {
      "cpu_percent": 45.2,
      "memory_percent": 67.8,
      "disk_usage_percent": 23.1
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### GET /api/performance/cache/stats
Get detailed cache statistics.

**Headers:** `Authorization: Bearer <token>`

#### POST /api/performance/cache/{cache_name}/clear
Clear specific cache.

**Headers:** `Authorization: Bearer <token>`

### Error Handling Endpoints

#### GET /api/errors/statistics
Get error statistics and metrics.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_errors": 45,
    "errors_by_category": {
      "system": 12,
      "network": 8,
      "validation": 25
    },
    "errors_by_severity": {
      "low": 30,
      "medium": 12,
      "high": 3
    }
  }
}
```

#### GET /api/errors/circuit-breakers
Get circuit breaker status.

**Headers:** `Authorization: Bearer <token>`

### Developer Copilot Endpoints

#### POST /api/copilot/analyze-repository
Analyze code repository.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "analysis_type": "full",
  "include_tests": true
}
```

**Response:**
```json
{
  "analysis_id": "analysis-12345",
  "status": "completed",
  "results": {
    "file_count": 156,
    "lines_of_code": 12450,
    "test_coverage": 78.5,
    "code_quality_score": 8.2,
    "suggestions": [
      {
        "type": "improvement",
        "file": "src/main.py",
        "line": 45,
        "message": "Consider using type hints for better code clarity"
      }
    ]
  }
}
```

#### POST /api/copilot/generate-diff
Generate code diff with improvements.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "file_path": "src/utils.py",
  "improvement_type": "performance",
  "context": "Optimize database queries"
}
```

**Response:**
```json
{
  "diff_id": "diff-12345",
  "original_file": "src/utils.py",
  "diff": "--- a/src/utils.py\n+++ b/src/utils.py\n@@ -10,7 +10,8 @@\n...",
  "explanation": "Optimized database queries by adding connection pooling...",
  "confidence": 0.87
}
```

### Voice Interface Endpoints

#### POST /api/voice/speech-to-text
Convert speech to text.

**Headers:** `Authorization: Bearer <token>`

**Request:** Multipart form data with audio file

**Response:**
```json
{
  "transcript": "What are the latest developments in quantum computing?",
  "confidence": 0.94,
  "language": "en-US",
  "duration": 3.2
}
```

#### POST /api/voice/text-to-speech
Convert text to speech.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "text": "Here are the latest developments in quantum computing...",
  "voice": "neural",
  "speed": 1.0,
  "format": "mp3"
}
```

**Response:** Audio file download

### WebSocket Endpoints

#### WS /ws/agents
Real-time agent coordination updates.

**Connection:** WebSocket with JWT token in query parameter or header

**Message Types:**
```json
{
  "type": "task_update",
  "task_id": "task-12345",
  "status": "in_progress",
  "progress": 45,
  "current_agent": "researcher",
  "message": "Analyzing research papers..."
}
```

#### WS /ws/chat
Real-time chat interface.

**Message Format:**
```json
{
  "type": "message",
  "content": "What are the benefits of AI?",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "id": "error-12345",
    "message": "Validation failed",
    "category": "validation",
    "severity": "low",
    "timestamp": "2024-01-01T12:00:00Z",
    "details": {
      "field": "username",
      "reason": "Username is required"
    }
  }
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable

## Rate Limiting

API endpoints are rate limited:

- **General API**: 100 requests per minute per IP
- **Authentication**: 10 requests per minute per IP
- **File uploads**: 5 requests per minute per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `limit`: Number of items per page (max 100)
- `offset`: Number of items to skip
- `cursor`: Cursor-based pagination token

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 1250,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTIzfQ=="
  }
}
```

## SDKs and Libraries

### Python SDK

```python
from agentic_research_client import AgenticResearchClient

client = AgenticResearchClient(
    base_url="https://api.example.com",
    api_key="your-api-key"
)

# Coordinate agents
task = client.agents.coordinate(
    task="Analyze AI trends",
    agents=["researcher", "analyzer"]
)

# Query RAG system
result = client.rag.query(
    query="What are transformer benefits?",
    include_citations=True
)
```

### JavaScript SDK

```javascript
import { AgenticResearchClient } from '@agentic-research/client';

const client = new AgenticResearchClient({
  baseUrl: 'https://api.example.com',
  apiKey: 'your-api-key'
});

// Coordinate agents
const task = await client.agents.coordinate({
  task: 'Analyze AI trends',
  agents: ['researcher', 'analyzer']
});

// Query RAG system
const result = await client.rag.query({
  query: 'What are transformer benefits?',
  includeCitations: true
});
```

## Examples

### Complete Research Workflow

```python
import asyncio
from agentic_research_client import AgenticResearchClient

async def research_workflow():
    client = AgenticResearchClient("https://api.example.com", "your-token")
    
    # 1. Start research task
    task = await client.agents.coordinate(
        task="Research quantum computing applications in cryptography",
        agents=["researcher", "analyzer"],
        context={"domain": "quantum_cryptography"}
    )
    
    # 2. Monitor progress
    while task.status != "completed":
        await asyncio.sleep(5)
        task = await client.agents.get_task(task.task_id)
        print(f"Progress: {task.progress}%")
    
    # 3. Get results
    results = task.results
    print(f"Summary: {results.summary}")
    
    # 4. Generate report
    report = await client.reports.generate(
        task_id=task.task_id,
        format="markdown"
    )
    
    return report

# Run the workflow
report = asyncio.run(research_workflow())
```

### Real-time Chat Integration

```javascript
const ws = new WebSocket('wss://api.example.com/ws/chat?token=your-jwt-token');

ws.onopen = () => {
  console.log('Connected to chat');
  
  // Send message
  ws.send(JSON.stringify({
    type: 'message',
    content: 'What are the latest AI developments?'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'response') {
    console.log('AI Response:', data.content);
    
    // Display citations
    data.citations?.forEach(citation => {
      console.log(`Source: ${citation.source} (${citation.confidence})`);
    });
  }
};
```

## Support

For API support and questions:

- **Documentation**: https://docs.agentic-research.com
- **GitHub Issues**: https://github.com/agentic-research/copilot/issues
- **Email**: support@agentic-research.com
- **Discord**: https://discord.gg/agentic-research

## Changelog

### v1.0.0 (2024-01-01)
- Initial API release
- Multi-agent coordination
- RAG system with citations
- Authentication and authorization
- Performance monitoring
- Developer copilot features
- Voice interface support
- Real-time WebSocket communication