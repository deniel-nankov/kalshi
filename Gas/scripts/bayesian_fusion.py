"""
Bayesian Fusion: Combine Ridge Model with Kalshi Market Consensus
==================================================================

This module implements Bayesian fusion to optimally combine:
1. Ridge model predictions (your statistical model)
2. Kalshi market consensus ($1.2M trading volume)

Expected improvement: 53% reduction in uncertainty!

Author: Gas Price Forecasting System
Date: October 19, 2025
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Tuple, Dict
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from kalshi_markets import KalshiMarkets
except ImportError:
    # If running from different directory
    import importlib.util
    spec = importlib.util.spec_from_file_location("kalshi_markets", Path(__file__).parent / "kalshi_markets.py")
    kalshi_markets = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kalshi_markets)
    KalshiMarkets = kalshi_markets.KalshiMarkets


def bayesian_fusion(
    model_pred: float,
    model_std: float,
    market_pred: float,
    market_std: float
) -> Tuple[float, float, Tuple[float, float]]:
    """
    Combine model prediction with market consensus using Bayesian inference.
    
    This uses precision-weighted averaging, which is optimal in the sense
    of minimizing posterior variance (Minimum Variance Unbiased Estimator).
    
    Parameters:
    -----------
    model_pred : float
        Prediction from your Ridge model (e.g., 3.058)
    model_std : float
        Standard deviation of model prediction (e.g., 0.100)
    market_pred : float
        Prediction from Kalshi market consensus (e.g., 3.031)
    market_std : float
        Standard deviation of market distribution (e.g., 0.054)
        
    Returns:
    --------
    fused_pred : float
        Bayesian fusion prediction
    fused_std : float
        Posterior standard deviation (always < min(model_std, market_std))
    ci : tuple
        95% confidence interval (lower, upper)
        
    Example:
    --------
    >>> fused_pred, fused_std, ci = bayesian_fusion(3.058, 0.10, 3.031, 0.054)
    >>> print(f"Fused: ${fused_pred:.3f} ± ${fused_std:.3f}")
    >>> print(f"95% CI: [${ci[0]:.3f}, ${ci[1]:.3f}]")
    
    Mathematical Background:
    ------------------------
    Prior: N(μ_model, σ²_model)
    Likelihood: N(μ_market, σ²_market)
    
    Posterior: N(μ_fusion, σ²_fusion) where:
    
    Precision (inverse variance):
        τ_model = 1/σ²_model
        τ_market = 1/σ²_market
        τ_fusion = τ_model + τ_market
    
    Posterior mean (precision-weighted average):
        μ_fusion = (τ_model × μ_model + τ_market × μ_market) / τ_fusion
    
    Posterior variance:
        σ²_fusion = 1 / τ_fusion
    """
    # Calculate precisions (inverse variance)
    model_precision = 1.0 / (model_std ** 2)
    market_precision = 1.0 / (market_std ** 2)
    
    # Total precision (sum of precisions)
    total_precision = model_precision + market_precision
    
    # Precision-weighted average (posterior mean)
    fused_pred = (
        model_precision * model_pred + 
        market_precision * market_pred
    ) / total_precision
    
    # Posterior variance (inverse of total precision)
    fused_var = 1.0 / total_precision
    fused_std = np.sqrt(fused_var)
    
    # 95% confidence interval (±1.96σ)
    ci_lower = fused_pred - 1.96 * fused_std
    ci_upper = fused_pred + 1.96 * fused_std
    
    return fused_pred, fused_std, (ci_lower, ci_upper)


def ensemble_prediction(
    predictions: Dict[str, Tuple[float, float]]
) -> Tuple[float, float, Dict]:
    """
    Combine multiple predictions using inverse-variance weighting.
    
    Parameters:
    -----------
    predictions : dict
        Dictionary of {name: (prediction, std)} pairs
        Example: {
            'Ridge': (3.058, 0.100),
            'Kalshi': (3.031, 0.054),
            'GBM': (3.045, 0.080)
        }
        
    Returns:
    --------
    ensemble_pred : float
        Weighted average prediction
    ensemble_std : float
        Ensemble standard deviation
    weights : dict
        Normalized weights for each model
        
    Example:
    --------
    >>> predictions = {
    ...     'Ridge': (3.058, 0.100),
    ...     'Kalshi': (3.031, 0.054),
    ...     'Volume-Weighted': (3.070, 0.080)
    ... }
    >>> pred, std, weights = ensemble_prediction(predictions)
    """
    # Calculate precision for each prediction
    precisions = {}
    for name, (pred, std) in predictions.items():
        precisions[name] = 1.0 / (std ** 2)
    
    # Total precision
    total_precision = sum(precisions.values())
    
    # Normalized weights
    weights = {name: prec / total_precision for name, prec in precisions.items()}
    
    # Weighted average
    ensemble_pred = sum(
        weights[name] * pred 
        for name, (pred, std) in predictions.items()
    )
    
    # Ensemble variance
    ensemble_var = 1.0 / total_precision
    ensemble_std = np.sqrt(ensemble_var)
    
    return ensemble_pred, ensemble_std, weights


def make_fusion_prediction(
    model_pred: float,
    model_std: float = 0.100,
    month: str = "OCT",
    year: str = "25",
    verbose: bool = True
) -> Dict:
    """
    Make fused prediction combining model with current Kalshi consensus.
    
    Parameters:
    -----------
    model_pred : float
        Prediction from your Ridge model
    model_std : float
        Model uncertainty (default: 0.100 based on R²=0.611)
    month : str
        Month to fetch Kalshi data (OCT, NOV, DEC)
    year : str
        Two-digit year (25 for 2025)
    verbose : bool
        Print detailed output
        
    Returns:
    --------
    dict with keys:
        - model_pred: Your model prediction
        - model_std: Model uncertainty
        - market_pred: Kalshi consensus
        - market_std: Market uncertainty
        - fused_pred: Bayesian fusion
        - fused_std: Fusion uncertainty
        - ci_95: 95% confidence interval
        - uncertainty_reduction: % improvement
        - weights: Model vs market weights
        
    Example:
    --------
    >>> result = make_fusion_prediction(3.058, month="OCT", year="25")
    >>> print(f"Final prediction: ${result['fused_pred']:.3f}")
    """
    # Get Kalshi market consensus
    try:
        markets = KalshiMarkets.get_gas_markets(month, year)
        
        if not markets:
            if verbose:
                print("⚠️ No Kalshi markets found, using model prediction only")
            return {
                'model_pred': model_pred,
                'model_std': model_std,
                'market_pred': None,
                'market_std': None,
                'fused_pred': model_pred,
                'fused_std': model_std,
                'ci_95': (model_pred - 1.96*model_std, model_pred + 1.96*model_std),
                'uncertainty_reduction': 0.0,
                'weights': {'model': 1.0, 'market': 0.0}
            }
        
        consensus = KalshiMarkets.get_market_consensus(markets)
        market_pred = consensus['expected_value']
        
        # Estimate market uncertainty from fitted distribution
        # Use spread of high-probability strikes as proxy
        high_prob_markets = [m for m in markets if 20 <= m['probability'] <= 80]
        if high_prob_markets:
            strikes = [m['strike_price'] for m in high_prob_markets]
            market_std = np.std(strikes) if len(strikes) > 1 else 0.054
        else:
            market_std = 0.054  # Default from normal fit
        
    except Exception as e:
        if verbose:
            print(f"⚠️ Error fetching Kalshi: {e}")
            print("Using model prediction only")
        return {
            'model_pred': model_pred,
            'model_std': model_std,
            'market_pred': None,
            'market_std': None,
            'fused_pred': model_pred,
            'fused_std': model_std,
            'ci_95': (model_pred - 1.96*model_std, model_pred + 1.96*model_std),
            'uncertainty_reduction': 0.0,
            'weights': {'model': 1.0, 'market': 0.0}
        }
    
    # Bayesian fusion
    fused_pred, fused_std, ci = bayesian_fusion(
        model_pred, model_std,
        market_pred, market_std
    )
    
    # Calculate weights
    model_precision = 1.0 / (model_std ** 2)
    market_precision = 1.0 / (market_std ** 2)
    total_precision = model_precision + market_precision
    
    model_weight = model_precision / total_precision
    market_weight = market_precision / total_precision
    
    # Uncertainty reduction
    reduction = (model_std - fused_std) / model_std
    
    if verbose:
        print("="*80)
        print("🎯 BAYESIAN FUSION PREDICTION")
        print("="*80)
        print()
        print("INPUT PREDICTIONS:")
        print(f"  Ridge Model:  ${model_pred:.3f} ± ${model_std:.3f} (weight: {model_weight:.1%})")
        print(f"  Kalshi Market: ${market_pred:.3f} ± ${market_std:.3f} (weight: {market_weight:.1%})")
        print()
        print("FUSED PREDICTION:")
        print(f"  Posterior:     ${fused_pred:.3f} ± ${fused_std:.3f}")
        print(f"  95% CI:        [${ci[0]:.3f}, ${ci[1]:.3f}]")
        print()
        print("IMPROVEMENT:")
        print(f"  Uncertainty reduction: {reduction:.1%}")
        print(f"  From ±${model_std:.3f} to ±${fused_std:.3f}")
        print()
        print("="*80)
    
    return {
        'model_pred': model_pred,
        'model_std': model_std,
        'market_pred': market_pred,
        'market_std': market_std,
        'fused_pred': fused_pred,
        'fused_std': fused_std,
        'ci_95': ci,
        'uncertainty_reduction': reduction,
        'weights': {
            'model': model_weight,
            'market': market_weight
        },
        'consensus': consensus
    }


def test_bayesian_fusion():
    """Test Bayesian fusion with current data."""
    
    print("\n" + "="*80)
    print("🧪 TESTING BAYESIAN FUSION")
    print("="*80)
    print()
    
    # Test case 1: Simple fusion
    print("Test 1: Basic fusion")
    print("-"*80)
    
    fused_pred, fused_std, ci = bayesian_fusion(
        model_pred=3.058,
        model_std=0.100,
        market_pred=3.031,
        market_std=0.054
    )
    
    print(f"Model:  $3.058 ± $0.100")
    print(f"Market: $3.031 ± $0.054")
    print(f"Fused:  ${fused_pred:.3f} ± ${fused_std:.3f}")
    print(f"95% CI: [${ci[0]:.3f}, ${ci[1]:.3f}]")
    print(f"Uncertainty reduced by {(1 - fused_std/0.100):.1%}")
    print()
    
    # Test case 2: Ensemble
    print("Test 2: Multi-model ensemble")
    print("-"*80)
    
    predictions = {
        'Ridge': (3.058, 0.100),
        'Kalshi PDF': (2.970, 0.050),
        'Kalshi Normal': (3.031, 0.054),
        'Volume-Weighted': (3.070, 0.080)
    }
    
    ensemble_pred, ensemble_std, weights = ensemble_prediction(predictions)
    
    print("Models:")
    for name, (pred, std) in predictions.items():
        weight = weights[name]
        print(f"  {name:18s}: ${pred:.3f} ± ${std:.3f} (weight: {weight:.1%})")
    
    print()
    print(f"Ensemble: ${ensemble_pred:.3f} ± ${ensemble_std:.3f}")
    print(f"Uncertainty reduced by {(1 - ensemble_std/0.100):.1%} vs Ridge alone")
    print()
    
    # Test case 3: Full workflow
    print("Test 3: Full prediction workflow")
    print("-"*80)
    
    result = make_fusion_prediction(
        model_pred=3.058,
        month="OCT",
        year="25",
        verbose=True
    )
    
    return result


if __name__ == "__main__":
    test_bayesian_fusion()
