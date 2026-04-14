#!/usr/bin/env python3.10
"""
Monte Carlo simulation for the Risk Runners Dental Captive.
Simulates thousands of years of operation to test solvency.
"""
import numpy as np
import pandas as pd
from typing import Dict
import random

from actors import create_dentist_roster, RiskType


class DentalCaptiveModel:
    """Monte Carlo simulation for the dental captive syndicate."""

    def __init__(self,
                 initial_capital: float = 1_000_000,
                 num_dentists: int = 12,
                 base_premium: float = 50_000):
        self.initial_capital = initial_capital
        self.num_dentists = num_dentists
        self.base_premium = base_premium
        self.roster = create_dentist_roster()
        self.annual_premium_income = sum(d.calculate_premium(base_premium) for d in self.roster)

        # Claim severity parameters (dental-specific)
        self.severity_params = {
            RiskType.EQUIPMENT_FAILURE: (35_000, 15_000),
            RiskType.PROCEDURE_COMPLICATION: (20_000, 8_000),
            RiskType.CYBER_BREACH: (45_000, 20_000),
        }
        self.risk_weights = {
            RiskType.EQUIPMENT_FAILURE: 0.40,
            RiskType.PROCEDURE_COMPLICATION: 0.35,
            RiskType.CYBER_BREACH: 0.25,
        }
        self.investment_return_rate = 0.04

    def simulate_year(self, current_capital: float) -> Dict:
        premium_income = self.annual_premium_income
        investment_income = current_capital * self.investment_return_rate
        total_claims = 0.0
        num_claims = 0

        for dentist in self.roster:
            if random.random() < dentist.calculate_risk_probability():
                risk_type = random.choices(
                    list(self.risk_weights.keys()),
                    weights=list(self.risk_weights.values())
                )[0]
                mean, std = self.severity_params[risk_type]
                claim = max(0, np.random.normal(mean, std))
                total_claims += claim
                num_claims += 1

        operating_expenses = premium_income * 0.10
        net_income = premium_income + investment_income - total_claims - operating_expenses
        ending_capital = current_capital + net_income
        expected_claims = sum(
            d.calculate_risk_probability() * 30_000 for d in self.roster
        )
        solvency_ratio = ending_capital / expected_claims if expected_claims > 0 else 0

        return {
            'premium_income': premium_income,
            'investment_income': investment_income,
            'total_claims': total_claims,
            'num_claims': num_claims,
            'operating_expenses': operating_expenses,
            'net_income': net_income,
            'ending_capital': ending_capital,
            'solvency_ratio': solvency_ratio,
            'is_solvent': ending_capital > 0,
        }

    def run_monte_carlo(self, num_simulations: int = 5_000, years: int = 10) -> pd.DataFrame:
        results = []
        for sim in range(num_simulations):
            capital = self.initial_capital
            for year in range(years):
                yr = self.simulate_year(capital)
                capital = yr['ending_capital']
                results.append({'simulation': sim, 'year': year, **yr})
            if sim % 1000 == 0:
                print(f"  Completed simulation {sim}/{num_simulations}")
        return pd.DataFrame(results)


def generate_summary_statistics(results_df: pd.DataFrame) -> Dict:
    final = results_df.groupby('simulation').last()
    return {
        'mean_final_capital': final['ending_capital'].mean(),
        'median_final_capital': final['ending_capital'].median(),
        'std_final_capital': final['ending_capital'].std(),
        'min_final_capital': final['ending_capital'].min(),
        'max_final_capital': final['ending_capital'].max(),
        'probability_of_ruin': (final['ending_capital'] <= 0).mean(),
        'mean_solvency_ratio': final['solvency_ratio'].mean(),
        'percentile_5_capital': final['ending_capital'].quantile(0.05),
        'percentile_95_capital': final['ending_capital'].quantile(0.95),
    }


if __name__ == "__main__":
    print("Running Dental Captive Monte Carlo...")
    model = DentalCaptiveModel()
    results = model.run_monte_carlo(num_simulations=1_000, years=10)
    stats = generate_summary_statistics(results)
    print(f"\nMean Final Capital: ${stats['mean_final_capital']:,.2f}")
    print(f"Probability of Ruin: {stats['probability_of_ruin']:.2%}")
    print(f"Mean Solvency Ratio: {stats['mean_solvency_ratio']:.2f}")
