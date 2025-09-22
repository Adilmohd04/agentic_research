"""
Shared Memory and Context Management System
Handles conversation history, agent context, and task tracking
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import sqlite3
import aiosqlite
from pathlib import Path


@dataclass
class Message:
    """Message data structure"""
    id: str
    role: str  # 'user' | 'assistant' | 'agent'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    citations: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'citations': self.citations or []
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            id=data['id'],
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {}),
            citations=data.get('citations')
        )


@dataclass
class AgentContext:
    """Agent context information"""
    agent_id: str
    role: str
    current_tasks: List[str]
    completed_tasks: List[str]
    tools: List[str]
    memory: Dict[str, Any]
    last_active: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'last_active': self.last_active.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentContext':
        return cls(
            agent_id=data['agent_id'],
            role=data['role'],
            current_tasks=data.get('current_tasks', []),
            completed_tasks=data.get('completed_tasks', []),
            tools=data.get('tools', []),
            memory=data.get('memory', {}),
            last_active=datetime.fromisoformat(data['last_active'])
        )


@dataclass
class TaskRecord:
    """Task tracking record"""
    task_id: str
    type: str
    description: str
    status: str
    assigned_agent: str
    created_at: datetime
    updated_at: datetime
    results: Optional[Dict[str, Any]] = None
    subtasks: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskRecord':
        return cls(
            task_id=data['task_id'],
            type=data['type'],
            description=data['description'],
            status=data['status'],
            assigned_agent=data['assigned_agent'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            results=data.get('results'),
            subtasks=data.get('subtasks', [])
        )


class ContextCompressor:
    """Handles context compression for long conversations"""
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def compress_messages(self, messages: List[Message]) -> List[Message]:
        """Compress message history using hierarchical summarization"""
        if not messages:
            return messages
        
        total_tokens = sum(self.estimate_tokens(msg.content) for msg in messages)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # Keep recent messages and summarize older ones
        recent_messages = messages[-10:]  # Keep last 10 messages
        older_messages = messages[:-10]
        
        if older_messages:
            # Create summary of older messages
            summary_content = self._create_summary(older_messages)
            summary_message = Message(
                id=str(uuid.uuid4()),
                role='assistant',
                content=f"[SUMMARY] Previous conversation: {summary_content}",
                timestamp=older_messages[-1].timestamp,
                metadata={'type': 'summary', 'compressed_count': len(older_messages)}
            )
            return [summary_message] + recent_messages
        
        return recent_messages
    
    def _create_summary(self, messages: List[Message]) -> str:
        """Create a summary of message history"""
        # Simple extractive summary - in production, use LLM for better summarization
        key_points = []
        for msg in messages:
            if msg.role == 'user':
                key_points.append(f"User asked: {msg.content[:100]}...")
            elif msg.role == 'assistant' and msg.metadata.get('confidence', 0) > 0.8:
                key_points.append(f"System provided: {msg.content[:100]}...")
        
        return " | ".join(key_points[:5])  # Top 5 key points


class SharedMemory:
    """Main shared memory system for multi-agent coordination"""
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        self.compressor = ContextCompressor()
        self._ensure_db_path()
        
        # In-memory caches for performance
        self._conversation_cache: Dict[str, List[Message]] = {}
        self._agent_cache: Dict[str, AgentContext] = {}
        self._task_cache: Dict[str, TaskRecord] = {}
        
        # Database will be initialized on first use
        self._db_initialized = False
    
    def _ensure_db_path(self):
        """Ensure database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def _init_database(self):
        """Initialize SQLite database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    citations TEXT,
                    INDEX(session_id),
                    INDEX(timestamp)
                )
            """)
            
            # Agent contexts table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_contexts (
                    agent_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    current_tasks TEXT,
                    completed_tasks TEXT,
                    tools TEXT,
                    memory TEXT,
                    last_active TEXT NOT NULL
                )
            """)
            
            # Task records table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_records (
                    task_id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assigned_agent TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    results TEXT,
                    subtasks TEXT,
                    INDEX(status),
                    INDEX(assigned_agent)
                )
            """)
            
            await db.commit()
            self._db_initialized = True
    
    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self._db_initialized:
            await self._init_database()
    
    # Message Management
    async def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to conversation history"""
        await self._ensure_initialized()
        
        # Add to cache
        if session_id not in self._conversation_cache:
            self._conversation_cache[session_id] = []
        self._conversation_cache[session_id].append(message)
        
        # Persist to database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO messages (id, session_id, role, content, timestamp, metadata, citations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message.id,
                session_id,
                message.role,
                message.content,
                message.timestamp.isoformat(),
                json.dumps(message.metadata),
                json.dumps(message.citations) if message.citations else None
            ))
            await db.commit()
    
    async def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history for a session"""
        await self._ensure_initialized()
        
        # Check cache first
        if session_id in self._conversation_cache:
            messages = self._conversation_cache[session_id]
            if limit:
                messages = messages[-limit:]
            return self.compressor.compress_messages(messages)
        
        # Load from database
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT id, role, content, timestamp, metadata, citations
                FROM messages 
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            async with db.execute(query, (session_id,)) as cursor:
                rows = await cursor.fetchall()
                messages = []
                for row in rows:
                    message = Message(
                        id=row[0],
                        role=row[1],
                        content=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        metadata=json.loads(row[4]) if row[4] else {},
                        citations=json.loads(row[5]) if row[5] else None
                    )
                    messages.append(message)
                
                # Cache the results
                self._conversation_cache[session_id] = messages
                return self.compressor.compress_messages(messages)
    
    # Agent Context Management
    async def update_agent_context(self, context: AgentContext) -> None:
        """Update agent context information"""
        await self._ensure_initialized()
        
        # Update cache
        self._agent_cache[context.agent_id] = context
        
        # Persist to database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO agent_contexts 
                (agent_id, role, current_tasks, completed_tasks, tools, memory, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                context.agent_id,
                context.role,
                json.dumps(context.current_tasks),
                json.dumps(context.completed_tasks),
                json.dumps(context.tools),
                json.dumps(context.memory),
                context.last_active.isoformat()
            ))
            await db.commit()
    
    async def get_agent_context(self, agent_id: str) -> Optional[AgentContext]:
        """Get agent context by ID"""
        # Check cache first
        if agent_id in self._agent_cache:
            return self._agent_cache[agent_id]
        
        # Load from database
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT agent_id, role, current_tasks, completed_tasks, tools, memory, last_active
                FROM agent_contexts WHERE agent_id = ?
            """, (agent_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    context = AgentContext(
                        agent_id=row[0],
                        role=row[1],
                        current_tasks=json.loads(row[2]) if row[2] else [],
                        completed_tasks=json.loads(row[3]) if row[3] else [],
                        tools=json.loads(row[4]) if row[4] else [],
                        memory=json.loads(row[5]) if row[5] else {},
                        last_active=datetime.fromisoformat(row[6])
                    )
                    # Cache the result
                    self._agent_cache[agent_id] = context
                    return context
        return None
    
    async def get_active_agents(self, since: Optional[datetime] = None) -> List[AgentContext]:
        """Get list of active agents"""
        if since is None:
            since = datetime.now() - timedelta(hours=1)  # Active in last hour
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT agent_id, role, current_tasks, completed_tasks, tools, memory, last_active
                FROM agent_contexts 
                WHERE last_active > ?
                ORDER BY last_active DESC
            """, (since.isoformat(),)) as cursor:
                rows = await cursor.fetchall()
                contexts = []
                for row in rows:
                    context = AgentContext(
                        agent_id=row[0],
                        role=row[1],
                        current_tasks=json.loads(row[2]) if row[2] else [],
                        completed_tasks=json.loads(row[3]) if row[3] else [],
                        tools=json.loads(row[4]) if row[4] else [],
                        memory=json.loads(row[5]) if row[5] else {},
                        last_active=datetime.fromisoformat(row[6])
                    )
                    contexts.append(context)
                return contexts
    
    # Task Management
    async def create_task(self, task: TaskRecord) -> None:
        """Create a new task record"""
        await self._ensure_initialized()
        
        # Add to cache
        self._task_cache[task.task_id] = task
        
        # Persist to database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO task_records 
                (task_id, type, description, status, assigned_agent, created_at, updated_at, results, subtasks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id,
                task.type,
                task.description,
                task.status,
                task.assigned_agent,
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
                json.dumps(task.results) if task.results else None,
                json.dumps(task.subtasks) if task.subtasks else None
            ))
            await db.commit()
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> None:
        """Update task record"""
        # Update cache
        if task_id in self._task_cache:
            task = self._task_cache[task_id]
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now()
        
        # Update database
        set_clauses = []
        values = []
        for key, value in updates.items():
            if key in ['results', 'subtasks']:
                set_clauses.append(f"{key} = ?")
                values.append(json.dumps(value) if value else None)
            else:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(task_id)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                UPDATE task_records 
                SET {', '.join(set_clauses)}
                WHERE task_id = ?
            """, values)
            await db.commit()
    
    async def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """Get task by ID"""
        # Check cache first
        if task_id in self._task_cache:
            return self._task_cache[task_id]
        
        # Load from database
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT task_id, type, description, status, assigned_agent, 
                       created_at, updated_at, results, subtasks
                FROM task_records WHERE task_id = ?
            """, (task_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    task = TaskRecord(
                        task_id=row[0],
                        type=row[1],
                        description=row[2],
                        status=row[3],
                        assigned_agent=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        updated_at=datetime.fromisoformat(row[6]),
                        results=json.loads(row[7]) if row[7] else None,
                        subtasks=json.loads(row[8]) if row[8] else None
                    )
                    # Cache the result
                    self._task_cache[task_id] = task
                    return task
        return None
    
    async def get_tasks_by_agent(self, agent_id: str, status: Optional[str] = None) -> List[TaskRecord]:
        """Get tasks assigned to an agent"""
        query = "SELECT task_id, type, description, status, assigned_agent, created_at, updated_at, results, subtasks FROM task_records WHERE assigned_agent = ?"
        params = [agent_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                tasks = []
                for row in rows:
                    task = TaskRecord(
                        task_id=row[0],
                        type=row[1],
                        description=row[2],
                        status=row[3],
                        assigned_agent=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        updated_at=datetime.fromisoformat(row[6]),
                        results=json.loads(row[7]) if row[7] else None,
                        subtasks=json.loads(row[8]) if row[8] else None
                    )
                    tasks.append(task)
                return tasks
    
    # Utility Methods
    async def clear_old_data(self, days: int = 30) -> None:
        """Clear old data to manage storage"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Clear old messages
            await db.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff_date.isoformat(),))
            
            # Clear old completed tasks
            await db.execute("""
                DELETE FROM task_records 
                WHERE status = 'completed' AND updated_at < ?
            """, (cutoff_date.isoformat(),))
            
            await db.commit()
        
        # Clear caches
        self._conversation_cache.clear()
        self._task_cache.clear()
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Message count
            async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                stats['total_messages'] = (await cursor.fetchone())[0]
            
            # Active agents count
            since = datetime.now() - timedelta(hours=1)
            async with db.execute("SELECT COUNT(*) FROM agent_contexts WHERE last_active > ?", (since.isoformat(),)) as cursor:
                stats['active_agents'] = (await cursor.fetchone())[0]
            
            # Task counts by status
            async with db.execute("SELECT status, COUNT(*) FROM task_records GROUP BY status") as cursor:
                task_counts = await cursor.fetchall()
                stats['tasks_by_status'] = {status: count for status, count in task_counts}
            
            # Cache sizes
            stats['cache_sizes'] = {
                'conversations': len(self._conversation_cache),
                'agents': len(self._agent_cache),
                'tasks': len(self._task_cache)
            }
            
            return stats


# Global shared memory instance
shared_memory = SharedMemory()