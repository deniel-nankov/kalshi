"""
Statistical Power Analysis for State-National Correlations

Goal: Determine if our current correlation estimates (4 time points) are statistically meaningful
      and calculate minimum sample size needed for robust conclusions

Questions:
1. What's the 95% CI on current correlation r=-0.230?
2. How many days needed to detect r=0.3 with 80% power?
3. Is current sample size sufficient for any conclusions?

Author: Research Team
Date: October 29, 2025
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 10)


def load_historical_data():
    """Load historical state snapshot data"""
    data_file = Path('state_analysis/data/historical_state_snapshot.csv')
    df = pd.read_csv(data_file)
    return df


def calculate_correlation_ci(r: float, n: int, alpha: float = 0.05):
    """
    Calculate confidence interval for Pearson correlation using Fisher z-transform
    
    Args:
        r: Observed correlation
        n: Sample size
        alpha: Significance level (default 0.05 for 95% CI)
    
    Returns:
        tuple: (lower_bound, upper_bound)
    """
    # Fisher z-transform
    z = np.arctanh(r)
    
    # Standard error of z
    se_z = 1 / np.sqrt(n - 3)
    
    # Critical value for two-tailed test
    z_crit = stats.norm.ppf(1 - alpha/2)
    
    # CI for z
    z_lower = z - z_crit * se_z
    z_upper = z + z_crit * se_z
    
    # Transform back to correlation scale
    r_lower = np.tanh(z_lower)
    r_upper = np.tanh(z_upper)
    
    return r_lower, r_upper


def bootstrap_correlation(x: np.ndarray, y: np.ndarray, n_bootstrap: int = 10000, alpha: float = 0.05):
    """
    Bootstrap confidence interval for correlation
    
    Args:
        x: First variable
        y: Second variable
        n_bootstrap: Number of bootstrap samples
        alpha: Significance level
    
    Returns:
        tuple: (lower_bound, upper_bound, bootstrap_correlations)
    """
    n = len(x)
    bootstrap_r = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        
        # Calculate correlation
        r_boot = np.corrcoef(x_boot, y_boot)[0, 1]
        bootstrap_r.append(r_boot)
    
    # Calculate percentile CI
    lower = np.percentile(bootstrap_r, alpha/2 * 100)
    upper = np.percentile(bootstrap_r, (1 - alpha/2) * 100)
    
    return lower, upper, np.array(bootstrap_r)


def power_analysis_correlation(r_true: float, n: int, alpha: float = 0.05):
    """
    Calculate statistical power for detecting a given correlation
    
    Args:
        r_true: True population correlation
        n: Sample size
        alpha: Significance level
    
    Returns:
        float: Statistical power (probability of detecting effect)
    """
    # Fisher z-transform
    z_true = np.arctanh(r_true)
    
    # Standard error under H1 (true r)
    se_z = 1 / np.sqrt(n - 3)
    
    # Critical value for H0: r=0
    z_crit = stats.norm.ppf(1 - alpha/2)
    
    # Non-centrality parameter
    ncp = z_true / se_z
    
    # Power (two-tailed test)
    power = 1 - stats.norm.cdf(z_crit - ncp) + stats.norm.cdf(-z_crit - ncp)
    
    return power


def sample_size_for_power(r_true: float, power: float = 0.80, alpha: float = 0.05):
    """
    Calculate minimum sample size needed to detect correlation with given power
    
    Args:
        r_true: True population correlation to detect
        power: Desired statistical power (default 0.80)
        alpha: Significance level (default 0.05)
    
    Returns:
        int: Minimum sample size
    """
    # Fisher z-transform
    z_true = np.arctanh(r_true)
    
    # Critical values
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    # Sample size calculation
    n = ((z_alpha + z_beta) / z_true) ** 2 + 3
    
    return int(np.ceil(n))


def analyze_current_data():
    """
    Analyze current 4-point correlation data
    """
    print("\n" + "="*60)
    print("📊 STATISTICAL POWER ANALYSIS")
    print("="*60 + "\n")
    
    # Load data
    df = load_historical_data()
    
    # Load state correlations
    corr_file = Path('state_analysis/outputs/state_correlations_preliminary.csv')
    corr_df = pd.read_csv(corr_file)
    
    print(f"Sample size: n = 4 time points")
    print(f"States analyzed: {len(corr_df)}")
    print(f"\n{'='*60}")
    print("CURRENT CORRELATION ESTIMATES")
    print(f"{'='*60}\n")
    
    # Overall statistics
    correlations = corr_df['correlation'].values
    avg_r = correlations.mean()
    median_r = np.median(correlations)
    std_r = correlations.std()
    
    print(f"Average correlation: {avg_r:.3f}")
    print(f"Median correlation: {median_r:.3f}")
    print(f"Std deviation: {std_r:.3f}")
    print(f"Range: [{correlations.min():.3f}, {correlations.max():.3f}]")
    
    # Fisher z CI for average correlation
    r_lower, r_upper = calculate_correlation_ci(avg_r, n=4)
    
    print(f"\n{'='*60}")
    print("CONFIDENCE INTERVALS (n=4)")
    print(f"{'='*60}\n")
    print(f"Average correlation: {avg_r:.3f}")
    print(f"95% CI (Fisher z): [{r_lower:.3f}, {r_upper:.3f}]")
    print(f"CI width: {r_upper - r_lower:.3f}")
    
    # Interpretation
    if r_lower < 0 and r_upper > 0:
        print(f"\n⚠️  INTERPRETATION: CI includes zero!")
        print(f"   Cannot conclude correlation is different from zero with n=4")
    elif r_lower > 0:
        print(f"\n✅ INTERPRETATION: Positive correlation (significant)")
    else:
        print(f"\n❓ INTERPRETATION: Likely negative correlation, but wide CI")
    
    # Power analysis for different effect sizes
    print(f"\n{'='*60}")
    print("POWER ANALYSIS: Current Sample Size (n=4)")
    print(f"{'='*60}\n")
    
    effect_sizes = [0.1, 0.3, 0.5, 0.7, 0.9]
    print(f"{'True r':<10} {'Power (80%?)':<15} {'Can detect?'}")
    print("-" * 40)
    
    for r in effect_sizes:
        power = power_analysis_correlation(r, n=4)
        can_detect = "✅ Yes" if power >= 0.80 else "❌ No"
        print(f"{r:<10.1f} {power:<15.3f} {can_detect}")
    
    # Sample size requirements
    print(f"\n{'='*60}")
    print("SAMPLE SIZE REQUIREMENTS (80% power, α=0.05)")
    print(f"{'='*60}\n")
    
    print(f"{'Detect r':<15} {'Min n':<15} {'Days needed':<15} {'Status'}")
    print("-" * 60)
    
    for r in effect_sizes:
        n_required = sample_size_for_power(r, power=0.80)
        status = "✅ Have it" if n_required <= 4 else f"❌ Need {n_required - 4} more"
        print(f"{r:<15.1f} {n_required:<15} {n_required:<15} {status}")
    
    # Special case: Our observed average r = -0.230
    print(f"\n{'='*60}")
    print(f"SPECIAL CASE: Observed r = {avg_r:.3f}")
    print(f"{'='*60}\n")
    
    n_needed = sample_size_for_power(abs(avg_r), power=0.80)
    print(f"To detect r={avg_r:.3f} with 80% power:")
    print(f"  Minimum n: {n_needed}")
    print(f"  Days needed: {n_needed}")
    print(f"  Current n: 4")
    print(f"  Additional days: {max(0, n_needed - 4)}")
    
    if n_needed > 4:
        print(f"\n⚠️  CONCLUSION: Current sample too small!")
        print(f"   Need {n_needed - 4} more days of data")
        print(f"   Timeline: Collect until Day {n_needed}")
    else:
        print(f"\n✅ CONCLUSION: Sample size sufficient!")
    
    return {
        'avg_r': avg_r,
        'ci_lower': r_lower,
        'ci_upper': r_upper,
        'n_current': 4,
        'n_needed': n_needed,
        'correlations': correlations,
    }


def create_visualizations(results: dict):
    """
    Create visualizations for power analysis
    """
    print(f"\n{'='*60}")
    print("📈 CREATING VISUALIZATIONS")
    print(f"{'='*60}\n")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Confidence intervals for different sample sizes
    ax1 = axes[0, 0]
    sample_sizes = np.arange(4, 31)
    ci_widths = []
    
    for n in sample_sizes:
        r_lower, r_upper = calculate_correlation_ci(results['avg_r'], n)
        ci_widths.append(r_upper - r_lower)
    
    ax1.plot(sample_sizes, ci_widths, 'b-', linewidth=2, label='95% CI Width')
    ax1.axvline(x=4, color='r', linestyle='--', label='Current n=4')
    ax1.axvline(x=results['n_needed'], color='g', linestyle='--', label=f'Required n={results["n_needed"]}')
    ax1.set_xlabel('Sample Size (days)', fontsize=12)
    ax1.set_ylabel('95% CI Width', fontsize=12)
    ax1.set_title('Confidence Interval Width vs Sample Size', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Power curves for different effect sizes
    ax2 = axes[0, 1]
    effect_sizes = [0.1, 0.3, 0.5, 0.7]
    sample_range = np.arange(4, 51)
    
    for r in effect_sizes:
        powers = [power_analysis_correlation(r, n) for n in sample_range]
        ax2.plot(sample_range, powers, linewidth=2, label=f'r = {r:.1f}')
    
    ax2.axhline(y=0.80, color='r', linestyle='--', label='80% Power')
    ax2.axvline(x=4, color='gray', linestyle='--', alpha=0.5, label='Current n=4')
    ax2.set_xlabel('Sample Size (days)', fontsize=12)
    ax2.set_ylabel('Statistical Power', fontsize=12)
    ax2.set_title('Power Analysis: Different Effect Sizes', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1])
    
    # Plot 3: Distribution of current correlations
    ax3 = axes[1, 0]
    ax3.hist(results['correlations'], bins=20, edgecolor='black', alpha=0.7)
    ax3.axvline(x=results['avg_r'], color='r', linestyle='--', linewidth=2, label=f'Mean = {results["avg_r"]:.3f}')
    ax3.axvline(x=0, color='gray', linestyle='-', linewidth=1, label='r = 0')
    ax3.set_xlabel('Correlation Coefficient', fontsize=12)
    ax3.set_ylabel('Number of States', fontsize=12)
    ax3.set_title('Distribution of State-National Correlations (n=4)', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Required sample size vs desired correlation
    ax4 = axes[1, 1]
    r_range = np.linspace(0.1, 0.9, 50)
    n_80power = [sample_size_for_power(r, power=0.80) for r in r_range]
    n_90power = [sample_size_for_power(r, power=0.90) for r in r_range]
    
    ax4.plot(r_range, n_80power, 'b-', linewidth=2, label='80% Power')
    ax4.plot(r_range, n_90power, 'g-', linewidth=2, label='90% Power')
    ax4.axhline(y=4, color='r', linestyle='--', label='Current n=4')
    ax4.axvline(x=abs(results['avg_r']), color='orange', linestyle='--', label=f'Observed |r|={abs(results["avg_r"]):.3f}')
    ax4.set_xlabel('True Correlation |r|', fontsize=12)
    ax4.set_ylabel('Required Sample Size (days)', fontsize=12)
    ax4.set_title('Sample Size Requirements', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim([0, 100])
    
    plt.tight_layout()
    
    # Save
    output_file = Path('state_analysis/outputs/power_analysis.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    
    plt.close()


def create_summary_report(results: dict):
    """
    Create markdown summary report
    """
    output_file = Path('state_analysis/outputs/POWER_ANALYSIS_REPORT.md')
    
    with open(output_file, 'w') as f:
        f.write("# 📊 Statistical Power Analysis Report\n\n")
        f.write(f"**Date:** October 29, 2025  \n")
        f.write(f"**Sample Size:** n = 4 time points  \n")
        f.write(f"**Purpose:** Assess reliability of current correlation estimates\n\n")
        
        f.write("---\n\n")
        f.write("## 🎯 KEY FINDINGS\n\n")
        
        f.write("### Current Correlation Estimate\n\n")
        f.write(f"- **Average correlation:** r = {results['avg_r']:.3f}\n")
        f.write(f"- **95% Confidence Interval:** [{results['ci_lower']:.3f}, {results['ci_upper']:.3f}]\n")
        f.write(f"- **CI Width:** {results['ci_upper'] - results['ci_lower']:.3f}\n\n")
        
        if results['ci_lower'] < 0 and results['ci_upper'] > 0:
            f.write("⚠️ **INTERPRETATION:** Confidence interval includes zero!\n\n")
            f.write("With only 4 time points, we **cannot conclude** that the correlation is different from zero. ")
            f.write("The observed r = -0.230 may be due to random variation.\n\n")
        
        f.write("### Sample Size Requirements\n\n")
        f.write(f"To detect r = {abs(results['avg_r']):.3f} with 80% power:\n\n")
        f.write(f"- **Minimum n:** {results['n_needed']} days\n")
        f.write(f"- **Current n:** {results['n_current']} days\n")
        f.write(f"- **Additional days needed:** {max(0, results['n_needed'] - results['n_current'])}\n\n")
        
        f.write("### Power Analysis Summary\n\n")
        f.write("| True r | Power (n=4) | Required n (80% power) |\n")
        f.write("|--------|-------------|------------------------|\n")
        
        for r in [0.1, 0.3, 0.5, 0.7, 0.9]:
            power_current = power_analysis_correlation(r, n=4)
            n_req = sample_size_for_power(r, power=0.80)
            f.write(f"| {r:.1f} | {power_current:.3f} | {n_req} |\n")
        
        f.write("\n---\n\n")
        f.write("## 🔬 CONCLUSIONS\n\n")
        
        if results['n_needed'] > 4:
            f.write("❌ **Current sample size INSUFFICIENT for robust conclusions**\n\n")
            f.write(f"With only 4 time points, confidence intervals are too wide to make definitive statements. ")
            f.write(f"We need **{results['n_needed'] - 4} more days** of data collection.\n\n")
            
            f.write("### Recommendations:\n\n")
            f.write(f"1. ✅ Continue daily state price collection\n")
            f.write(f"2. ✅ Target: Collect {results['n_needed']} consecutive days\n")
            f.write(f"3. ✅ Re-run correlation analysis after reaching minimum n\n")
            f.write(f"4. ❌ Do NOT add state features to model yet (insufficient statistical power)\n")
            f.write(f"5. ✅ Document preliminary findings in paper's \"Future Work\" section\n\n")
        else:
            f.write("✅ **Current sample size SUFFICIENT!**\n\n")
        
        f.write("---\n\n")
        f.write("## 📈 TIMELINE\n\n")
        f.write("| Phase | Days Collected | Statistical Power | Action |\n")
        f.write("|-------|----------------|-------------------|--------|\n")
        f.write(f"| **Current** | 4 | Low | Preliminary only |\n")
        f.write(f"| **Phase 1** | 10 | Moderate | Initial patterns |\n")
        f.write(f"| **Phase 2** | {results['n_needed']} | 80% | Robust conclusions |\n")
        f.write(f"| **Phase 3** | 30 | 90%+ | Granger causality |\n\n")
        
        f.write("**Bottom Line:** Negative correlations are **interesting but premature**. ")
        f.write(f"Continue daily collection for {results['n_needed'] - 4} more days before drawing conclusions.\n\n")
    
    print(f"✅ Saved: {output_file}")


if __name__ == '__main__':
    # Run analysis
    results = analyze_current_data()
    
    # Create visualizations
    create_visualizations(results)
    
    # Create report
    create_summary_report(results)
    
    print(f"\n{'='*60}")
    print("✅ POWER ANALYSIS COMPLETE!")
    print(f"{'='*60}\n")
    print("Files created:")
    print("  1. state_analysis/outputs/power_analysis.png")
    print("  2. state_analysis/outputs/POWER_ANALYSIS_REPORT.md")
    print("\n" + "="*60)
