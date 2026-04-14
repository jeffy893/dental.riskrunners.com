#!/usr/bin/env python3.10
"""
Main runner for the Risk Runners Dental Captive simulation.
Generates all graphs and data files for the website.
"""
import os
import sys
import json
import random
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from actors import create_dentist_roster, RiskType, SpecialtyType
from risk_model import DentalCaptiveModel, generate_summary_statistics

os.makedirs('../docs/assets', exist_ok=True)
os.makedirs('../docs/data', exist_ok=True)
os.makedirs('../data', exist_ok=True)


def run_monte_carlo_analysis():
    print("\n" + "=" * 60)
    print("MONTE CARLO SOLVENCY ANALYSIS")
    print("=" * 60)

    model = DentalCaptiveModel(initial_capital=1_000_000, num_dentists=12, base_premium=50_000)
    print(f"\nAnnual premium income: ${model.annual_premium_income:,.0f}")
    print("Running 5,000 simulations over 10 years...")
    results_df = model.run_monte_carlo(num_simulations=5_000, years=10)
    stats = generate_summary_statistics(results_df)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    final = results_df.groupby('simulation').last()
    ax1.hist(final['ending_capital'] / 1e6, bins=50, color='#2A9D8F', edgecolor='black', alpha=0.7)
    ax1.axvline(x=stats['mean_final_capital'] / 1e6, color='red', linestyle='--', linewidth=2,
                label=f"Mean: ${stats['mean_final_capital'] / 1e6:.2f}M")
    ax1.set_xlabel('Final Capital ($M)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Final Capital (10 Years)', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    yearly = results_df.groupby('year')['solvency_ratio'].agg(['mean', 'std'])
    ax2.plot(yearly.index, yearly['mean'], linewidth=2, color='#1B2A4A')
    ax2.fill_between(yearly.index, yearly['mean'] - yearly['std'],
                     yearly['mean'] + yearly['std'], alpha=0.3, color='#1B2A4A')
    ax2.axhline(y=1.0, color='red', linestyle='--', label='Minimum Solvency')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Solvency Ratio')
    ax2.set_title('Solvency Ratio Over Time (Mean ± Std Dev)', fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    for sim_id in range(20):
        sim_data = results_df[results_df['simulation'] == sim_id]
        ax3.plot(sim_data['year'], sim_data['ending_capital'] / 1e6, alpha=0.5, linewidth=1)
    ax3.set_xlabel('Year')
    ax3.set_ylabel('Capital ($M)')
    ax3.set_title('Sample Capital Trajectories (20 Simulations)', fontweight='bold')
    ax3.grid(True, alpha=0.3)

    metrics = ['Mean\nCapital', '5th\nPctile', 'Median', '95th\nPctile']
    values = [stats['mean_final_capital'] / 1e6, stats['percentile_5_capital'] / 1e6,
              stats['median_final_capital'] / 1e6, stats['percentile_95_capital'] / 1e6]
    ax4.bar(metrics, values, color=['#2A9D8F', '#E76F51', '#1B2A4A', '#27AE60'], edgecolor='black')
    ax4.set_ylabel('Capital ($M)')
    ax4.set_title('Key Risk Metrics (10-Year Horizon)', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('../docs/assets/monte_carlo_results.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: docs/assets/monte_carlo_results.png")
    results_df.to_csv('../data/monte_carlo_results.csv', index=False)
    return stats


def run_claims_analysis():
    print("\n" + "=" * 60)
    print("CLAIMS DISTRIBUTION ANALYSIS")
    print("=" * 60)

    roster = create_dentist_roster()
    all_claims = []
    for year in range(10):
        for d in roster:
            if random.random() < d.calculate_risk_probability():
                risk_type = random.choices(
                    [RiskType.EQUIPMENT_FAILURE, RiskType.PROCEDURE_COMPLICATION, RiskType.CYBER_BREACH],
                    weights=[0.40, 0.35, 0.25])[0]
                severity_map = {
                    RiskType.EQUIPMENT_FAILURE: (35_000, 15_000),
                    RiskType.PROCEDURE_COMPLICATION: (20_000, 8_000),
                    RiskType.CYBER_BREACH: (45_000, 20_000),
                }
                mean, std = severity_map[risk_type]
                amount = max(0, np.random.normal(mean, std))
                all_claims.append({
                    'year': year, 'dentist_id': d.id, 'dentist_name': d.name,
                    'specialty': d.specialty.value, 'risk_type': risk_type.value,
                    'amount': round(amount, 2),
                })

    df = pd.DataFrame(all_claims)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    if not df.empty:
        by_type = df.groupby('risk_type')['amount'].sum()
        wedges, texts, autotexts = ax1.pie(
            by_type.values, labels=[t.replace('_', ' ').title() for t in by_type.index],
            autopct='%1.1f%%', colors=['#F4A261', '#81B29A', '#7EB8DA'],
            startangle=90, textprops={'fontsize': 12})
        for t in autotexts:
            t.set_color('#1B2A4A')
            t.set_fontweight('bold')
            t.set_fontsize(14)
        ax1.set_title('Claims by Risk Type (10 Years)', fontweight='bold')

        by_spec = df.groupby('specialty')['amount'].count()
        ax2.bar(by_spec.index, by_spec.values, color='#2A9D8F', edgecolor='black')
        ax2.set_xlabel('Specialty')
        ax2.set_ylabel('Number of Claims')
        ax2.set_title('Claim Frequency by Specialty', fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('../docs/assets/claims_analysis.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: docs/assets/claims_analysis.png")
    df.to_csv('../data/claims_detail.csv', index=False)
    return df


def generate_simulated_policies():
    """Generate simulated policy JSON for the policy-slips page."""
    print("\n" + "=" * 60)
    print("GENERATING SIMULATED POLICIES")
    print("=" * 60)

    roster = create_dentist_roster()
    policies = []
    for d in roster:
        premium = d.calculate_premium(50_000)
        claims_detail = []
        total_incurred = 0
        for _ in range(d.claims_history):
            amt = round(random.uniform(5_000, 40_000), 2)
            total_incurred += amt
            claims_detail.append({
                "date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "type": random.choice(["Equipment Failure", "Procedure Complication", "Cyber Incident"]),
                "amount": amt,
                "status": "Closed"
            })

        policies.append({
            "policy_number": f"RR-DENT-2026-{d.id:03d}",
            "status": "Active",
            "insured_entity": {
                "name": d.name,
                "specialty": d.specialty.value.title(),
                "address": {"street": f"{random.randint(100,9999)} Dental Way",
                            "city": random.choice(["Phoenix", "Scottsdale", "Tempe", "Mesa", "Chandler"]),
                            "state": "AZ", "zip": f"8{random.randint(5000,5099)}"},
                "contact": {"name": d.name, "phone": f"(602) 555-{random.randint(1000,9999)}"}
            },
            "risk_class": {
                "primary": "Dental Practice Liability",
                "sub_class": f"{d.specialty.value.title()} Dentistry",
                "market_segment": d.specialty.value.title()
            },
            "term": {"effective_date": "2026-01-01", "expiration_date": "2026-12-31", "policy_period_days": 365},
            "coverage": {
                "limit_of_liability": {"per_occurrence": 250_000, "aggregate": 1_000_000, "currency": "USD"},
                "deductible": {"amount": 5_000, "applies_to": "per_occurrence"},
                "covered_perils": [
                    "Equipment failure (CBCT, 3D printers, autoclaves)",
                    "Unforeseen procedure complications",
                    "Cybersecurity breaches and data exposure",
                    "Material compatibility failures",
                    "Lab/subcontractor errors on restorations",
                    "Supply chain disruptions for specialized components"
                ]
            },
            "premium": {
                "base_premium": 50_000,
                "experience_modification": round(premium - 50_000, 2),
                "total_premium": round(premium, 2),
                "payment_terms": "Annual", "installments": 1
            },
            "risk_narrative": {
                "summary": f"{d.name} operates a {d.specialty.value} dental practice with {d.experience_years} years of experience and a tech adoption level of {d.tech_adoption_level:.0%}.",
                "operations_description": f"Practice specializing in {d.specialty.value} dentistry with annual revenue of ${d.annual_revenue:,.0f}. Employs advanced dental technology including digital imaging and CAD/CAM systems.",
                "risk_factors": [
                    f"Tech adoption level: {d.tech_adoption_level:.0%} (higher = more innovation risk)",
                    f"Experience: {d.experience_years} years",
                    f"Prior claims: {d.claims_history} in last 3 years"
                ],
                "loss_control_measures": [
                    "Quarterly equipment maintenance program",
                    "Annual cybersecurity audit",
                    "Continuing education requirements",
                    "Peer review protocols for advanced procedures"
                ]
            },
            "claims_history": {
                "prior_3_years": {
                    "total_claims": d.claims_history,
                    "total_incurred": round(total_incurred, 2),
                    "claims_detail": claims_detail
                }
            },
            "reinsurance": {
                "treaty_applicable": True,
                "excess_of_loss_attachment": 250_000,
                "reinsurer": "Arizona Re (Simulated)",
                "reinsurance_premium": round(premium * 0.15, 2)
            },
            "underwriting": {
                "underwriter": "Risk Runners Dental Captive",
                "approval_date": "2025-12-15",
                "claims_made_basis": False
            }
        })

    total_premium = sum(p['premium']['total_premium'] for p in policies)
    total_claims = sum(p['claims_history']['prior_3_years']['total_claims'] for p in policies)
    total_incurred = sum(p['claims_history']['prior_3_years']['total_incurred'] for p in policies)
    spec_dist = {}
    for p in policies:
        seg = p['risk_class']['market_segment']
        spec_dist[seg] = spec_dist.get(seg, 0) + 1

    data = {
        "generated": datetime.now().isoformat(),
        "summary_statistics": {
            "total_policies": len(policies),
            "total_premium_income": round(total_premium, 2),
            "total_claims_3_years": total_claims,
            "total_incurred_3_years": round(total_incurred, 2),
            "loss_ratio_3_years": round(total_incurred / total_premium, 4) if total_premium else 0,
            "specialty_distribution": spec_dist
        },
        "policies": policies
    }

    with open('../docs/data/simulatedPolicies.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("✓ Saved: docs/data/simulatedPolicies.json")
    return data


def main():
    print("\n" + "=" * 60)
    print("RISK RUNNERS DENTAL CAPTIVE SIMULATION")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    mc_stats = run_monte_carlo_analysis()
    claims_df = run_claims_analysis()
    policies = generate_simulated_policies()

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Mean Final Capital:   ${mc_stats['mean_final_capital']:,.2f}")
    print(f"Probability of Ruin:  {mc_stats['probability_of_ruin']:.2%}")
    print(f"Mean Solvency Ratio:  {mc_stats['mean_solvency_ratio']:.2f}")
    print(f"Total Claims (10yr):  {len(claims_df)}")
    print(f"Policies Generated:   {len(policies['policies'])}")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
