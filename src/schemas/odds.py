"""
Odds Data Schema

Pydantic models for sports betting odds data.
Demonstrates typed validation for real-time data feeds.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class OddsFormat(str, Enum):
    """Supported odds formats."""
    AMERICAN = "american"
    DECIMAL = "decimal"
    FRACTIONAL = "fractional"


class MarketStatus(str, Enum):
    """Market trading status."""
    OPEN = "open"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class OddsLine(BaseModel):
    """A single betting line with odds."""
    
    selection: str = Field(..., description="Team or outcome name")
    odds: Decimal = Field(..., description="Odds value")
    odds_format: OddsFormat = Field(default=OddsFormat.AMERICAN)
    implied_probability: Optional[Decimal] = Field(default=None)
    
    @field_validator("odds")
    @classmethod
    def validate_odds(cls, v: Decimal, info) -> Decimal:
        """Validate odds are within reasonable bounds."""
        # American odds: typically -10000 to +10000
        if v < -10000 or v > 10000:
            raise ValueError(f"Odds out of range: {v}")
        # American odds can't be between -100 and +100
        if -100 < v < 100 and v != 0:
            raise ValueError(f"Invalid American odds: {v}")
        return v
    
    def calculate_implied_probability(self) -> Decimal:
        """Calculate implied probability from odds."""
        if self.odds_format == OddsFormat.AMERICAN:
            if self.odds > 0:
                return Decimal(100) / (self.odds + 100)
            else:
                return abs(self.odds) / (abs(self.odds) + 100)
        elif self.odds_format == OddsFormat.DECIMAL:
            return Decimal(1) / self.odds
        return Decimal(0)


class Market(BaseModel):
    """A betting market with multiple lines."""
    
    market_id: str
    market_type: str = Field(..., description="e.g., 'moneyline', 'spread', 'total'")
    status: MarketStatus = Field(default=MarketStatus.OPEN)
    lines: List[OddsLine] = Field(default_factory=list)
    last_updated: datetime
    
    @property
    def is_active(self) -> bool:
        """Check if market is tradeable."""
        return self.status == MarketStatus.OPEN


class Event(BaseModel):
    """A sporting event with markets."""
    
    event_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    start_time: datetime
    markets: List[Market] = Field(default_factory=list)
    
    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: datetime) -> datetime:
        """Ensure event hasn't already ended (simplified check)."""
        return v


class OddsSnapshot(BaseModel):
    """A point-in-time snapshot of odds from a provider."""
    
    provider: str
    captured_at: datetime
    events: List[Event] = Field(default_factory=list)
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """Find event by ID."""
        for event in self.events:
            if event.event_id == event_id:
                return event
        return None
