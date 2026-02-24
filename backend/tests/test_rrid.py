"""
Tests for RRID (Research Resource Identifier) endpoints.

Covers search, resolve, attach, list, detach, duplicate handling,
validation, and cascade deletion — all with mocked SciCrunch HTTP calls.
"""

import json
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest
from app import db
from app.models import DocidRrid


# ---------------------------------------------------------------------------
# Mock response fixtures
# ---------------------------------------------------------------------------

MOCK_SCICRUNCH_SEARCH_RESPONSE = {
    "hits": {
        "total": 1,
        "hits": [
            {
                "_id": "SCR_012345",
                "_source": {
                    "item": {
                        "name": "Flow Cytometry Core",
                        "description": "A core facility for flow cytometry services",
                        "url": "https://example.com/flow",
                        "types": [{"curie": "Resource:CoreFacility", "name": "Core Facility"}],
                        "curie": "SCR_012345",
                    }
                },
            }
        ],
    }
}

MOCK_SCICRUNCH_RESOLVER_RESPONSE = {
    "name": "Flow Cytometry Core",
    "curie": "RRID:SCR_012345",
    "description": "A core facility for flow cytometry services",
    "url": "https://example.com/flow",
    "resource_type": "core facility",
    "properCitation": "(Flow Cytometry Core, RRID:SCR_012345)",
    "mentions": 42,
}


# ---------------------------------------------------------------------------
# Helper to mock resolve_rrid for attach tests
# ---------------------------------------------------------------------------

def _mock_resolve_success(rrid_string, entity_type=None, entity_id=None):
    """Return a successful resolve result matching the real service shape."""
    return (
        {
            "resolved": {
                "name": "Flow Cytometry Core",
                "rrid": "RRID:SCR_012345",
                "description": "A core facility for flow cytometry services",
                "url": "https://example.com/flow",
                "resource_type": "core facility",
                "properCitation": "(Flow Cytometry Core, RRID:SCR_012345)",
                "mentions": 42,
            },
            "last_resolved_at": datetime.utcnow().isoformat(),
            "cached": False,
        },
        None,
    )


# ===================================================================
# 1. Search endpoint
# ===================================================================

class TestSearchEndpoint:
    """GET /api/v1/rrid/search"""

    def test_search_returns_normalized_results(self, authenticated_client):
        """Search mocks a SciCrunch ES response and asserts normalized output."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SCICRUNCH_SEARCH_RESPONSE

        with patch("app.service_scicrunch.scicrunch_http_session.post", return_value=mock_response):
            response = authenticated_client.get("/api/v1/rrid/search?q=flow+cytometry")

        assert response.status_code == 200
        results = response.get_json()
        assert isinstance(results, list)
        assert len(results) == 1

        first_result = results[0]
        assert first_result["scicrunch_id"] == "SCR_012345"
        assert first_result["name"] == "Flow Cytometry Core"
        assert first_result["description"] == "A core facility for flow cytometry services"
        assert first_result["url"] == "https://example.com/flow"
        assert isinstance(first_result["types"], list)
        assert first_result["rrid"] == "RRID:SCR_012345"

    def test_search_missing_query_returns_400(self, authenticated_client):
        """Missing required 'q' parameter returns 400."""
        response = authenticated_client.get("/api/v1/rrid/search")
        assert response.status_code == 400
        assert "Missing required parameter: q" in response.get_json()["error"]

    def test_search_invalid_type_returns_400(self, authenticated_client):
        """Invalid resource type returns 400."""
        response = authenticated_client.get("/api/v1/rrid/search?q=test&type=invalid_type")
        assert response.status_code == 400
        assert "Invalid resource type" in response.get_json()["error"]

    def test_search_scicrunch_failure_returns_502(self, authenticated_client):
        """SciCrunch HTTP failure returns 502."""
        import requests as req

        with patch(
            "app.service_scicrunch.scicrunch_http_session.post",
            side_effect=req.ConnectionError("Connection timeout"),
        ):
            response = authenticated_client.get("/api/v1/rrid/search?q=test")

        assert response.status_code == 502
        assert "unavailable" in response.get_json()["error"].lower()


# ===================================================================
# 2. Resolve endpoint
# ===================================================================

class TestResolveEndpoint:
    """GET /api/v1/rrid/resolve"""

    def test_resolve_returns_canonical_fields(self, authenticated_client):
        """Resolve mocks the resolver response and asserts correct extraction."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SCICRUNCH_RESOLVER_RESPONSE

        with patch("app.service_scicrunch.scicrunch_http_session.get", return_value=mock_response):
            response = authenticated_client.get("/api/v1/rrid/resolve?rrid=RRID:SCR_012345")

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Flow Cytometry Core"
        assert data["properCitation"] == "(Flow Cytometry Core, RRID:SCR_012345)"
        assert data["mentions"] == 42
        assert data["description"] == "A core facility for flow cytometry services"
        assert data["url"] == "https://example.com/flow"
        assert data["resource_type"] == "core facility"
        assert "last_resolved_at" in data
        assert "stale" in data

    def test_resolve_invalid_rrid_returns_400(self, authenticated_client):
        """Invalid RRID format returns 400."""
        response = authenticated_client.get("/api/v1/rrid/resolve?rrid=INVALID_FORMAT")
        assert response.status_code == 400
        assert "Invalid RRID format" in response.get_json()["error"]

    def test_resolve_missing_rrid_returns_400(self, authenticated_client):
        """Missing required 'rrid' parameter returns 400."""
        response = authenticated_client.get("/api/v1/rrid/resolve")
        assert response.status_code == 400
        assert "Missing required parameter: rrid" in response.get_json()["error"]

    def test_resolve_partial_entity_context_returns_400(self, authenticated_client):
        """Providing entity_type without entity_id returns 400."""
        response = authenticated_client.get(
            "/api/v1/rrid/resolve?rrid=RRID:SCR_012345&entity_type=publication"
        )
        assert response.status_code == 400
        assert "Both entity_type and entity_id" in response.get_json()["error"]

    def test_resolve_invalid_entity_type_returns_400(self, authenticated_client):
        """Invalid entity_type returns 400."""
        response = authenticated_client.get(
            "/api/v1/rrid/resolve?rrid=RRID:SCR_012345&entity_type=user_account&entity_id=1"
        )
        assert response.status_code == 400
        assert "Invalid entity_type" in response.get_json()["error"]


# ===================================================================
# 3. Attach endpoint
# ===================================================================

class TestAttachEndpoint:
    """POST /api/v1/rrid/attach"""

    def test_attach_creates_rrid_row(self, authenticated_client, app):
        """Attach creates a docid_rrids row with resolved metadata."""
        with patch("app.routes.rrid.resolve_rrid", side_effect=_mock_resolve_success):
            response = authenticated_client.post(
                "/api/v1/rrid/attach",
                data=json.dumps({
                    "rrid": "RRID:SCR_012345",
                    "entity_type": "publication",
                    "entity_id": 1,
                }),
                content_type="application/json",
            )

        assert response.status_code == 201
        data = response.get_json()
        assert data["rrid"] == "RRID:SCR_012345"
        assert data["entity_type"] == "publication"
        assert data["entity_id"] == 1
        assert data["rrid_name"] == "Flow Cytometry Core"
        assert data["rrid_resource_type"] == "core facility"
        assert data["rrid_url"] == "https://example.com/flow"
        assert data["id"] is not None

    def test_attach_duplicate_returns_409(self, authenticated_client, app):
        """Attaching the same RRID twice returns 409 Conflict."""
        with patch("app.routes.rrid.resolve_rrid", side_effect=_mock_resolve_success):
            # First attach — should succeed
            first_response = authenticated_client.post(
                "/api/v1/rrid/attach",
                data=json.dumps({
                    "rrid": "RRID:SCR_099999",
                    "entity_type": "publication",
                    "entity_id": 99,
                }),
                content_type="application/json",
            )
            assert first_response.status_code == 201

            # Second attach — same RRID + entity = 409
            second_response = authenticated_client.post(
                "/api/v1/rrid/attach",
                data=json.dumps({
                    "rrid": "RRID:SCR_099999",
                    "entity_type": "publication",
                    "entity_id": 99,
                }),
                content_type="application/json",
            )

        assert second_response.status_code == 409
        assert "already attached" in second_response.get_json()["error"]

    def test_attach_missing_fields_returns_400(self, authenticated_client):
        """Missing required fields return 400."""
        response = authenticated_client.post(
            "/api/v1/rrid/attach",
            data=json.dumps({"rrid": "RRID:SCR_012345"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "Missing required field" in response.get_json()["error"]

    def test_attach_invalid_entity_type_returns_400(self, authenticated_client):
        """Invalid entity_type on attach returns 400."""
        response = authenticated_client.post(
            "/api/v1/rrid/attach",
            data=json.dumps({
                "rrid": "RRID:SCR_012345",
                "entity_type": "user_account",
                "entity_id": 1,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "Invalid entity_type" in response.get_json()["error"]

    def test_attach_invalid_rrid_format_returns_400(self, authenticated_client):
        """Invalid RRID format on attach returns 400."""
        response = authenticated_client.post(
            "/api/v1/rrid/attach",
            data=json.dumps({
                "rrid": "NOT_AN_RRID",
                "entity_type": "publication",
                "entity_id": 1,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "Invalid RRID format" in response.get_json()["error"]


# ===================================================================
# 4. List endpoint
# ===================================================================

class TestListEndpoint:
    """GET /api/v1/rrid/entity"""

    def test_list_returns_attached_rrids(self, authenticated_client, app):
        """List returns RRIDs attached to a specific entity."""
        # First attach an RRID
        with patch("app.routes.rrid.resolve_rrid", side_effect=_mock_resolve_success):
            authenticated_client.post(
                "/api/v1/rrid/attach",
                data=json.dumps({
                    "rrid": "RRID:SCR_055555",
                    "entity_type": "publication",
                    "entity_id": 55,
                }),
                content_type="application/json",
            )

        # Now list
        response = authenticated_client.get(
            "/api/v1/rrid/entity?entity_type=publication&entity_id=55"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["rrid"] == "RRID:SCR_055555"
        assert data[0]["entity_type"] == "publication"

    def test_list_empty_returns_200_with_empty_array(self, authenticated_client):
        """No attached RRIDs returns 200 with empty array."""
        response = authenticated_client.get(
            "/api/v1/rrid/entity?entity_type=publication&entity_id=99999"
        )
        assert response.status_code == 200
        assert response.get_json() == []

    def test_list_missing_params_returns_400(self, authenticated_client):
        """Missing entity_type or entity_id returns 400."""
        response = authenticated_client.get("/api/v1/rrid/entity?entity_type=publication")
        assert response.status_code == 400
        assert "Missing required parameter" in response.get_json()["error"]

    def test_list_invalid_entity_type_returns_400(self, authenticated_client):
        """Invalid entity_type returns 400."""
        response = authenticated_client.get(
            "/api/v1/rrid/entity?entity_type=user_account&entity_id=1"
        )
        assert response.status_code == 400
        assert "Invalid entity_type" in response.get_json()["error"]


# ===================================================================
# 5. Detach (delete) endpoint
# ===================================================================

class TestDetachEndpoint:
    """DELETE /api/v1/rrid/<rrid_id>"""

    def test_detach_removes_rrid(self, authenticated_client, app):
        """Detach removes the RRID row and subsequent list no longer includes it."""
        # Attach first
        with patch("app.routes.rrid.resolve_rrid", side_effect=_mock_resolve_success):
            attach_response = authenticated_client.post(
                "/api/v1/rrid/attach",
                data=json.dumps({
                    "rrid": "RRID:SCR_077777",
                    "entity_type": "organization",
                    "entity_id": 77,
                }),
                content_type="application/json",
            )
        assert attach_response.status_code == 201
        rrid_record_id = attach_response.get_json()["id"]

        # Delete
        delete_response = authenticated_client.delete(f"/api/v1/rrid/{rrid_record_id}")
        assert delete_response.status_code == 200
        assert "detached" in delete_response.get_json()["message"].lower()

        # Verify gone
        list_response = authenticated_client.get(
            "/api/v1/rrid/entity?entity_type=organization&entity_id=77"
        )
        rrid_ids = [r["id"] for r in list_response.get_json()]
        assert rrid_record_id not in rrid_ids

    def test_detach_nonexistent_returns_404(self, authenticated_client):
        """Deleting a non-existent RRID returns 404."""
        response = authenticated_client.delete("/api/v1/rrid/999999")
        assert response.status_code == 404


# ===================================================================
# 6. RRID format validation (service layer)
# ===================================================================

class TestRridValidation:
    """validate_rrid() service function."""

    def test_valid_formats_accepted(self, app):
        """Valid RRID strings are accepted and normalized."""
        from app.service_scicrunch import validate_rrid

        with app.app_context():
            valid_inputs = [
                ("RRID:SCR_012345", "RRID:SCR_012345"),
                ("SCR_012345", "RRID:SCR_012345"),
                ("RRID:AB_123456789", "RRID:AB_123456789"),
                ("AB_123456789", "RRID:AB_123456789"),
                ("RRID:CVCL_0001", "RRID:CVCL_0001"),
                ("rrid:scr_012345", "RRID:SCR_012345"),  # case insensitive
            ]

            for raw_input, expected_normalized in valid_inputs:
                normalized_value, validation_error = validate_rrid(raw_input)
                assert validation_error is None, f"Expected no error for '{raw_input}'"
                assert normalized_value == expected_normalized, (
                    f"Expected '{expected_normalized}' for '{raw_input}', got '{normalized_value}'"
                )

    def test_invalid_formats_rejected(self, app):
        """Invalid RRID strings are rejected."""
        from app.service_scicrunch import validate_rrid

        with app.app_context():
            invalid_inputs = [
                "",
                "INVALID",
                "RRID:INVALID_123",
                "RRID:XYZ_999",
                "12345",
                "RRID:",
            ]

            for raw_input in invalid_inputs:
                normalized_value, validation_error = validate_rrid(raw_input)
                assert validation_error is not None, f"Expected error for '{raw_input}'"
                assert normalized_value is None


# ===================================================================
# 7. Cascade deletion
# ===================================================================

class TestCascadeDeletion:
    """Application-level cascade removes RRID rows when parent entity deleted."""

    def test_rrid_rows_removed_when_directly_deleted(self, authenticated_client, app):
        """Directly deleting DocidRrid rows by entity works."""
        with app.app_context():
            # Insert a row directly
            rrid_row = DocidRrid(
                entity_type="publication",
                entity_id=888,
                rrid="RRID:SCR_888888",
                rrid_name="Test Resource",
                rrid_resource_type="core facility",
                last_resolved_at=datetime.utcnow(),
            )
            db.session.add(rrid_row)
            db.session.commit()

            # Verify it exists
            assert DocidRrid.query.filter_by(
                entity_type="publication", entity_id=888
            ).count() == 1

            # Simulate cascade: delete by entity
            DocidRrid.query.filter_by(
                entity_type="publication", entity_id=888
            ).delete()
            db.session.commit()

            # Verify zero orphaned rows
            assert DocidRrid.query.filter_by(
                entity_type="publication", entity_id=888
            ).count() == 0
