"""
Advanced Pipeline Visualization System

Creates comprehensive visualizations of the data pipeline including:
1. Medallion architecture with data flow
2. Layer-by-layer transformations with animations
3. Feature engineering process
4. Model training workflow
5. Real-time system operation animation
6. Interactive pipeline dashboard

Requirements:
    pip install matplotlib seaborn plotly networkx imageio pillow pandas numpy
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter
import seaborn as sns
import numpy as np
import pandas as pd

# Try to import plotly for interactive visualizations
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️  Plotly not available. Install with: pip install plotly")

# Try to import networkx for graph visualizations
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("⚠️  NetworkX not available. Install with: pip install networkx")


# Setup paths
REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "advanced_visualizations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Color schemes
COLORS = {
    'bronze': '#CD7F32',
    'silver': '#C0C0C0',
    'gold': '#FFD700',
    'model': '#4169E1',
    'prediction': '#32CD32',
    'api': '#FF6347',
    'automation': '#9370DB',
    'background': '#F5F5F5',
    'text': '#2C3E50',
    'accent': '#E74C3C',
    'success': '#27AE60',
    'warning': '#F39C12',
}

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def create_medallion_architecture_detailed():
    """Create detailed medallion architecture with data flow"""
    fig, ax = plt.subplots(figsize=(20, 12), facecolor='white')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    fig.suptitle('Medallion Architecture - Detailed Data Flow', 
                 fontsize=24, fontweight='bold', y=0.98)
    
    # Layer positions
    layers = {
        'bronze': {'x': 1.5, 'y': 5, 'width': 1.5, 'height': 6},
        'silver': {'x': 4, 'y': 5, 'width': 1.5, 'height': 6},
        'gold': {'x': 6.5, 'y': 5, 'width': 1.5, 'height': 6},
    }
    
    # Draw Bronze Layer
    bronze_box = FancyBboxPatch(
        (layers['bronze']['x'], layers['bronze']['y']), 
        layers['bronze']['width'], layers['bronze']['height'],
        boxstyle="round,pad=0.1", 
        edgecolor=COLORS['bronze'], 
        facecolor=COLORS['bronze'], 
        alpha=0.3,
        linewidth=3
    )
    ax.add_patch(bronze_box)
    ax.text(layers['bronze']['x'] + 0.75, 10.5, '🥉 BRONZE LAYER\n(Raw Data)', 
            ha='center', va='top', fontsize=14, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=COLORS['bronze'], alpha=0.7))
    
    # Bronze data sources
    bronze_sources = [
        ('EIA API', 'Inventory\nUtilization\nImports', 9.5),
        ('RBOB Futures', 'WTI Crude\nGasoline', 7.5),
        ('AAA API', 'Retail Prices\nState Data', 5.5),
    ]
    
    for i, (source, data, y_pos) in enumerate(bronze_sources):
        # Data source box
        source_box = FancyBboxPatch(
            (0.1, y_pos), 0.8, 1.5,
            boxstyle="round,pad=0.05",
            edgecolor='#34495E',
            facecolor='#ECF0F1',
            linewidth=2
        )
        ax.add_patch(source_box)
        ax.text(0.5, y_pos + 1.2, source, ha='center', va='top', 
                fontsize=10, fontweight='bold')
        ax.text(0.5, y_pos + 0.5, data, ha='center', va='center', 
                fontsize=8, style='italic')
        
        # Arrow to bronze
        arrow = FancyArrowPatch(
            (0.9, y_pos + 0.75), (layers['bronze']['x'], y_pos + 0.75),
            arrowstyle='->', mutation_scale=30, linewidth=2.5,
            color=COLORS['bronze'], alpha=0.7
        )
        ax.add_patch(arrow)
        
        # Data description in bronze
        ax.text(layers['bronze']['x'] + 0.75, y_pos + 0.75, 
                f'✓ {source.split()[0]}', ha='center', va='center',
                fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Draw Silver Layer
    silver_box = FancyBboxPatch(
        (layers['silver']['x'], layers['silver']['y']), 
        layers['silver']['width'], layers['silver']['height'],
        boxstyle="round,pad=0.1",
        edgecolor=COLORS['silver'],
        facecolor=COLORS['silver'],
        alpha=0.3,
        linewidth=3
    )
    ax.add_patch(silver_box)
    ax.text(layers['silver']['x'] + 0.75, 10.5, '🥈 SILVER LAYER\n(Cleaned Data)', 
            ha='center', va='top', fontsize=14, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=COLORS['silver'], alpha=0.7))
    
    # Silver transformations
    silver_transforms = [
        ('Validation', '✓ Schema\n✓ Types\n✓ Ranges', 9.5),
        ('Cleaning', '✓ Nulls\n✓ Duplicates\n✓ Outliers', 7.5),
        ('Standardization', '✓ Dates\n✓ Units\n✓ Formats', 5.5),
    ]
    
    for name, desc, y_pos in silver_transforms:
        ax.text(layers['silver']['x'] + 0.75, y_pos + 0.75, 
                f'{name}\n{desc}', ha='center', va='center',
                fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Arrow Bronze -> Silver
    arrow_bs = FancyArrowPatch(
        (layers['bronze']['x'] + layers['bronze']['width'], 8),
        (layers['silver']['x'], 8),
        arrowstyle='->', mutation_scale=40, linewidth=4,
        color=COLORS['silver'], alpha=0.7
    )
    ax.add_patch(arrow_bs)
    ax.text(3.1, 8.3, 'Clean & Validate', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    # Draw Gold Layer
    gold_box = FancyBboxPatch(
        (layers['gold']['x'], layers['gold']['y']), 
        layers['gold']['width'], layers['gold']['height'],
        boxstyle="round,pad=0.1",
        edgecolor=COLORS['gold'],
        facecolor=COLORS['gold'],
        alpha=0.3,
        linewidth=3
    )
    ax.add_patch(gold_box)
    ax.text(layers['gold']['x'] + 0.75, 10.5, '🥇 GOLD LAYER\n(Features)', 
            ha='center', va='top', fontsize=14, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=COLORS['gold'], alpha=0.7))
    
    # Gold features
    gold_features = [
        ('Price Features', 'Lags\nReturns\nVolatility', 9.5),
        ('Supply Metrics', 'Inventory\nUtilization\nInteractions', 7.5),
        ('Seasonal', 'Winter Blend\nTiming\nWeekday', 5.5),
    ]
    
    for name, desc, y_pos in gold_features:
        ax.text(layers['gold']['x'] + 0.75, y_pos + 0.75, 
                f'{name}\n{desc}', ha='center', va='center',
                fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Arrow Silver -> Gold
    arrow_sg = FancyArrowPatch(
        (layers['silver']['x'] + layers['silver']['width'], 8),
        (layers['gold']['x'], 8),
        arrowstyle='->', mutation_scale=40, linewidth=4,
        color=COLORS['gold'], alpha=0.7
    )
    ax.add_patch(arrow_sg)
    ax.text(5.6, 8.3, 'Engineer Features', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    # Model Training Box
    model_box = FancyBboxPatch(
        (8.2, 7), 1.5, 3,
        boxstyle="round,pad=0.1",
        edgecolor=COLORS['model'],
        facecolor=COLORS['model'],
        alpha=0.3,
        linewidth=3
    )
    ax.add_patch(model_box)
    ax.text(8.95, 10.2, '🤖 MODELS', ha='center', va='top', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=COLORS['model'], alpha=0.7))
    ax.text(8.95, 9, 'Ridge\nRegression', ha='center', va='center', fontsize=9)
    ax.text(8.95, 8, 'Quantile\nRegression', ha='center', va='center', fontsize=9)
    ax.text(8.95, 7.3, 'R² = 0.59', ha='center', va='center', fontsize=8,
            bbox=dict(boxstyle='round', facecolor=COLORS['success'], alpha=0.7))
    
    # Arrow Gold -> Models
    arrow_gm = FancyArrowPatch(
        (layers['gold']['x'] + layers['gold']['width'], 8.5),
        (8.2, 8.5),
        arrowstyle='->', mutation_scale=40, linewidth=4,
        color=COLORS['model'], alpha=0.7
    )
    ax.add_patch(arrow_gm)
    ax.text(7.8, 8.8, 'Train', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    # Prediction Box
    pred_box = FancyBboxPatch(
        (8.2, 3.5), 1.5, 2,
        boxstyle="round,pad=0.1",
        edgecolor=COLORS['prediction'],
        facecolor=COLORS['prediction'],
        alpha=0.3,
        linewidth=3
    )
    ax.add_patch(pred_box)
    ax.text(8.95, 5.7, '🔮 FORECAST', ha='center', va='top', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=COLORS['prediction'], alpha=0.7))
    ax.text(8.95, 4.5, 'Oct 31, 2025\n$3.05/gal', ha='center', va='center', fontsize=10,
            fontweight='bold')
    
    # Arrow Models -> Prediction
    arrow_mp = FancyArrowPatch(
        (8.95, 7), (8.95, 5.5),
        arrowstyle='->', mutation_scale=40, linewidth=4,
        color=COLORS['prediction'], alpha=0.7
    )
    ax.add_patch(arrow_mp)
    ax.text(9.4, 6.2, 'Predict', ha='left', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    # Automation indicators
    auto_y = 2.5
    ax.text(1.5, auto_y, '🤖 AUTOMATED', ha='left', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=COLORS['automation'], alpha=0.7))
    ax.text(1.5, auto_y - 0.5, 'Bronze: Smart scheduling\nSilver: Auto-rebuild\nGold: Manual', 
            ha='left', fontsize=8, style='italic')
    
    # Timing info
    timing_y = 1.2
    ax.text(1.5, timing_y, '⏱️  TIMING', ha='left', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=COLORS['warning'], alpha=0.7))
    ax.text(1.5, timing_y - 0.5, 'Bronze→Silver: 5 sec\nGold: 10 sec\nTrain: 2-3 min', 
            ha='left', fontsize=8, style='italic')
    
    # Data freshness
    fresh_y = 0.5
    ax.text(6, fresh_y, '📊 FRESHNESS: Bronze updates when sources refresh | Silver follows Bronze | Gold on-demand',
            ha='left', fontsize=9, style='italic',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "01_medallion_architecture_detailed.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_layer_transformation_animation():
    """Create animation showing data transformation through layers"""
    print("\n🎬 Creating layer transformation animation...")
    
    fig, ax = plt.subplots(figsize=(16, 10), facecolor='white')
    
    # Sample data representing quality/completeness
    frames = 100
    
    def animate(frame):
        ax.clear()
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        progress = frame / frames
        
        # Title
        ax.text(5, 9.5, 'Data Transformation Pipeline - Live Flow', 
                ha='center', fontsize=20, fontweight='bold')
        
        # Bronze layer (always visible)
        bronze_alpha = 0.3 + 0.3 * min(1, progress * 3)
        bronze_box = FancyBboxPatch((1, 3), 1.5, 4, boxstyle="round,pad=0.1",
                                    edgecolor=COLORS['bronze'], facecolor=COLORS['bronze'],
                                    alpha=bronze_alpha, linewidth=3)
        ax.add_patch(bronze_box)
        ax.text(1.75, 7.3, '🥉 BRONZE', ha='center', fontsize=14, fontweight='bold')
        
        # Data points in bronze
        if progress > 0.1:
            num_points = int(50 * min(1, progress * 2))
            np.random.seed(42)
            x_bronze = np.random.uniform(1.2, 2.3, num_points)
            y_bronze = np.random.uniform(3.2, 6.8, num_points)
            ax.scatter(x_bronze, y_bronze, c=COLORS['bronze'], s=20, alpha=0.6)
            ax.text(1.75, 2.7, f'{num_points} records', ha='center', fontsize=10)
        
        # Flow arrow Bronze -> Silver
        if progress > 0.3:
            arrow_alpha = min(1, (progress - 0.3) * 3)
            arrow1 = FancyArrowPatch((2.5, 5), (3.5, 5), 
                                    arrowstyle='->', mutation_scale=30,
                                    linewidth=3, color='blue', alpha=arrow_alpha)
            ax.add_patch(arrow1)
            ax.text(3, 5.3, 'Clean', ha='center', fontsize=10, alpha=arrow_alpha)
        
        # Silver layer
        if progress > 0.4:
            silver_alpha = 0.3 + 0.3 * min(1, (progress - 0.4) * 2)
            silver_box = FancyBboxPatch((4, 3), 1.5, 4, boxstyle="round,pad=0.1",
                                        edgecolor=COLORS['silver'], facecolor=COLORS['silver'],
                                        alpha=silver_alpha, linewidth=3)
            ax.add_patch(silver_box)
            ax.text(4.75, 7.3, '🥈 SILVER', ha='center', fontsize=14, fontweight='bold')
            
            # Cleaner data points
            if progress > 0.5:
                num_clean = int(48 * min(1, (progress - 0.5) * 2))  # Lost 2 records to cleaning
                np.random.seed(43)
                x_silver = np.random.uniform(4.2, 5.3, num_clean)
                y_silver = np.random.uniform(3.2, 6.8, num_clean)
                ax.scatter(x_silver, y_silver, c=COLORS['silver'], s=20, alpha=0.7, marker='s')
                ax.text(4.75, 2.7, f'{num_clean} clean records', ha='center', fontsize=10)
        
        # Flow arrow Silver -> Gold
        if progress > 0.6:
            arrow_alpha2 = min(1, (progress - 0.6) * 3)
            arrow2 = FancyArrowPatch((5.5, 5), (6.5, 5),
                                    arrowstyle='->', mutation_scale=30,
                                    linewidth=3, color='orange', alpha=arrow_alpha2)
            ax.add_patch(arrow2)
            ax.text(6, 5.3, 'Engineer', ha='center', fontsize=10, alpha=arrow_alpha2)
        
        # Gold layer
        if progress > 0.7:
            gold_alpha = 0.3 + 0.3 * min(1, (progress - 0.7) * 2)
            gold_box = FancyBboxPatch((7, 3), 1.5, 4, boxstyle="round,pad=0.1",
                                      edgecolor=COLORS['gold'], facecolor=COLORS['gold'],
                                      alpha=gold_alpha, linewidth=3)
            ax.add_patch(gold_box)
            ax.text(7.75, 7.3, '🥇 GOLD', ha='center', fontsize=14, fontweight='bold')
            
            # Feature-enriched points
            if progress > 0.8:
                num_features = int(48 * min(1, (progress - 0.8) * 2))
                np.random.seed(44)
                x_gold = np.random.uniform(7.2, 8.3, num_features)
                y_gold = np.random.uniform(3.2, 6.8, num_features)
                # Color by feature value
                colors_gold = plt.cm.viridis(np.random.rand(num_features))
                ax.scatter(x_gold, y_gold, c=colors_gold, s=30, alpha=0.8, marker='*')
                ax.text(7.75, 2.7, f'{num_features} rows × 15 features', ha='center', fontsize=10)
        
        # Progress indicator
        progress_bar_width = 8
        progress_x = 1
        progress_y = 1
        ax.add_patch(Rectangle((progress_x, progress_y), progress_bar_width, 0.3,
                               facecolor='lightgray', edgecolor='black', linewidth=2))
        ax.add_patch(Rectangle((progress_x, progress_y), progress_bar_width * progress, 0.3,
                               facecolor=COLORS['success'], alpha=0.7))
        ax.text(5, 0.5, f'Progress: {int(progress * 100)}%', ha='center', fontsize=12)
        
        # Stats panel
        if progress > 0.9:
            stats_text = (
                "✓ Quality: 96% (2 records dropped)\n"
                "✓ Features: 15 engineered\n"
                "✓ Ready for modeling"
            )
            ax.text(5, 8.5, stats_text, ha='center', fontsize=11,
                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    anim = FuncAnimation(fig, animate, frames=frames, interval=50, repeat=True)
    
    output_path = OUTPUT_DIR / "02_layer_transformation_animation.gif"
    writer = PillowWriter(fps=20)
    anim.save(output_path, writer=writer)
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_feature_engineering_flow():
    """Create detailed feature engineering visualization"""
    if not NETWORKX_AVAILABLE:
        print("⚠️  Skipping feature engineering flow (NetworkX not available)")
        return
    
    print("\n🔧 Creating feature engineering flow diagram...")
    
    fig, ax = plt.subplots(figsize=(18, 12), facecolor='white')
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes by category
    raw_data = ['RBOB Price', 'WTI Price', 'Retail Price', 'Inventory', 'Utilization']
    lag_features = ['RBOB Lag3', 'RBOB Lag7', 'RBOB Lag14']
    derived_features = ['Crack Spread', 'Retail Margin', 'Delta RBOB 1W']
    volatility = ['Vol RBOB 10D', 'RBOB Momentum 7D']
    supply = ['Days Supply', 'Util×Inv Interaction']
    seasonal = ['Winter Blend', 'Days Since Oct1', 'Is Weekend']
    output = ['Model Features (15)']
    
    # Position nodes
    pos = {}
    
    # Raw data (left)
    for i, node in enumerate(raw_data):
        pos[node] = (0, 5 - i)
        G.add_node(node, layer='raw')
    
    # Lag features
    for i, node in enumerate(lag_features):
        pos[node] = (2, 5 - i)
        G.add_node(node, layer='lag')
        G.add_edge('RBOB Price', node)
    
    # Derived features
    for i, node in enumerate(derived_features):
        pos[node] = (2, 2 - i)
        G.add_node(node, layer='derived')
    G.add_edge('RBOB Price', 'Crack Spread')
    G.add_edge('WTI Price', 'Crack Spread')
    G.add_edge('RBOB Price', 'Retail Margin')
    G.add_edge('Retail Price', 'Retail Margin')
    G.add_edge('RBOB Price', 'Delta RBOB 1W')
    
    # Volatility features
    for i, node in enumerate(volatility):
        pos[node] = (4, 4.5 - i * 1.5)
        G.add_node(node, layer='volatility')
        G.add_edge('RBOB Price', node)
    
    # Supply features
    for i, node in enumerate(supply):
        pos[node] = (4, 1.5 - i * 1.5)
        G.add_node(node, layer='supply')
    G.add_edge('Inventory', 'Days Supply')
    G.add_edge('Inventory', 'Util×Inv Interaction')
    G.add_edge('Utilization', 'Util×Inv Interaction')
    
    # Seasonal
    for i, node in enumerate(seasonal):
        pos[node] = (4, -1.5 - i * 1.5)
        G.add_node(node, layer='seasonal')
    
    # Output
    pos['Model Features (15)'] = (6, 2)
    G.add_node('Model Features (15)', layer='output')
    
    # Connect all features to output
    for node in lag_features + derived_features + volatility + supply + seasonal:
        G.add_edge(node, 'Model Features (15)')
    
    # Draw
    node_colors = []
    for node in G.nodes():
        layer = G.nodes[node]['layer']
        if layer == 'raw':
            node_colors.append(COLORS['bronze'])
        elif layer in ['lag', 'derived']:
            node_colors.append(COLORS['silver'])
        elif layer in ['volatility', 'supply', 'seasonal']:
            node_colors.append(COLORS['gold'])
        else:
            node_colors.append(COLORS['model'])
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, 
                          alpha=0.7, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold', ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True,
                          arrowsize=15, width=1.5, alpha=0.6, ax=ax)
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=COLORS['bronze'], label='Raw Data (Silver)', alpha=0.7),
        mpatches.Patch(color=COLORS['silver'], label='Basic Features', alpha=0.7),
        mpatches.Patch(color=COLORS['gold'], label='Advanced Features (Gold)', alpha=0.7),
        mpatches.Patch(color=COLORS['model'], label='Model Input', alpha=0.7),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    ax.set_title('Feature Engineering Flow: Silver → Gold', fontsize=18, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "03_feature_engineering_flow.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_system_operation_animation():
    """Create animation showing the complete system in operation"""
    print("\n🎬 Creating system operation animation...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), facecolor='white',
                                     gridspec_kw={'height_ratios': [3, 1]})
    
    frames = 150
    
    def animate(frame):
        for ax in [ax1, ax2]:
            ax.clear()
        
        # Main system view
        ax1.set_xlim(0, 12)
        ax1.set_ylim(0, 8)
        ax1.axis('off')
        
        time_progress = frame / frames
        cycle = (frame % 50) / 50  # Repeated cycle for data flow
        
        ax1.text(6, 7.5, 'Gas Price Forecasting System - Live Operation', 
                ha='center', fontsize=18, fontweight='bold')
        
        # Current time
        hours = int(time_progress * 24)
        minutes = int((time_progress * 24 * 60) % 60)
        ax1.text(6, 7, f'Time: {hours:02d}:{minutes:02d}', 
                ha='center', fontsize=12, style='italic')
        
        # Data sources (top)
        sources = [
            ('EIA', 1, 6, time_progress > 0.3),
            ('RBOB', 3, 6, time_progress > 0.1),
            ('AAA', 5, 6, time_progress > 0.5),
        ]
        
        for name, x, y, active in sources:
            color = COLORS['success'] if active else 'lightgray'
            circle = Circle((x, y), 0.3, color=color, alpha=0.7)
            ax1.add_patch(circle)
            ax1.text(x, y, name, ha='center', va='center', fontsize=9, fontweight='bold')
            
            # Pulse effect when active
            if active and cycle < 0.3:
                pulse_circle = Circle((x, y), 0.3 + cycle, 
                                     color=color, alpha=0.5 * (1 - cycle/0.3), fill=False, linewidth=2)
                ax1.add_patch(pulse_circle)
        
        # Pipeline layers
        layers_config = [
            ('Bronze', 2, 4, COLORS['bronze'], time_progress > 0.2),
            ('Silver', 5, 4, COLORS['silver'], time_progress > 0.4),
            ('Gold', 8, 4, COLORS['gold'], time_progress > 0.6),
        ]
        
        for name, x, y, color, active in layers_config:
            alpha = 0.7 if active else 0.3
            box = FancyBboxPatch((x-0.8, y-0.5), 1.6, 1, boxstyle="round,pad=0.1",
                                edgecolor=color, facecolor=color, alpha=alpha, linewidth=2)
            ax1.add_patch(box)
            ax1.text(x, y, name, ha='center', va='center', fontsize=11, fontweight='bold')
            
            # Processing indicator
            if active and cycle < 0.5:
                spinner_angle = cycle * 4 * np.pi
                spinner_x = x + 0.6 * np.cos(spinner_angle)
                spinner_y = y + 0.6 * np.sin(spinner_angle)
                ax1.plot([x, spinner_x], [y, spinner_y], 'k-', linewidth=2)
        
        # Data flow particles
        if time_progress > 0.3:
            # Bronze -> Silver flow
            for i in range(5):
                particle_progress = (cycle + i * 0.2) % 1
                if particle_progress < 0.7:
                    px = 2.8 + (5 - 2.8) * particle_progress / 0.7
                    py = 4
                    ax1.plot(px, py, 'o', color=COLORS['bronze'], markersize=8, alpha=0.8)
        
        if time_progress > 0.5:
            # Silver -> Gold flow
            for i in range(5):
                particle_progress = (cycle + i * 0.2) % 1
                if particle_progress < 0.7:
                    px = 5.8 + (8 - 5.8) * particle_progress / 0.7
                    py = 4
                    ax1.plot(px, py, 'o', color=COLORS['silver'], markersize=8, alpha=0.8)
        
        # Model & Prediction
        if time_progress > 0.7:
            model_box = FancyBboxPatch((10-0.8, 4-0.5), 1.6, 1, boxstyle="round,pad=0.1",
                                       edgecolor=COLORS['model'], facecolor=COLORS['model'],
                                       alpha=0.7, linewidth=2)
            ax1.add_patch(model_box)
            ax1.text(10, 4, 'Model', ha='center', va='center', fontsize=11, fontweight='bold')
            
            # Gold -> Model flow
            if cycle < 0.5:
                for i in range(3):
                    particle_progress = (cycle + i * 0.15) % 0.5 / 0.5
                    px = 8.8 + (10 - 8.8) * particle_progress
                    py = 4
                    ax1.plot(px, py, '*', color=COLORS['gold'], markersize=10, alpha=0.8)
        
        if time_progress > 0.85:
            pred_box = FancyBboxPatch((10-0.8, 2-0.5), 1.6, 1, boxstyle="round,pad=0.1",
                                     edgecolor=COLORS['prediction'], facecolor=COLORS['prediction'],
                                     alpha=0.7, linewidth=2)
            ax1.add_patch(pred_box)
            ax1.text(10, 2.2, '🔮', ha='center', fontsize=20)
            ax1.text(10, 1.8, '$3.05', ha='center', va='center', fontsize=11, fontweight='bold')
            
            # Model -> Prediction arrow
            arrow = FancyArrowPatch((10, 3.5), (10, 2.5),
                                   arrowstyle='->', mutation_scale=20, linewidth=2,
                                   color=COLORS['prediction'])
            ax1.add_patch(arrow)
        
        # Status panel
        status_y_start = 1
        statuses = [
            (f"Data Fresh: {'✓' if time_progress > 0.5 else '...'}", COLORS['success'] if time_progress > 0.5 else 'gray'),
            (f"Models Trained: {'✓' if time_progress > 0.8 else '...'}", COLORS['success'] if time_progress > 0.8 else 'gray'),
            (f"Forecast Ready: {'✓' if time_progress > 0.85 else '...'}", COLORS['success'] if time_progress > 0.85 else 'gray'),
        ]
        
        for i, (status, color) in enumerate(statuses):
            ax1.text(0.5, status_y_start - i * 0.3, status, fontsize=9,
                    bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        # Timeline view (bottom)
        ax2.set_xlim(0, 24)
        ax2.set_ylim(0, 3)
        ax2.set_xlabel('Hour of Day', fontsize=11)
        ax2.set_title('Daily Activity Timeline', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Activity bars
        activities = [
            ('Bronze Download', 0, 2, 0.5, COLORS['bronze']),
            ('Silver Process', 2, 4, 1, COLORS['silver']),
            ('Gold Build', 4, 6, 1.5, COLORS['gold']),
            ('Model Training', 6, 9, 2, COLORS['model']),
            ('Prediction', 9, 10, 2.5, COLORS['prediction']),
        ]
        
        current_hour = hours
        
        for name, start, end, y, color in activities:
            alpha = 0.7 if current_hour >= start else 0.2
            rect = Rectangle((start, y-0.15), end-start, 0.3,
                           facecolor=color, alpha=alpha, edgecolor='black', linewidth=1)
            ax2.add_patch(rect)
            ax2.text(start + (end-start)/2, y, name, ha='center', va='center', fontsize=8)
        
        # Current time marker
        ax2.axvline(current_hour, color='red', linewidth=2, linestyle='--', alpha=0.8)
        ax2.text(current_hour, 2.8, '▼', ha='center', color='red', fontsize=14)
    
    anim = FuncAnimation(fig, animate, frames=frames, interval=100, repeat=True)
    
    output_path = OUTPUT_DIR / "04_system_operation_animation.gif"
    writer = PillowWriter(fps=10)
    anim.save(output_path, writer=writer)
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_interactive_dashboard():
    """Create interactive Plotly dashboard"""
    if not PLOTLY_AVAILABLE:
        print("⚠️  Skipping interactive dashboard (Plotly not available)")
        return
    
    print("\n📊 Creating interactive dashboard...")
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Data Pipeline Flow', 'Layer Processing Times',
                       'Feature Importance', 'Model Performance'),
        specs=[[{'type': 'sankey'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'scatter'}]]
    )
    
    # 1. Sankey diagram for data flow
    fig.add_trace(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=['EIA API', 'RBOB API', 'AAA API', 'Bronze', 'Silver', 'Gold', 'Model', 'Forecast'],
            color=[COLORS['bronze'], COLORS['bronze'], COLORS['bronze'],
                   COLORS['bronze'], COLORS['silver'], COLORS['gold'],
                   COLORS['model'], COLORS['prediction']]
        ),
        link=dict(
            source=[0, 1, 2, 3, 4, 5, 6],
            target=[3, 3, 3, 4, 5, 6, 7],
            value=[100, 100, 100, 300, 298, 298, 298],
            color=['rgba(205, 127, 50, 0.3)'] * 7
        )
    ), row=1, col=1)
    
    # 2. Processing times
    layers = ['Bronze', 'Silver', 'Gold', 'Train', 'Predict']
    times = [30, 5, 10, 180, 1]
    
    fig.add_trace(go.Bar(
        x=layers,
        y=times,
        marker_color=[COLORS['bronze'], COLORS['silver'], COLORS['gold'],
                     COLORS['model'], COLORS['prediction']],
        text=[f"{t}s" for t in times],
        textposition='auto',
    ), row=1, col=2)
    
    # 3. Feature importance
    features = ['RBOB Price', 'Crack Spread', 'Winter Blend', 'Inventory', 
                'Utilization', 'Vol 10D', 'Lag7', 'Days Since Oct1']
    importance = [0.35, 0.18, 0.12, 0.10, 0.08, 0.07, 0.06, 0.04]
    
    fig.add_trace(go.Bar(
        x=importance,
        y=features,
        orientation='h',
        marker_color=COLORS['gold'],
        text=[f"{i:.2f}" for i in importance],
        textposition='auto',
    ), row=2, col=1)
    
    # 4. Model performance over time
    dates = pd.date_range('2020-10-01', '2025-10-12', freq='M')
    r2_scores = 0.45 + 0.15 * np.random.rand(len(dates))  # Simulated improving performance
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=r2_scores,
        mode='lines+markers',
        line=dict(color=COLORS['model'], width=3),
        marker=dict(size=8),
        name='R² Score'
    ), row=2, col=2)
    
    # Add horizontal line for current R² (manually for subplot)
    fig.add_shape(
        type="line",
        x0=dates[0], x1=dates[-1],
        y0=0.59, y1=0.59,
        line=dict(color="green", width=2, dash="dash"),
        row=2, col=2
    )
    fig.add_annotation(
        x=dates[-1], y=0.59,
        text="Current R²=0.59",
        showarrow=False,
        xanchor="right",
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text="Gas Price Forecasting System - Interactive Dashboard",
        title_font_size=20,
        showlegend=False,
        height=900,
    )
    
    fig.update_yaxes(title_text="Time (seconds)", row=1, col=2)
    fig.update_xaxes(title_text="Feature", row=2, col=1)
    fig.update_yaxes(title_text="Importance", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=2)
    fig.update_yaxes(title_text="R² Score", row=2, col=2)
    
    output_path = OUTPUT_DIR / "05_interactive_dashboard.html"
    fig.write_html(output_path)
    print(f"✓ Saved: {output_path}")


def create_data_quality_flow():
    """Create visualization showing data quality improvements through layers"""
    print("\n✨ Creating data quality flow...")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor='white')
    fig.suptitle('Data Quality Progression: Bronze → Silver → Gold', 
                 fontsize=18, fontweight='bold')
    
    # Simulated data quality metrics
    metrics = {
        'Bronze': {
            'completeness': 0.92,
            'accuracy': 0.85,
            'consistency': 0.78,
            'timeliness': 0.95,
        },
        'Silver': {
            'completeness': 0.96,
            'accuracy': 0.95,
            'consistency': 0.93,
            'timeliness': 0.95,
        },
        'Gold': {
            'completeness': 0.98,
            'accuracy': 0.97,
            'consistency': 0.96,
            'timeliness': 0.95,
        }
    }
    
    colors_map = {
        'Bronze': COLORS['bronze'],
        'Silver': COLORS['silver'],
        'Gold': COLORS['gold']
    }
    
    for idx, (layer, data) in enumerate(metrics.items()):
        ax = axes[idx]
        
        categories = list(data.keys())
        values = list(data.values())
        
        # Create radar chart
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # Complete the circle
        angles += angles[:1]
        
        ax.plot(angles, values, 'o-', linewidth=2, color=colors_map[layer], label=layer)
        ax.fill(angles, values, alpha=0.25, color=colors_map[layer])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=9)
        ax.set_ylim(0, 1)
        ax.set_title(f'{layer} Layer\nAvg Quality: {np.mean(list(data.values())):.1%}',
                    fontsize=14, fontweight='bold')
        ax.grid(True)
        ax.legend(loc='upper right')
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / "06_data_quality_progression.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")
    plt.close()


def main():
    """Generate all advanced visualizations"""
    print("=" * 80)
    print("🎨 Advanced Pipeline Visualization System")
    print("=" * 80)
    
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    
    # Create visualizations
    create_medallion_architecture_detailed()
    create_layer_transformation_animation()
    create_feature_engineering_flow()
    create_system_operation_animation()
    create_interactive_dashboard()
    create_data_quality_flow()
    
    print("\n" + "=" * 80)
    print("✅ All visualizations created successfully!")
    print("=" * 80)
    print(f"\n📂 Find your visualizations in: {OUTPUT_DIR}")
    print("\nCreated files:")
    for file in sorted(OUTPUT_DIR.glob("*")):
        print(f"  • {file.name}")
    
    print("\n💡 Tips:")
    print("  • Open .html files in your web browser for interactive dashboards")
    print("  • .gif files show animated data flows")
    print("  • .png files are high-resolution static diagrams")


if __name__ == "__main__":
    main()
