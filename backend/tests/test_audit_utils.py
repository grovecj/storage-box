"""Unit tests for audit utilities."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.utils.audit import log_action
from app.models.audit import AuditLog


@pytest.mark.asyncio
class TestLogAction:
    async def test_uses_box_code_from_details_if_present(self, mock_db):
        """Should not add box_code if already in details."""
        details = {"box_code": "BOX-0042", "action_type": "create"}

        result = await log_action(
            db=mock_db,
            box_id=1,
            action="box_created",
            details=details,
            box_code="BOX-0001"  # This should be ignored
        )

        # Should not execute any queries since box_code is already present
        mock_db.execute.assert_not_called()
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

        # Verify the audit log entry has the correct details
        added_entry = mock_db.add.call_args[0][0]
        assert isinstance(added_entry, AuditLog)
        assert added_entry.box_id == 1
        assert added_entry.action == "box_created"
        assert added_entry.details["box_code"] == "BOX-0042"
        assert added_entry.details["action_type"] == "create"

    async def test_uses_provided_box_code_parameter(self, mock_db):
        """Should use box_code parameter if provided and not in details."""
        details = {"action_type": "update"}

        result = await log_action(
            db=mock_db,
            box_id=1,
            action="box_updated",
            details=details,
            box_code="BOX-0123"
        )

        # Should not execute query since box_code param is provided
        mock_db.execute.assert_not_called()
        mock_db.add.assert_called_once()

        added_entry = mock_db.add.call_args[0][0]
        assert added_entry.details["box_code"] == "BOX-0123"
        assert added_entry.details["action_type"] == "update"

    async def test_fetches_box_code_from_db_when_box_id_provided(self, mock_db):
        """Should fetch box_code from DB when box_id provided but no box_code."""
        details = {"action_type": "delete"}

        # Mock the DB query to return a box_code
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "BOX-0999"
        mock_db.execute.return_value = mock_result

        result = await log_action(
            db=mock_db,
            box_id=5,
            action="box_deleted",
            details=details,
            box_code=None
        )

        # Should execute query to fetch box_code
        mock_db.execute.assert_called_once()
        mock_db.add.assert_called_once()

        added_entry = mock_db.add.call_args[0][0]
        assert added_entry.box_id == 5
        assert added_entry.details["box_code"] == "BOX-0999"
        assert added_entry.details["action_type"] == "delete"

    async def test_handles_box_code_not_found_in_db(self, mock_db):
        """Should handle case when box_code lookup returns None."""
        details = {"action_type": "orphaned"}

        # Mock the DB query to return None (box not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await log_action(
            db=mock_db,
            box_id=999,
            action="box_orphaned",
            details=details,
            box_code=None
        )

        mock_db.execute.assert_called_once()
        mock_db.add.assert_called_once()

        # Details should not include box_code
        added_entry = mock_db.add.call_args[0][0]
        assert "box_code" not in added_entry.details
        assert added_entry.details["action_type"] == "orphaned"

    async def test_skips_lookup_when_box_id_is_none(self, mock_db):
        """Should not fetch box_code when box_id is None."""
        details = {"action_type": "system"}

        result = await log_action(
            db=mock_db,
            box_id=None,
            action="system_event",
            details=details,
            box_code=None
        )

        # Should not execute any queries
        mock_db.execute.assert_not_called()
        mock_db.add.assert_called_once()

        added_entry = mock_db.add.call_args[0][0]
        assert added_entry.box_id is None
        assert "box_code" not in added_entry.details
        assert added_entry.details["action_type"] == "system"

    async def test_preserves_original_details_dict(self, mock_db):
        """Should not mutate the original details dict."""
        original_details = {"action_type": "test"}

        result = await log_action(
            db=mock_db,
            box_id=1,
            action="test_action",
            details=original_details,
            box_code="BOX-0001"
        )

        # Original details should not be modified
        assert "box_code" not in original_details
        assert original_details == {"action_type": "test"}
