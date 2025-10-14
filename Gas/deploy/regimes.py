"""
Shared regime logic for gasoline price modeling.
"""

REGIMES = ["Normal", "Tight", "Crisis"]

def regime_label(row) -> str:
    """
    Assigns a regime label based on supply/demand stress features.
    Returns one of REGIMES.
    """
    # Example logic; update as needed for your project
    if row.get("days_supply", None) is None or row.get("utilization_pct", None) is None:
        return "Normal"
    if row["days_supply"] < 20 and row["utilization_pct"] > 90:
        return "Crisis"
    if row["days_supply"] < 24:
        return "Tight"
    return "Normal"
