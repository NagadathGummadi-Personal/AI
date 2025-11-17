"""
Database Executor Interface for Tools Specification System.

This module defines the interface for database tool executors that handle
database operations across different database providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ....spec.tool_context import ToolContext
from ....spec.tool_result import ToolResult


class IDbExecutor(ABC):
    """
    Interface for database tool executors.
    
    Database executors handle operations for specific database providers
    (DynamoDB, PostgreSQL, MySQL, SQLite, etc.). Each implementation handles
    database-specific connection, query execution, and result formatting.
    
    Methods:
        execute: Execute a database operation
    
    Implementing Classes:
        DynamoDBExecutor: AWS DynamoDB operations
        PostgreSQLExecutor: PostgreSQL operations
        MySQLExecutor: MySQL operations
        SQLiteExecutor: SQLite operations
    
    Example Implementation:
        class MongoDBExecutor(IDbExecutor):
            async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
                # MongoDB-specific implementation
                result = await self._execute_mongo_operation(args, ctx)
                return ToolResult(content=result, tool_name=self.spec.tool_name)
    """
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """
        Execute a database operation.
        
        Args:
            args: Operation arguments containing:
                - operation: Type of operation (e.g., 'query', 'insert', 'update')
                - Additional database-specific parameters
            ctx: Tool execution context containing:
                - user_id: User identifier
                - session_id: Session identifier
                - trace_id: Trace identifier
                - memory: Memory interface
                - metrics: Metrics interface
                
        Returns:
            ToolResult containing:
                - content: Operation result data
                - tool_name: Name of the tool
                - error: Error information if operation failed
                - usage: Resource usage information
                
        Raises:
            ValidationError: If arguments are invalid
            PermissionError: If authorization fails
            TimeoutError: If operation times out
            Exception: Database-specific errors
        
        Example:
            result = await executor.execute({
                'operation': 'query',
                'table': 'users',
                'conditions': {'id': '123'}
            }, ctx)
            
            if result.error:
                print(f"Error: {result.error}")
            else:
                print(f"Data: {result.content}")
        """
        pass

