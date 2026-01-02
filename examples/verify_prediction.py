"""
BetSpecs Trust Layer Example
---------------------------
Demonstrates how the Trust Layer catches hallucinations and validates
domain-specific nuances like line movement and team aliases.
"""

from decimal import Decimal
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trust_layer.validator import TrustLayerValidator, AIPrediction


def run_demo():
    print("Initializing Trust Layer Validator...")
    validator = TrustLayerValidator()
    
    # 1. The "Happy Path" - Valid Prediction with Intelligent Alias Matching
    print("\n--- Scenario 1: Valid Prediction (Alias Resolution) ---")
    pred_good = AIPrediction(
        event_id="evt_101",
        prediction_type="moneyline",
        selection="Dubs",  # Slang for Warriors
        odds_claimed=Decimal("-150"),
        confidence=0.85,
        reasoning="Home court advantage is significant."
    )
    
    print(f"AI Claim: {pred_good.selection} at {pred_good.odds_claimed} ({pred_good.reasoning})")
    print("Source: Golden State Warriors at -150")
    
    passed, results = validator.verify_prediction(
        prediction=pred_good,
        source_odds=Decimal("-150"),
        source_team="Golden State Warriors"
    )
    
    print(f"Result: {'✅ PASSED' if passed else '❌ FAILED'}")
    for r in results:
        print(f"  - [{r.status.value.upper()}] {r.claim_type}: {r.claim_value} vs {r.source_value}")
        if r.metadata:
            print(f"    Metadata: {r.metadata}")


    # 2. The "Hallucination" - Odds don't match reality
    print("\n--- Scenario 2: Hallucination Detection ---")
    pred_bad = AIPrediction(
        event_id="evt_102",
        prediction_type="point_spread",
        selection="Chiefs",
        odds_claimed=Decimal("+3.5"),  # AI thinks they are getting points
        confidence=0.92,
        reasoning="Mahomes is an underdog here."
    )
    
    print(f"AI Claim: {pred_bad.selection} {pred_bad.odds_claimed}")
    print("Source: Kansas City Chiefs -2.5 (Favorites)")
    
    passed, results = validator.verify_prediction(
        prediction=pred_bad,
        source_odds=Decimal("-2.5"),  # Actual odds
        source_team="Kansas City Chiefs"
    )
    
    print(f"Result: {'✅ PASSED' if passed else '❌ FAILED'}")
    for r in results:
        status_icon = "✅" if r.status == "verified" else "mw-emoji" if r.status == "partial" else "❌"
        # Correct icon for partial? use ⚠️
        if r.status == "partial": status_icon = "⚠️ "
        if r.status == "failed": status_icon = "❌"
        
        print(f"  - [{status_icon}] {r.claim_type}: {r.discrepancy}")


    # 3. The "Line Move" - Close but moved
    print("\n--- Scenario 3: Line Movement Detection ---")
    pred_move = AIPrediction(
        event_id="evt_103",
        prediction_type="total",
        selection="Over",
        odds_claimed=Decimal("210.5"),
        confidence=0.8,
        reasoning="High pace game expected."
    )
    
    print(f"AI Claim: Total {pred_move.odds_claimed}")
    print("Source: Total 212.0 (Line moved up)")
    
    passed, results = validator.verify_prediction(
        prediction=pred_move,
        source_odds=Decimal("212.0"),
        source_team="Over" # N/A for totals
    )
    
    print(f"Result: {'✅ PASSED' if passed else '❌ FAILED'}")
    for r in results:
        print(f"  - [{r.status.value.upper()}] {r.claim_type}: {r.discrepancy}")
        if r.metadata:
            print(f"    Metadata: {r.metadata}")


    # Audit Log
    print("\n--- Audit Log Export ---")
    stats = validator.get_statistics()
    print(f"Total Verifications: {stats['total_verifications']}")
    print(f"Rejection Rate: {stats['rejection_rate']:.1%}")


if __name__ == "__main__":
    run_demo()
