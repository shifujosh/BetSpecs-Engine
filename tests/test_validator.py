"""
Unit tests for the Trust Layer Validator.

Verifies domain-specific logic including:
- Vig calculation
- Steam/Reverse line movement detection
- Fuzzy team name matching
- Confidence validation
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trust_layer.validator import (
    TrustLayerValidator,
    VerificationStatus,
    AIPrediction,
    OddsMovementDirection
)


class TestOddsValidator:
    """Tests for odds-specific logic."""
    
    def test_vig_calculation(self):
        """Should correctly calculate house edge."""
        validator = TrustLayerValidator().odds_validator
        
        # Standard -110/-110 market
        # Implied prob: 52.38% + 52.38% = 104.76% -> 4.76% vig
        vig = validator.calculate_vig(Decimal("-110"), Decimal("-110"))
        assert round(float(vig), 2) == 4.76
        
        # Zero vig market (fair)
        vig = validator.calculate_vig(Decimal("+100"), Decimal("+100"))
        assert vig == 0

    def test_line_movement_steam(self):
        """Should detect sharp money movement (steam)."""
        validator = TrustLayerValidator().odds_validator
        
        # Line moves from -110 to -125 (getting more expensive)
        direction = validator.detect_line_movement(
            current=Decimal("-125"),
            previous=Decimal("-110"),
            market_side="favorite"
        )
        assert direction == OddsMovementDirection.STEAM
        
    def test_staleness_check(self):
        """Should reject old data."""
        validator = TrustLayerValidator().odds_validator
        
        stale_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        
        result = validator.verify_odds(
            claimed=Decimal("-110"),
            source=Decimal("-110"),
            source_timestamp=stale_time
        )
        assert result.status == VerificationStatus.STALE


class TestTeamNameValidator:
    """Tests for fuzzy team name matching."""
    
    def test_alias_resolution(self):
        """Should resolve common aliases to canonical names."""
        validator = TrustLayerValidator().team_validator
        
        # "Dubs" -> Golden State Warriors match
        result = validator.verify_team(
            claimed="Dubs",
            source="Golden State Warriors"
        )
        assert result.status == VerificationStatus.VERIFIED
        assert result.metadata.get("matched_via") == "alias_lookup"

    def test_fuzzy_partial_match(self):
        """Should give partial credit for substrings."""
        validator = TrustLayerValidator().team_validator
        
        result = validator.verify_team(
            claimed="Lakers",
            source="Los Angeles Lakers"
        )
        # Often verify_team logic handles substring as verified or partial depending on strictness
        # In our implementation: exact match or safe alias is verified. 
        # Substring is Partial.
        assert result.status == VerificationStatus.PARTIAL
        assert "partial match" in result.discrepancy.lower()


class TestIntegration:
    """Full prediction flow tests."""
    
    def test_full_prediction_verification(self):
        """Should verify a valid prediction end-to-end."""
        validator = TrustLayerValidator()
        
        prediction = AIPrediction(
            event_id="evt_123",
            prediction_type="moneyline",
            selection="Warriors",
            odds_claimed=Decimal("-150"),
            confidence=0.85,
            reasoning="Curry is hot"
        )
        
        passed, results = validator.verify_prediction(
            prediction=prediction,
            source_odds=Decimal("-150"),
            source_team="Golden State Warriors",
            source_timestamp=datetime.now(timezone.utc)
        )
        
        # Should pass despite "Warriors" != "Golden State Warriors" 
        # because of alias lookup or partial matching tolerance in a real system.
        # Let's check our implementation: 
        # Warriors is a KNOWN_ALIAS for Golden State Warriors. So it is VERIFIED.
        
        assert passed is True
        assert len(results) == 2  # Team + Odds checks
        assert results[0].status == VerificationStatus.VERIFIED
        assert results[1].status == VerificationStatus.VERIFIED

    def test_hallucination_catch(self):
        """Should fail widely divergent odds."""
        validator = TrustLayerValidator()
        
        prediction = AIPrediction(
            event_id="evt_123",
            prediction_type="moneyline",
            selection="Lakers",
            odds_claimed=Decimal("+200"),  # AI thinks massive underdog
            confidence=0.9,
            reasoning="LeBron out"
        )
        
        # Real odds are -500 (massive favorite)
        passed, results = validator.verify_prediction(
            prediction=prediction,
            source_odds=Decimal("-500"), 
            source_team="Lakers"
        )
        
        assert passed is False
        assert any(r.status == VerificationStatus.FAILED for r in results)
