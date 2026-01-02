"""
Unit tests for the Trust Layer validator.

These tests demonstrate how the Trust Layer catches
AI hallucinations and prevents bad data from reaching users.

Run with: pytest tests/test_validator.py -v
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trust_layer.validator import (
    TrustLayerValidator,
    VerificationStatus,
    AIPrediction,
)


class TestOddsVerification:
    """Tests for odds value verification."""

    def test_matching_odds_verified(self):
        """Exact match should verify."""
        validator = TrustLayerValidator()
        result = validator.verify_odds_claim(
            claimed_odds=Decimal("-110"),
            source_odds=Decimal("-110"),
            selection="Lakers"
        )
        assert result.status == VerificationStatus.VERIFIED
        assert result.discrepancy is None

    def test_within_tolerance_verified(self):
        """Small difference within tolerance should verify."""
        validator = TrustLayerValidator(tolerance=Decimal("0.5"))
        result = validator.verify_odds_claim(
            claimed_odds=Decimal("-110"),
            source_odds=Decimal("-110.3"),
            selection="Lakers"
        )
        assert result.status == VerificationStatus.VERIFIED

    def test_hallucinated_odds_rejected(self):
        """AI claiming wrong odds should fail."""
        validator = TrustLayerValidator()
        result = validator.verify_odds_claim(
            claimed_odds=Decimal("-150"),  # AI hallucinated
            source_odds=Decimal("-110"),   # Real odds
            selection="Lakers"
        )
        assert result.status == VerificationStatus.FAILED
        assert "exceeds tolerance" in result.discrepancy


class TestTeamNameVerification:
    """Tests for team name verification."""

    def test_exact_match_verified(self):
        """Exact team name match should verify."""
        validator = TrustLayerValidator()
        result = validator.verify_team_name(
            claimed_team="Los Angeles Lakers",
            source_team="Los Angeles Lakers"
        )
        assert result.status == VerificationStatus.VERIFIED

    def test_case_insensitive_match(self):
        """Different casing should still verify."""
        validator = TrustLayerValidator()
        result = validator.verify_team_name(
            claimed_team="LOS ANGELES LAKERS",
            source_team="Los Angeles Lakers"
        )
        assert result.status == VerificationStatus.VERIFIED

    def test_partial_match_flagged(self):
        """Abbreviation should be partial match."""
        validator = TrustLayerValidator()
        result = validator.verify_team_name(
            claimed_team="Lakers",
            source_team="Los Angeles Lakers"
        )
        assert result.status == VerificationStatus.PARTIAL

    def test_wrong_team_rejected(self):
        """Completely wrong team should fail."""
        validator = TrustLayerValidator()
        result = validator.verify_team_name(
            claimed_team="Boston Celtics",  # AI hallucinated wrong team
            source_team="Los Angeles Lakers"
        )
        assert result.status == VerificationStatus.FAILED


class TestPredictionVerification:
    """Integration tests for full prediction verification."""

    def test_valid_prediction_passes(self):
        """Valid prediction should pass all checks."""
        validator = TrustLayerValidator()
        prediction = AIPrediction(
            event_id="game_123",
            prediction_type="moneyline",
            predicted_value="Los Angeles Lakers",
            confidence=0.75,
            reasoning="Strong home record",
            generated_at=datetime.now(timezone.utc),
        )
        
        passed, results = validator.verify_prediction(
            prediction=prediction,
            source_odds=Decimal("-110"),
            source_team="Los Angeles Lakers"
        )
        
        assert passed is True
        assert all(r.status == VerificationStatus.VERIFIED for r in results)

    def test_invalid_confidence_rejected(self):
        """Confidence > 1.0 should fail."""
        validator = TrustLayerValidator()
        prediction = AIPrediction(
            event_id="game_123",
            prediction_type="moneyline",
            predicted_value="Lakers",
            confidence=1.5,  # Invalid
            reasoning="Sure thing!",
            generated_at=datetime.now(timezone.utc),
        )
        
        passed, results = validator.verify_prediction(
            prediction=prediction,
            source_odds=Decimal("-110"),
            source_team="Lakers"
        )
        
        assert passed is False


class TestVerificationLogging:
    """Tests for audit logging."""

    def test_all_verifications_logged(self):
        """Every verification should be logged."""
        validator = TrustLayerValidator()
        
        # Run several verifications
        validator.verify_odds_claim(Decimal("-110"), Decimal("-110"), "Team A")
        validator.verify_odds_claim(Decimal("-150"), Decimal("-110"), "Team B")
        validator.verify_team_name("Lakers", "Lakers")
        
        summary = validator.get_verification_summary()
        
        assert summary["total_checks"] == 3
        assert summary["verified"] == 2
        assert summary["failed"] == 1
        assert summary["pass_rate"] == pytest.approx(0.666, rel=0.01)
