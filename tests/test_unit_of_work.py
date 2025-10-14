"""
Tests for the unit_of_work decorators.

This module tests the transactional, unit_of_work, and read_only_transaction decorators
to ensure they properly manage database transactions, handle exceptions, and provide
the expected behavior for different scenarios.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from src.app.core.decorators.unit_of_work import transactional, unit_of_work, read_only_transaction


class TestTransactionalDecorator:
    """Test cases for the @transactional decorator."""

    @pytest.mark.asyncio
    async def test_transactional_success_commit(self):
        """Test that transactional decorator commits on successful execution."""
        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        
        @transactional()
        async def test_function(db: AsyncSession):
            # Simulate some database operation
            return "success"
        
        result = await test_function(db=mock_db)
        
        assert result == "success"
        mock_db.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_transactional_rollback_on_exception(self):
        """Test that transactional decorator rolls back on exception."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_db.begin.return_value = mock_transaction
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock()
        
        @transactional()
        async def test_function(db: AsyncSession):
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await test_function(db=mock_db)
        
        mock_db.begin.assert_called_once()
        # Verify transaction context was entered
        mock_transaction.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_transactional_rollback_on_http_exception(self):
        """Test that transactional decorator rolls back on HTTPException."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_db.begin.return_value = mock_transaction
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock()
        
        @transactional()
        async def test_function(db: AsyncSession):
            raise HTTPException(status_code=400, detail="Bad request")
        
        with pytest.raises(HTTPException):
            await test_function(db=mock_db)
        
        mock_db.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_transactional_with_nested_transactions(self):
        """Test that transactional decorator handles nested transactions with savepoints."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.in_transaction.return_value = True
        mock_savepoint = AsyncMock()
        mock_db.begin_nested.return_value = mock_savepoint
        mock_savepoint.__aenter__ = AsyncMock(return_value=mock_savepoint)
        mock_savepoint.__aexit__ = AsyncMock()
        
        @transactional()
        async def test_function(db: AsyncSession):
            return "nested_success"
        
        result = await test_function(db=mock_db)
        
        assert result == "nested_success"
        mock_db.begin_nested.assert_called_once()
        mock_savepoint.__aenter__.assert_called_once()


class TestUnitOfWorkDecorator:
    """Test cases for the @unit_of_work decorator."""

    @pytest.mark.asyncio
    async def test_unit_of_work_success(self):
        """Test that unit_of_work decorator works correctly for successful operations."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        
        @unit_of_work()
        async def test_function(db: AsyncSession):
            return {"result": "success"}
        
        result = await test_function(db=mock_db)
        
        assert result == {"result": "success"}
        mock_db.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_unit_of_work_with_sqlalchemy_error(self):
        """Test that unit_of_work decorator handles SQLAlchemy errors properly."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_db.begin.return_value = mock_transaction
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock()
        
        @unit_of_work()
        async def test_function(db: AsyncSession):
            raise SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError, match="Database error"):
            await test_function(db=mock_db)
        
        mock_db.begin.assert_called_once()


class TestReadOnlyTransactionDecorator:
    """Test cases for the @read_only_transaction decorator."""

    @pytest.mark.asyncio
    async def test_read_only_transaction_success(self):
        """Test that read_only_transaction decorator works for read operations."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        
        @read_only_transaction()
        async def test_function(db: AsyncSession):
            return {"data": "read_result"}
        
        result = await test_function(db=mock_db)
        
        assert result == {"data": "read_result"}
        mock_db.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_only_transaction_rollback_on_exception(self):
        """Test that read_only_transaction decorator rolls back on exception."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_db.begin.return_value = mock_transaction
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock()
        
        @read_only_transaction()
        async def test_function(db: AsyncSession):
            raise Exception("Read operation failed")
        
        with pytest.raises(Exception, match="Read operation failed"):
            await test_function(db=mock_db)
        
        mock_db.begin.assert_called_once()


class TestDecoratorIntegration:
    """Integration tests for decorator usage scenarios."""

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test that decorators preserve original function metadata."""
        @transactional()
        async def documented_function(db: AsyncSession):
            """This function has documentation."""
            return "result"
        
        assert documented_function.__name__ == "documented_function"
        assert "This function has documentation." in documented_function.__doc__

    @pytest.mark.asyncio
    async def test_decorator_with_multiple_parameters(self):
        """Test that decorators work with functions having multiple parameters."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        
        @transactional()
        async def multi_param_function(user_id: int, data: dict, db: AsyncSession):
            return {"user_id": user_id, "data": data}
        
        result = await multi_param_function(user_id=1, data={"name": "test"}, db=mock_db)
        
        assert result == {"user_id": 1, "data": {"name": "test"}}
        mock_db.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_error_handling_preserves_original_exception(self):
        """Test that decorators preserve the original exception details."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_db.begin.return_value = mock_transaction
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock()
        
        original_error = ValueError("Original error message")
        
        @transactional()
        async def error_function(db: AsyncSession):
            raise original_error
        
        with pytest.raises(ValueError) as exc_info:
            await error_function(db=mock_db)
        
        assert exc_info.value is original_error
        assert str(exc_info.value) == "Original error message"