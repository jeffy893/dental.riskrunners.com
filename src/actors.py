#!/usr/bin/env python3.10
"""
Defines the actors in the dental captive simulation:
12 Dentists (Practice Owners) with varied specializations and risk profiles.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List
import random


class SpecialtyType(Enum):
    """Dental specialization categories."""
    GENERAL = "general"
    IMPLANT = "implant"
    COSMETIC = "cosmetic"
    PEDIATRIC = "pediatric"


class RiskType(Enum):
    """Types of fortuitous risks that can occur."""
    EQUIPMENT_FAILURE = "equipment_failure"
    PROCEDURE_COMPLICATION = "procedure_complication"
    CYBER_BREACH = "cyber_breach"
    NONE = "none"


@dataclass
class Dentist:
    """Represents one of the 12 dentists in the captive syndicate."""
    id: int
    name: str
    specialty: SpecialtyType
    experience_years: int
    skill_level: float          # 0.0-1.0, affects risk probability
    annual_revenue: float
    tech_adoption_level: float  # 0.0-1.0, higher = more advanced tech = more innovation risk
    claims_history: int = 0

    def calculate_risk_probability(self) -> float:
        """Calculate annual probability of a fortuitous risk event."""
        base_risk = 0.12
        skill_mod = (1.0 - self.skill_level) * 0.08
        tech_mod = self.tech_adoption_level * 0.06  # more tech = more innovation risk
        return min(0.30, base_risk + skill_mod + tech_mod)

    def calculate_premium(self, base_premium: float = 50_000) -> float:
        """Calculate experience-modified annual premium."""
        exp_mod = 1.0
        if self.claims_history == 0:
            exp_mod = 0.85  # 15% safety credit
        elif self.claims_history >= 3:
            exp_mod = 1.20  # 20% surcharge
        tech_factor = 1.0 + (self.tech_adoption_level - 0.5) * 0.10
        return base_premium * exp_mod * tech_factor


def create_dentist_roster() -> List[Dentist]:
    """Create the roster of 12 dentists with varied profiles."""
    specs = [
        SpecialtyType.GENERAL, SpecialtyType.GENERAL, SpecialtyType.GENERAL,
        SpecialtyType.IMPLANT, SpecialtyType.IMPLANT, SpecialtyType.IMPLANT,
        SpecialtyType.COSMETIC, SpecialtyType.COSMETIC, SpecialtyType.COSMETIC,
        SpecialtyType.PEDIATRIC, SpecialtyType.PEDIATRIC, SpecialtyType.PEDIATRIC,
    ]
    names = [
        "Dr. Adams", "Dr. Baker", "Dr. Chen", "Dr. Davis",
        "Dr. Evans", "Dr. Foster", "Dr. Garcia", "Dr. Harris",
        "Dr. Ibrahim", "Dr. Jones", "Dr. Kim", "Dr. Lopez",
    ]
    roster = []
    for i in range(12):
        roster.append(Dentist(
            id=i + 1,
            name=names[i],
            specialty=specs[i],
            experience_years=random.randint(5, 25),
            skill_level=random.uniform(0.65, 0.95),
            annual_revenue=random.uniform(800_000, 2_500_000),
            tech_adoption_level=random.uniform(0.3, 0.9),
            claims_history=random.randint(0, 3),
        ))
    return roster


if __name__ == "__main__":
    roster = create_dentist_roster()
    print(f"Created {len(roster)} dentists:")
    for d in roster:
        print(f"  {d.name}: {d.specialty.value}, skill={d.skill_level:.2f}, "
              f"tech={d.tech_adoption_level:.2f}, risk_prob={d.calculate_risk_probability():.2%}")
