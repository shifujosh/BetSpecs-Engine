#!/usr/bin/env python3
"""
Example: Trust Layer Verification

This script demonstrates how the Trust Layer catches
AI hallucinations before they reach the user.

Usage:
    python examples/verify_prediction.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trust_layer.validator import (
    TrustLayerValidator,
    AIPrediction,
    VerificationStatus,
)


def demonstrate_valid_prediction():
    """Show a prediction that passes verification."""
    print("\n" + "=" * 60)
    print("SCENARIO 1: Valid AI Prediction")
    print("=" * 60)
    
    validator = TrustLayerValidator()
    
    # Simulated AI output
    prediction = AIPrediction(
        event_id="nba_2025_lal_bos",
        prediction_type="moneyline",
        predicted_value="Los Angeles Lakers",
        confidence=0.68,
        reasoning="Lakers 8-2 in last 10 home games. Celtics missing key starter.",
        generated_at=datetime.now(timezone.utc),
    )
    
    # Simulated verified source data
    source_odds = Decimal("-145")
    source_team = "Los Angeles Lakers"
    
    print(f"\nAI Prediction:")
    print(f"  Team: {prediction.predicted_value}")
    print(f"  Confidence: {prediction.confidence:.0%}")
    print(f"  Reasoning: {prediction.reasoning}")
    
    print(f"\nSource Data:")
    print(f"  Team: {source_team}")
    print(f"  Odds: {source_odds}")
    
    # Run verification
    passed, results = validator.verify_prediction(
        prediction=prediction,
        source_odds=source_odds,
        source_team=source_team
    )
    
    print(f"\n{'✅ VERIFIED' if passed else '❌ REJECTED'}")
    for result in results:
        status_icon = "✓" if result.status == VerificationStatus.VERIFIED else "✗"
        print(f"  {status_icon} {result.claim}: {result.status.value}")


def demonstrate_hallucinated_prediction():
    """Show a prediction with hallucinated data that gets caught."""
    print("\n" + "=" * 60)
    print("SCENARIO 2: AI Hallucination Caught")
    print("=" * 60)
    
    validator = TrustLayerValidator()
    
    # Simulated AI output with hallucination
    prediction = AIPrediction(
        event_id="nba_2025_lal_bos",
        prediction_type="moneyline",
        predicted_value="Boston Celtics",  # WRONG - AI hallucinated
        confidence=1.2,  # INVALID - over 100%
        reasoning="Celtics undefeated this season.",  # FALSE
        generated_at=datetime.now(timezone.utc),
    )
    
    # Verified source data
    source_odds = Decimal("-145")
    source_team = "Los Angeles Lakers"  # Actual favorite
    
    print(f"\nAI Prediction (with hallucinations):")
    print(f"  Team: {prediction.predicted_value} ← WRONG")
    print(f"  Confidence: {prediction.confidence:.0%} ← INVALID")
    print(f"  Reasoning: {prediction.reasoning}")
    
    print(f"\nSource Data:")
    print(f"  Team: {source_team}")
    print(f"  Odds: {source_odds}")
    
    # Run verification
    passed, results = validator.verify_prediction(
        prediction=prediction,
        source_odds=source_odds,
        source_team=source_team
    )
    
    print(f"\n{'✅ VERIFIED' if passed else '❌ REJECTED'}")
    for result in results:
        status_icon = "✓" if result.status == VerificationStatus.VERIFIED else "✗"
        print(f"  {status_icon} {result.claim}: {result.status.value}")
        if result.discrepancy:
            print(f"      Reason: {result.discrepancy}")


def demonstrate_odds_verification():
    """Show odds value verification."""
    print("\n" + "=" * 60)
    print("SCENARIO 3: Odds Verification")
    print("=" * 60)
    
    validator = TrustLayerValidator(tolerance=Decimal("0.5"))
    
    test_cases = [
        ("Lakers", Decimal("-145"), Decimal("-145"), "Exact match"),
        ("Celtics", Decimal("+125"), Decimal("+125.3"), "Within tolerance"),
        ("Warriors", Decimal("-200"), Decimal("-155"), "Hallucinated odds"),
    ]
    
    print("\nVerifying AI-claimed odds against source:")
    print("-" * 60)
    
    for team, claimed, source, description in test_cases:
        result = validator.verify_odds_claim(claimed, source, team)
        status_icon = "✓" if result.status == VerificationStatus.VERIFIED else "✗"
        print(f"  {status_icon} {team}: AI={claimed}, Source={source} → {result.status.value}")
        print(f"      ({description})")
    
    print("\n" + "-" * 60)
    summary = validator.get_verification_summary()
    print(f"Summary: {summary['verified']}/{summary['total_checks']} verified ({summary['pass_rate']:.0%})")


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("BetSpecs Trust Layer Demonstration")
    print("=" * 60)
    print("\nThe Trust Layer prevents AI hallucinations from reaching users.")
    print("Every AI output is cross-referenced against verified source data.")
    
    demonstrate_valid_prediction()
    demonstrate_hallucinated_prediction()
    demonstrate_odds_verification()
    
    print("\n" + "=" * 60)
    print("Trust Layer demonstration complete.")
    print("No unverified AI outputs reached the display.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
