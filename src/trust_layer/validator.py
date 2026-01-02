"""
Trust Layer: AI Output Validator

The Trust Layer is the critical component that prevents hallucinated
data from reaching the user. It cross-references AI-generated insights
against verified source data.

Principles:
1. Never trust raw AI output
2. Always cross-reference with source data
3. Fail loudly on discrepancy
4. Log all verifications for audit
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class VerificationStatus(str, Enum):
    """Result of verification check."""
    VERIFIED = "verified"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class VerificationResult:
    """Result of a single verification check."""
    status: VerificationStatus
    claim: str
    source_value: Optional[str]
    ai_value: Optional[str]
    discrepancy: Optional[str]
    timestamp: datetime


@dataclass
class AIPrediction:
    """An AI-generated prediction or insight."""
    event_id: str
    prediction_type: str
    predicted_value: str
    confidence: float
    reasoning: str
    generated_at: datetime


class TrustLayerValidator:
    """
    Validates AI outputs against verified source data.
    
    The Trust Layer sits between the AI and the user interface.
    No AI output reaches the display without passing verification.
    """
    
    def __init__(self, tolerance: Decimal = Decimal("0.01")):
        """
        Initialize validator.
        
        Args:
            tolerance: Acceptable deviation for numeric comparisons
        """
        self.tolerance = tolerance
        self.verification_log: List[VerificationResult] = []
    
    def verify_odds_claim(
        self, 
        claimed_odds: Decimal, 
        source_odds: Decimal,
        selection: str
    ) -> VerificationResult:
        """
        Verify AI's claimed odds match source data.
        
        Args:
            claimed_odds: What the AI said the odds are
            source_odds: What the verified data source shows
            selection: The team/outcome being checked
        
        Returns:
            VerificationResult with status and details
        """
        diff = abs(claimed_odds - source_odds)
        
        if diff <= self.tolerance:
            result = VerificationResult(
                status=VerificationStatus.VERIFIED,
                claim=f"Odds for {selection}",
                source_value=str(source_odds),
                ai_value=str(claimed_odds),
                discrepancy=None,
                timestamp=datetime.now(timezone.utc),
            )
        else:
            result = VerificationResult(
                status=VerificationStatus.FAILED,
                claim=f"Odds for {selection}",
                source_value=str(source_odds),
                ai_value=str(claimed_odds),
                discrepancy=f"Difference of {diff} exceeds tolerance {self.tolerance}",
                timestamp=datetime.now(timezone.utc),
            )
        
        self.verification_log.append(result)
        return result
    
    def verify_team_name(
        self, 
        claimed_team: str, 
        source_team: str
    ) -> VerificationResult:
        """
        Verify AI's team name matches source.
        
        Catches hallucinated team names.
        """
        # Normalize for comparison
        claimed_normalized = claimed_team.lower().strip()
        source_normalized = source_team.lower().strip()
        
        if claimed_normalized == source_normalized:
            status = VerificationStatus.VERIFIED
            discrepancy = None
        elif claimed_normalized in source_normalized or source_normalized in claimed_normalized:
            status = VerificationStatus.PARTIAL
            discrepancy = "Partial match - may be abbreviation"
        else:
            status = VerificationStatus.FAILED
            discrepancy = "Team name mismatch"
        
        result = VerificationResult(
            status=status,
            claim="Team name",
            source_value=source_team,
            ai_value=claimed_team,
            discrepancy=discrepancy,
            timestamp=datetime.now(timezone.utc),
        )
        
        self.verification_log.append(result)
        return result
    
    def verify_prediction(
        self, 
        prediction: AIPrediction,
        source_odds: Decimal,
        source_team: str
    ) -> Tuple[bool, List[VerificationResult]]:
        """
        Run full verification suite on an AI prediction.
        
        Returns:
            Tuple of (all_passed, list of results)
        """
        results = []
        
        # Verify team name
        team_result = self.verify_team_name(
            claimed_team=prediction.predicted_value,
            source_team=source_team
        )
        results.append(team_result)
        
        # Check confidence is reasonable
        if prediction.confidence > 1.0 or prediction.confidence < 0:
            results.append(VerificationResult(
                status=VerificationStatus.FAILED,
                claim="Confidence score",
                source_value="0.0-1.0",
                ai_value=str(prediction.confidence),
                discrepancy="Confidence out of valid range",
                timestamp=datetime.now(timezone.utc),
            ))
        
        all_passed = all(r.status == VerificationStatus.VERIFIED for r in results)
        return all_passed, results
    
    def get_verification_summary(self) -> dict:
        """Get summary of all verifications performed."""
        total = len(self.verification_log)
        verified = sum(1 for r in self.verification_log if r.status == VerificationStatus.VERIFIED)
        failed = sum(1 for r in self.verification_log if r.status == VerificationStatus.FAILED)
        
        return {
            "total_checks": total,
            "verified": verified,
            "failed": failed,
            "pass_rate": verified / total if total > 0 else 0.0,
        }
