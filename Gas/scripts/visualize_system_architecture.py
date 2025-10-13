"""
System Architecture Visualizer

Creates comprehensive diagrams showing:
1. Data flow through medallion architecture
2. Feature engineering pipeline
3. Model training workflow
4. Complete system overview
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path


def create_medallion_architecture_diagram(output_path: Path):
    """Visualize the Bronze → Silver → Gold data pipeline."""
    
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'Medallion Architecture: Data Flow Pipeline', 
            fontsize=20, fontweight='bold', ha='center')
    
    # Color scheme
    bronze_color = '#CD7F32'
    silver_color = '#C0C0C0'
    gold_color = '#FFD700'
    
    # ===== BRONZE LAYER =====
    bronze_y = 7.5
    ax.add_patch(FancyBboxPatch((0.5, bronze_y-0.8), 2.5, 1.6, 
                                boxstyle="round,pad=0.1", 
                                facecolor=bronze_color, edgecolor='black', linewidth=2, alpha=0.3))
    ax.text(1.75, bronze_y+0.5, 'BRONZE LAYER', fontsize=14, fontweight='bold', ha='center')
    ax.text(1.75, bronze_y+0.1, 'Raw Data Ingestion', fontsize=10, ha='center', style='italic')
    
    # Bronze sources
    bronze_sources = [
        ('EIA API', 'Weekly inventory\nUtilization %\nImports'),
        ('CME', 'RBOB futures\nWTI crude'),
        ('EIA Retail', 'Weekly retail\ngas prices')
    ]
    
    for i, (source, desc) in enumerate(bronze_sources):
        y_pos = bronze_y - 0.3 - i*0.35
        ax.add_patch(FancyBboxPatch((0.6, y_pos-0.15), 0.5, 0.25, 
                                    boxstyle="round,pad=0.02", 
                                    facecolor='white', edgecolor=bronze_color, linewidth=1.5))
        ax.text(0.85, y_pos, source, fontsize=8, ha='center', va='center', fontweight='bold')
        ax.text(2.2, y_pos, desc, fontsize=7, ha='left', va='center')
    
    # ===== SILVER LAYER =====
    silver_y = 7.5
    ax.add_patch(FancyBboxPatch((3.5, silver_y-0.8), 2.5, 1.6, 
                                boxstyle="round,pad=0.1", 
                                facecolor=silver_color, edgecolor='black', linewidth=2, alpha=0.3))
    ax.text(4.75, silver_y+0.5, 'SILVER LAYER', fontsize=14, fontweight='bold', ha='center')
    ax.text(4.75, silver_y+0.1, 'Cleaned & Validated', fontsize=10, ha='center', style='italic')
    
    # Silver processing steps
    silver_steps = [
        'Date parsing',
        'Missing value handling',
        'Schema validation',
        'Daily interpolation'
    ]
    
    for i, step in enumerate(silver_steps):
        y_pos = silver_y - 0.3 - i*0.35
        ax.add_patch(FancyBboxPatch((3.6, y_pos-0.12), 0.8, 0.2, 
                                    boxstyle="round,pad=0.02", 
                                    facecolor='white', edgecolor=silver_color, linewidth=1.5))
        ax.text(4.0, y_pos, step, fontsize=7, ha='center', va='center')
    
    # ===== GOLD LAYER =====
    gold_y = 7.5
    ax.add_patch(FancyBboxPatch((6.5, gold_y-0.8), 2.5, 1.6, 
                                boxstyle="round,pad=0.1", 
                                facecolor=gold_color, edgecolor='black', linewidth=2, alpha=0.3))
    ax.text(7.75, gold_y+0.5, 'GOLD LAYER', fontsize=14, fontweight='bold', ha='center')
    ax.text(7.75, gold_y+0.1, 'Model-Ready Features', fontsize=10, ha='center', style='italic')
    
    # Gold features
    gold_features = [
        '22 engineered features',
        'Lagged variables',
        'Temporal encodings',
        'Interaction terms'
    ]
    
    for i, feature in enumerate(gold_features):
        y_pos = gold_y - 0.3 - i*0.35
        ax.add_patch(FancyBboxPatch((6.6, y_pos-0.12), 0.9, 0.2, 
                                    boxstyle="round,pad=0.02", 
                                    facecolor='white', edgecolor=gold_color, linewidth=1.5))
        ax.text(7.05, y_pos, feature, fontsize=7, ha='center', va='center')
    
    # Arrows between layers
    arrow_props = dict(arrowstyle='->', lw=3, color='black')
    ax.annotate('', xy=(3.5, bronze_y), xytext=(3.0, bronze_y), arrowprops=arrow_props)
    ax.annotate('', xy=(6.5, silver_y), xytext=(6.0, silver_y), arrowprops=arrow_props)
    
    # ===== DOWNSTREAM USAGE =====
    downstream_y = 4.5
    ax.text(5, downstream_y+0.8, 'Downstream Applications', 
            fontsize=14, fontweight='bold', ha='center')
    
    # Model boxes
    models = [
        ('Ridge\nRegression', 2, downstream_y),
        ('Quantile\nRegression', 4, downstream_y),
        ('Walk-Forward\nValidation', 6, downstream_y),
        ('SHAP\nAnalysis', 8, downstream_y)
    ]
    
    for name, x, y in models:
        ax.add_patch(FancyBboxPatch((x-0.5, y-0.3), 1, 0.6, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor='#E8F4F8', edgecolor='#2E86AB', linewidth=2))
        ax.text(x, y, name, fontsize=9, ha='center', va='center', fontweight='bold')
        
        # Arrow from gold to model
        ax.annotate('', xy=(x, y+0.3), xytext=(7.75, gold_y-0.9), 
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='gray', alpha=0.6))
    
    # ===== DATA QUALITY METRICS =====
    metrics_y = 2.5
    ax.text(5, metrics_y+0.5, 'Data Quality & Validation', 
            fontsize=12, fontweight='bold', ha='center')
    
    metrics = [
        ('1,824 rows', 'Daily 2020-2025'),
        ('22 features', 'Gold layer'),
        ('0 missing', 'Post-processing'),
        ('163 Oct rows', 'Training data')
    ]
    
    for i, (value, label) in enumerate(metrics):
        x_pos = 2 + i*1.8
        ax.add_patch(FancyBboxPatch((x_pos-0.4, metrics_y-0.25), 0.8, 0.5, 
                                    boxstyle="round,pad=0.03", 
                                    facecolor='#D5F4E6', edgecolor='#27AE60', linewidth=1.5))
        ax.text(x_pos, metrics_y+0.05, value, fontsize=10, ha='center', va='center', fontweight='bold')
        ax.text(x_pos, metrics_y-0.12, label, fontsize=7, ha='center', va='center')
    
    # ===== FOOTER INFO =====
    footer_text = (
        "Pipeline Flow: API → Bronze (raw) → Silver (cleaned) → Gold (engineered) → Models\n"
        "Automation: Scheduled daily updates | Validation: 4-layer quality checks | Storage: Parquet format"
    )
    ax.text(5, 0.5, footer_text, fontsize=8, ha='center', va='center', 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved medallion architecture diagram to {output_path}")


def create_feature_engineering_flowchart(output_path: Path):
    """Visualize the feature engineering process."""
    
    fig, ax = plt.subplots(figsize=(14, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Title
    ax.text(5, 11.5, 'Feature Engineering Pipeline', 
            fontsize=20, fontweight='bold', ha='center')
    ax.text(5, 11, '22 Features Across 6 Categories', 
            fontsize=12, ha='center', style='italic', color='gray')
    
    # Feature categories with details
    categories = [
        {
            'name': 'Price Features (8)',
            'y': 9.5,
            'color': '#3498DB',
            'features': [
                'price_rbob (RBOB futures)',
                'price_wti (WTI crude)',
                'crack_spread (RBOB - WTI)',
                'retail_margin (Retail - RBOB)',
                'rbob_lag3, rbob_lag7, rbob_lag14',
                'delta_rbob_1w (weekly change)'
            ]
        },
        {
            'name': 'Supply Features (4)',
            'y': 7.5,
            'color': '#E74C3C',
            'features': [
                'inventory_mbbl (million barrels)',
                'utilization_pct (refinery capacity)',
                'days_supply (inventory / demand)',
                'net_imports_kbd (1000 bbl/day)'
            ]
        },
        {
            'name': 'Momentum Features (3)',
            'y': 5.5,
            'color': '#9B59B6',
            'features': [
                'rbob_return_1d (daily % change)',
                'vol_rbob_10d (10-day volatility)',
                'rbob_momentum_7d (7-day trend)'
            ]
        },
        {
            'name': 'Interaction Terms (2)',
            'y': 4,
            'color': '#F39C12',
            'features': [
                'util_inv_interaction (capacity × inventory)',
                'copula_supply_stress (joint tail risk)'
            ]
        },
        {
            'name': 'Temporal Features (3)',
            'y': 2.5,
            'color': '#1ABC9C',
            'features': [
                'weekday (0-6, Monday=0)',
                'is_weekend (binary indicator)',
                'winter_blend_effect (seasonal premium)'
            ]
        },
        {
            'name': 'Target Variable (2)',
            'y': 1,
            'color': '#34495E',
            'features': [
                'days_since_oct1 (days into October)',
                'target (H-day ahead retail price)'
            ]
        }
    ]
    
    for cat in categories:
        # Category box
        ax.add_patch(FancyBboxPatch((1, cat['y']-0.6), 8, 1.2, 
                                    boxstyle="round,pad=0.1", 
                                    facecolor=cat['color'], edgecolor='black', 
                                    linewidth=2, alpha=0.2))
        
        # Category title
        ax.text(5, cat['y']+0.4, cat['name'], 
                fontsize=13, fontweight='bold', ha='center', color=cat['color'])
        
        # Features list
        features_text = '\n'.join([f"• {f}" for f in cat['features']])
        ax.text(5, cat['y']-0.15, features_text, 
                fontsize=8, ha='center', va='center', family='monospace')
    
    # Processing steps annotations
    processing_steps = [
        (0.5, 10, 'Source:\nRBOB\nfutures'),
        (0.5, 8, 'Source:\nEIA\nweekly'),
        (0.5, 6, 'Computed:\nRolling\nwindows'),
        (0.5, 4.5, 'Advanced:\nCopula\nmodeling'),
        (0.5, 2.8, 'Calendar:\nDate\nfeatures'),
        (0.5, 1.3, 'Output:\nModel\nready')
    ]
    
    for x, y, text in processing_steps:
        ax.add_patch(mpatches.Circle((x, y), 0.25, facecolor='#ECF0F1', 
                                    edgecolor='#7F8C8D', linewidth=1.5))
        ax.text(x, y, text, fontsize=6, ha='center', va='center', 
                fontweight='bold', color='#2C3E50')
    
    # Academic foundations sidebar
    ax.add_patch(FancyBboxPatch((9.2, 2), 0.7, 8, boxstyle="round,pad=0.05",
                                facecolor='#FFF9E6', edgecolor='#F39C12', linewidth=2))
    ax.text(9.55, 9.8, 'Literature', fontsize=9, ha='center', fontweight='bold', rotation=90)
    ax.text(9.55, 9, 'Founded', fontsize=8, ha='center', rotation=90, style='italic')
    
    papers = ['Borenstein\n2002', 'Kilian\n2014', 'Hamilton\n2009', 
              'Patton\n2006', 'Bacon\n1991']
    for i, paper in enumerate(papers):
        y_pos = 8.5 - i*1.5
        ax.text(9.55, y_pos, paper, fontsize=6, ha='center', rotation=90, 
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved feature engineering flowchart to {output_path}")


def create_model_training_workflow(output_path: Path):
    """Visualize the model training and validation workflow."""
    
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'Model Training & Validation Workflow', 
            fontsize=20, fontweight='bold', ha='center')
    
    # ===== DATA PREPARATION =====
    prep_y = 8.5
    ax.add_patch(FancyBboxPatch((1, prep_y-0.4), 8, 0.8, 
                                boxstyle="round,pad=0.1", 
                                facecolor='#E8F8F5', edgecolor='#27AE60', linewidth=2))
    ax.text(5, prep_y+0.2, 'Data Preparation', fontsize=12, fontweight='bold', ha='center')
    ax.text(5, prep_y-0.1, 'Train/Test Split: Oct 1, 2024 | Train: 1,447 rows | Test: 377 rows', 
            fontsize=9, ha='center')
    
    # ===== THREE MODEL TRACKS =====
    track_y = 7
    track_height = 4.5
    
    tracks = [
        {
            'name': 'Ridge Regression',
            'x': 1.5,
            'color': '#3498DB',
            'steps': [
                ('Time-Series CV', '5-fold expanding window'),
                ('Alpha Selection', 'Test [0.01, 0.1, 1, 10, 100]'),
                ('Train Full Model', 'Best α = 0.01'),
                ('Performance', 'R² = 0.9999, RMSE = 0.0002')
            ]
        },
        {
            'name': 'Walk-Forward Valid.',
            'x': 4.5,
            'color': '#E74C3C',
            'steps': [
                ('5 Horizons', '1, 3, 7, 14, 21 days'),
                ('4 Years', '2021-2024 Octobers'),
                ('20 Tests Total', 'Per horizon/year combo'),
                ('Best: 1-day', 'R² = 82%, RMSE = $0.025')
            ]
        },
        {
            'name': 'Quantile Regression',
            'x': 7.5,
            'color': '#9B59B6',
            'steps': [
                ('3 Quantiles', 'P10, P50, P90'),
                ('Prediction Intervals', 'Uncertainty quantification'),
                ('Pinball Loss', 'Quantile-specific metric'),
                ('Coverage', 'Perfect calibration')
            ]
        }
    ]
    
    for track in tracks:
        # Track container
        ax.add_patch(FancyBboxPatch((track['x']-0.7, 2.5), 1.4, track_height, 
                                    boxstyle="round,pad=0.1", 
                                    facecolor=track['color'], edgecolor='black', 
                                    linewidth=2, alpha=0.15))
        
        # Track title
        ax.text(track['x'], track_y+0.2, track['name'], 
                fontsize=11, fontweight='bold', ha='center', color=track['color'])
        
        # Processing steps
        for i, (step, detail) in enumerate(track['steps']):
            y_pos = track_y - 0.5 - i*1.0
            
            # Step box
            ax.add_patch(FancyBboxPatch((track['x']-0.6, y_pos-0.35), 1.2, 0.7, 
                                        boxstyle="round,pad=0.05", 
                                        facecolor='white', edgecolor=track['color'], 
                                        linewidth=1.5))
            
            # Step number
            ax.add_patch(mpatches.Circle((track['x']-0.5, y_pos+0.2), 0.12, 
                                        facecolor=track['color'], edgecolor='white', linewidth=1))
            ax.text(track['x']-0.5, y_pos+0.2, str(i+1), 
                   fontsize=8, ha='center', va='center', color='white', fontweight='bold')
            
            # Step text
            ax.text(track['x'], y_pos+0.15, step, 
                   fontsize=9, ha='center', va='center', fontweight='bold')
            ax.text(track['x'], y_pos-0.1, detail, 
                   fontsize=7, ha='center', va='center', style='italic')
    
    # Arrow from prep to tracks
    for track in tracks:
        ax.annotate('', xy=(track['x'], track_y+0.4), xytext=(track['x'], prep_y-0.5), 
                   arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
    
    # ===== OUTPUT & EVALUATION =====
    output_y = 1.2
    ax.add_patch(FancyBboxPatch((1, output_y-0.5), 8, 1, 
                                boxstyle="round,pad=0.1", 
                                facecolor='#FFF9E6', edgecolor='#F39C12', linewidth=2))
    ax.text(5, output_y+0.25, 'Output & Artifacts', fontsize=12, fontweight='bold', ha='center')
    
    outputs = [
        '3 trained models (PKL)',
        'Metrics CSV/JSON',
        '7 walk-forward plots',
        '6 quantile plots',
        'Feature importance',
        'Validation reports'
    ]
    
    output_text = '  •  '.join(outputs)
    ax.text(5, output_y-0.15, output_text, fontsize=8, ha='center')
    
    # Arrows to output
    for track in tracks:
        ax.annotate('', xy=(5, output_y+0.5), xytext=(track['x'], 2.5), 
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='gray', alpha=0.6))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved model training workflow to {output_path}")


def create_system_overview_diagram(output_path: Path):
    """Create a comprehensive system overview showing all components."""
    
    fig = plt.figure(figsize=(18, 12))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Main title
    ax.text(9, 11.5, 'Complete System Architecture', 
            fontsize=24, fontweight='bold', ha='center')
    ax.text(9, 11, 'Gasoline Price Forecasting Pipeline', 
            fontsize=14, ha='center', style='italic', color='gray')
    
    # ===== LAYER 1: DATA SOURCES =====
    layer1_y = 9.5
    ax.text(9, layer1_y+0.5, 'Layer 1: Data Sources', 
            fontsize=14, fontweight='bold', ha='center', color='#2C3E50')
    
    sources = [
        ('EIA API', 3, '#CD7F32', 'Inventory\nUtilization\nImports'),
        ('CME Futures', 9, '#CD7F32', 'RBOB\nWTI'),
        ('EIA Retail', 15, '#CD7F32', 'Weekly\nPrices')
    ]
    
    for name, x, color, details in sources:
        ax.add_patch(FancyBboxPatch((x-1, layer1_y-0.5), 2, 1, 
                                    boxstyle="round,pad=0.1", 
                                    facecolor=color, edgecolor='black', 
                                    linewidth=2, alpha=0.3))
        ax.text(x, layer1_y+0.2, name, fontsize=11, ha='center', fontweight='bold')
        ax.text(x, layer1_y-0.2, details, fontsize=8, ha='center')
    
    # ===== LAYER 2: MEDALLION ARCHITECTURE =====
    layer2_y = 7
    ax.text(9, layer2_y+0.8, 'Layer 2: Medallion Architecture', 
            fontsize=14, fontweight='bold', ha='center', color='#2C3E50')
    
    medallion = [
        ('Bronze', 3, '#CD7F32', 'Raw\nData'),
        ('Silver', 9, '#C0C0C0', 'Cleaned\n& Validated'),
        ('Gold', 15, '#FFD700', 'Model-Ready\n22 Features')
    ]
    
    for name, x, color, desc in medallion:
        ax.add_patch(FancyBboxPatch((x-1.2, layer2_y-0.5), 2.4, 1, 
                                    boxstyle="round,pad=0.1", 
                                    facecolor=color, edgecolor='black', 
                                    linewidth=2, alpha=0.4))
        ax.text(x, layer2_y+0.2, name, fontsize=12, ha='center', fontweight='bold')
        ax.text(x, layer2_y-0.2, desc, fontsize=9, ha='center')
        
        # Arrows between stages
        if x < 15:
            ax.annotate('', xy=(x+2.5, layer2_y), xytext=(x+1.3, layer2_y), 
                       arrowprops=dict(arrowstyle='->', lw=3, color='black'))
    
    # Arrows from sources to bronze
    for _, x, _, _ in sources:
        ax.annotate('', xy=(3, layer2_y+0.5), xytext=(x, layer1_y-0.5), 
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='gray', alpha=0.6))
    
    # ===== LAYER 3: FEATURE ENGINEERING =====
    layer3_y = 4.8
    ax.text(9, layer3_y+0.8, 'Layer 3: Feature Engineering', 
            fontsize=14, fontweight='bold', ha='center', color='#2C3E50')
    
    feature_groups = [
        ('Price\n(8)', 2, '#3498DB'),
        ('Supply\n(4)', 4.5, '#E74C3C'),
        ('Momentum\n(3)', 7, '#9B59B6'),
        ('Interactions\n(2)', 9.5, '#F39C12'),
        ('Temporal\n(3)', 12, '#1ABC9C'),
        ('Target\n(2)', 16, '#34495E')
    ]
    
    for name, x, color in feature_groups:
        ax.add_patch(FancyBboxPatch((x-0.6, layer3_y-0.4), 1.2, 0.8, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor=color, edgecolor='black', 
                                    linewidth=1.5, alpha=0.3))
        ax.text(x, layer3_y, name, fontsize=9, ha='center', va='center', fontweight='bold')
    
    # Arrow from gold to features
    ax.annotate('', xy=(9, layer3_y+0.5), xytext=(15, layer2_y-0.5), 
               arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # ===== LAYER 4: MODELING =====
    layer4_y = 2.8
    ax.text(9, layer4_y+0.6, 'Layer 4: Modeling & Validation', 
            fontsize=14, fontweight='bold', ha='center', color='#2C3E50')
    
    models = [
        ('Ridge\nRegression', 3, '#3498DB', 'R²=99.99%'),
        ('Quantile\nRegression', 7, '#9B59B6', 'P10/P50/P90'),
        ('Walk-Forward\nValidation', 11, '#E74C3C', '20 tests'),
        ('SHAP\nAnalysis', 15, '#27AE60', 'Interpretability')
    ]
    
    for name, x, color, metric in models:
        ax.add_patch(FancyBboxPatch((x-1, layer4_y-0.4), 2, 0.8, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor=color, edgecolor='black', 
                                    linewidth=2, alpha=0.3))
        ax.text(x, layer4_y+0.1, name, fontsize=9, ha='center', fontweight='bold')
        ax.text(x, layer4_y-0.2, metric, fontsize=7, ha='center', style='italic')
        
        # Arrow from features to model
        ax.annotate('', xy=(x, layer4_y+0.4), xytext=(9, layer3_y-0.5), 
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='gray', alpha=0.5))
    
    # ===== LAYER 5: OUTPUT =====
    layer5_y = 1
    ax.add_patch(FancyBboxPatch((3, layer5_y-0.4), 12, 0.8, 
                                boxstyle="round,pad=0.1", 
                                facecolor='#FFF9E6', edgecolor='#F39C12', linewidth=2))
    ax.text(9, layer5_y+0.2, 'Final Output & Artifacts', fontsize=12, fontweight='bold', ha='center')
    ax.text(9, layer5_y-0.15, '18 files: Models (PKL) • Metrics (CSV/JSON) • Visualizations (PNG) • Reports (TXT)', 
            fontsize=9, ha='center')
    
    # Arrows to output
    for _, x, _, _ in models:
        ax.annotate('', xy=(9, layer5_y+0.5), xytext=(x, layer4_y-0.5), 
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='gray', alpha=0.5))
    
    # ===== SIDE INFO PANEL =====
    ax.add_patch(FancyBboxPatch((0.3, 3), 1.5, 6, boxstyle="round,pad=0.1",
                                facecolor='#ECF0F1', edgecolor='#7F8C8D', linewidth=2))
    ax.text(1.05, 8.7, 'System Stats', fontsize=11, ha='center', fontweight='bold')
    
    stats = [
        ('Data Points', '1,824'),
        ('Features', '22'),
        ('Models', '3'),
        ('Validations', '20'),
        ('Time Span', '2020-2025'),
        ('Best R²', '99.99%'),
        ('Runtime', '~25 sec')
    ]
    
    for i, (label, value) in enumerate(stats):
        y_pos = 8.2 - i*0.8
        ax.text(0.6, y_pos, label, fontsize=8, ha='left', fontweight='bold')
        ax.text(1.5, y_pos, value, fontsize=8, ha='right', color='#E74C3C')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved system overview diagram to {output_path}")


def main():
    """Generate all architecture visualizations."""
    
    output_dir = Path(__file__).resolve().parents[1] / "outputs" / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("🎨 GENERATING SYSTEM ARCHITECTURE VISUALIZATIONS")
    print("="*70 + "\n")
    
    # Generate all diagrams
    create_medallion_architecture_diagram(output_dir / "01_medallion_architecture.png")
    create_feature_engineering_flowchart(output_dir / "02_feature_engineering.png")
    create_model_training_workflow(output_dir / "03_model_training_workflow.png")
    create_system_overview_diagram(output_dir / "04_system_overview.png")
    
    print("\n" + "="*70)
    print(f"✓ All visualizations saved to {output_dir}")
    print("="*70)
    print("\nGenerated files:")
    for f in sorted(output_dir.glob("*.png")):
        size_kb = f.stat().st_size / 1024
        print(f"  • {f.name:45s} {size_kb:>8.1f} KB")
    print()


if __name__ == "__main__":
    main()
