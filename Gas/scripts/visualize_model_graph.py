"""
Create a Graphviz diagram showing how the baseline ensemble is wired.

The diagram highlights:
    • Feature groups feeding each model
    • Ridge, Futures, Inventory residual baselines
    • Weighted ensemble combination

Outputs:
    Gas/outputs/visualizations/model_ensemble_graph.(gv|png)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from graphviz import Digraph
import shutil


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize baseline ensemble data flow using Graphviz.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "visualizations",
        help="Directory to save the Graphviz diagram (default: outputs/visualizations)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        choices=["png", "pdf", "svg"],
        help="Rendered output format (default: png)",
    )
    return parser.parse_args()


def build_graph() -> Digraph:
    graph = Digraph("gasoline_baseline_ensemble", format="png")
    graph.attr(rankdir="LR", bgcolor="#0B0C10", fontname="Helvetica")

    graph.attr("node", shape="box", style="filled", color="#1F4068", fontcolor="white", fontname="Helvetica")

    graph.node(
        "Wholesale Features",
        "Wholesale Features\n(RBOB futures, WTI, cracks, lags)",
        fillcolor="#1B4F72",
    )
    graph.node(
        "Fundamental Features",
        "Fundamental Features\n(Inventory, utilization, imports, PADD3)",
        fillcolor="#154360",
    )

    graph.node(
        "Ridge Model",
        "Ridge Baseline\n(Full feature set)",
        fillcolor="#117A65",
    )
    graph.node(
        "Futures Model",
        "Linear Regression\n(Futures-only)",
        fillcolor="#0E6251",
    )
    graph.node(
        "Inventory Residual",
        "Ridge residual\n(Retail – RBOB)",
        fillcolor="#0E6655",
    )

    graph.node(
        "Ensemble",
        "Weighted Ensemble\n(0.5 Ridge, 0.3 Residual, 0.2 Futures)",
        shape="ellipse",
        fillcolor="#76448A",
    )

    graph.node(
        "Forecast Output",
        "October 31 Retail Forecast\n+ prediction intervals",
        shape="doubleoctagon",
        fillcolor="#B03A2E",
    )

    graph.edge("Wholesale Features", "Ridge Model")
    graph.edge("Wholesale Features", "Futures Model")
    graph.edge("Wholesale Features", "Inventory Residual", label="Retail margin inputs", fontsize="10")

    graph.edge("Fundamental Features", "Ridge Model")
    graph.edge("Fundamental Features", "Inventory Residual")

    graph.edge("Ridge Model", "Ensemble", label="0.5", fontsize="10")
    graph.edge("Futures Model", "Ensemble", label="0.2", fontsize="10")
    graph.edge("Inventory Residual", "Ensemble", label="0.3", fontsize="10")

    graph.edge("Ensemble", "Forecast Output")
    return graph


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if shutil.which("dot") is None:
        raise SystemExit(
            "Graphviz executable 'dot' not found. Install Graphviz (e.g., `brew install graphviz`) and ensure it is on PATH."
        )

    graph = build_graph()
    graph.format = args.format
    output_path = graph.render(filename="model_ensemble_graph", directory=str(output_dir), cleanup=True)
    print(f"✓ Model ensemble diagram written to {output_path}")


if __name__ == "__main__":
    main()
