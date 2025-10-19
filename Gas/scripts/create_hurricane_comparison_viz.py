"""
Create before/after comparison visualization of hurricane feature enhancements.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "interpretability"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create comparison visualization
fig = plt.figure(figsize=(18, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Title
fig.suptitle('Hurricane Risk Modeling Enhancement: Before → After', 
             fontsize=20, fontweight='bold', y=0.98)

# Before (Original Implementation)
ax1 = fig.add_subplot(gs[0, 0])
ax1.text(0.5, 0.9, '❌ BEFORE', ha='center', va='top', fontsize=16, fontweight='bold', 
         transform=ax1.transAxes, color='#E74C3C')
ax1.text(0.5, 0.7, 'October Only', ha='center', va='top', fontsize=12, transform=ax1.transAxes)
ax1.text(0.5, 0.55, '2020-2021 (2 years)', ha='center', va='top', fontsize=12, transform=ax1.transAxes)
ax1.text(0.5, 0.4, '6 basic features', ha='center', va='top', fontsize=12, transform=ax1.transAxes)
ax1.text(0.5, 0.25, '2 hurricanes', ha='center', va='top', fontsize=12, transform=ax1.transAxes)
ax1.text(0.5, 0.1, 'No geographic data', ha='center', va='top', fontsize=12, 
         transform=ax1.transAxes, color='#E74C3C')
ax1.axis('off')

# Arrow
ax2 = fig.add_subplot(gs[0, 1])
ax2.annotate('', xy=(0.8, 0.5), xytext=(0.2, 0.5),
            arrowprops=dict(arrowstyle='->', lw=3, color='#2ECC71'),
            transform=ax2.transAxes)
ax2.text(0.5, 0.6, 'ENHANCED', ha='center', va='bottom', fontsize=14, 
         fontweight='bold', transform=ax2.transAxes, color='#2ECC71')
ax2.axis('off')

# After (Enhanced Implementation)
ax3 = fig.add_subplot(gs[0, 2])
ax3.text(0.5, 0.9, '✅ AFTER', ha='center', va='top', fontsize=16, fontweight='bold', 
         transform=ax3.transAxes, color='#2ECC71')
ax3.text(0.5, 0.7, 'Aug-Oct (Peak Season)', ha='center', va='top', fontsize=12, transform=ax3.transAxes)
ax3.text(0.5, 0.55, '2005-2025 (20 years)', ha='center', va='top', fontsize=12, transform=ax3.transAxes)
ax3.text(0.5, 0.4, '13 enhanced features', ha='center', va='top', fontsize=12, transform=ax3.transAxes)
ax3.text(0.5, 0.25, '10 major hurricanes', ha='center', va='top', fontsize=12, transform=ax3.transAxes)
ax3.text(0.5, 0.1, 'Geographic + Refinery modeling', ha='center', va='top', fontsize=12, 
         transform=ax3.transAxes, color='#2ECC71')
ax3.axis('off')

# Feature comparison
ax4 = fig.add_subplot(gs[1, :])
features_before = ['hurricane_risk_score', 'hurricane_probability', 'hurricane_intensity',
                   'is_hurricane_event', 'days_since_last_hurricane', 'hurricane_risk_7d_avg']
features_after = features_before + [
    'hurricane_category', 'distance_to_nearest_refinery_mi', 'refineries_at_risk_count',
    'padd3_threat_level', 'is_gulf_coast_landfall', 'padd3_threat_14d_max', 'days_until_next_hurricane'
]

y_pos_before = list(range(len(features_before)))
y_pos_after = list(range(len(features_after)))

ax4.barh(y_pos_before, [1]*len(features_before), color='#E74C3C', alpha=0.6, label='Before (6 features)')
ax4.barh([y + 0.3 for y in y_pos_after], [1.2]*len(features_after), color='#2ECC71', alpha=0.6, label='After (13 features)')

ax4.set_yticks(list(range(max(len(features_before), len(features_after)))))
ax4.set_yticklabels(features_after if len(features_after) > len(features_before) else features_before, fontsize=9)
ax4.set_xlabel('Feature Set Comparison', fontsize=12)
ax4.set_title('Feature Set Expansion', fontsize=14, fontweight='bold')
ax4.legend(loc='lower right')
ax4.set_xlim(0, 1.5)
ax4.invert_yaxis()

# Geographic specificity example
ax5 = fig.add_subplot(gs[2, 0])
ax5.text(0.5, 0.95, '🌀 Hurricane Ian (2022)', ha='center', va='top', fontsize=11, 
         fontweight='bold', transform=ax5.transAxes)
ax5.text(0.1, 0.75, '• Cat 4, $113B damage', ha='left', va='top', fontsize=9, transform=ax5.transAxes)
ax5.text(0.1, 0.60, '• 721 mi from refineries', ha='left', va='top', fontsize=9, transform=ax5.transAxes)
ax5.text(0.1, 0.45, '• Florida west coast', ha='left', va='top', fontsize=9, transform=ax5.transAxes)
ax5.text(0.1, 0.30, '• PADD 3 threat: 0.0/10', ha='left', va='top', fontsize=9, 
         transform=ax5.transAxes, color='#2ECC71', fontweight='bold')
ax5.text(0.1, 0.15, '• Gas impact: Minimal', ha='left', va='top', fontsize=9, 
         transform=ax5.transAxes, color='#2ECC71', fontweight='bold')
ax5.axis('off')
ax5.add_patch(mpatches.Rectangle((0.05, 0.05), 0.9, 0.9, 
              fill=False, edgecolor='#2ECC71', linewidth=2, transform=ax5.transAxes))

ax6 = fig.add_subplot(gs[2, 1])
ax6.text(0.5, 0.95, '🌀 Hurricane Laura (2020)', ha='center', va='top', fontsize=11, 
         fontweight='bold', transform=ax6.transAxes)
ax6.text(0.1, 0.75, '• Cat 4, <$20B damage', ha='left', va='top', fontsize=9, transform=ax6.transAxes)
ax6.text(0.1, 0.60, '• 28 mi from Lake Charles', ha='left', va='top', fontsize=9, transform=ax6.transAxes)
ax6.text(0.1, 0.45, '• Direct TX/LA hit', ha='left', va='top', fontsize=9, transform=ax6.transAxes)
ax6.text(0.1, 0.30, '• PADD 3 threat: 8.9/10', ha='left', va='top', fontsize=9, 
         transform=ax6.transAxes, color='#E74C3C', fontweight='bold')
ax6.text(0.1, 0.15, '• Gas impact: +12%', ha='left', va='top', fontsize=9, 
         transform=ax6.transAxes, color='#E74C3C', fontweight='bold')
ax6.axis('off')
ax6.add_patch(mpatches.Rectangle((0.05, 0.05), 0.9, 0.9, 
              fill=False, edgecolor='#E74C3C', linewidth=2, transform=ax6.transAxes))

# Key insight
ax7 = fig.add_subplot(gs[2, 2])
ax7.text(0.5, 0.75, '💡 KEY INSIGHT', ha='center', va='top', fontsize=13, 
         fontweight='bold', transform=ax7.transAxes, color='#3498DB')
ax7.text(0.5, 0.55, 'Location > Intensity', ha='center', va='top', fontsize=11, 
         transform=ax7.transAxes, fontweight='bold')
ax7.text(0.5, 0.4, 'for gas price prediction', ha='center', va='top', fontsize=10, 
         transform=ax7.transAxes)
ax7.text(0.5, 0.2, 'Geographic specificity', ha='center', va='top', fontsize=9, 
         transform=ax7.transAxes, style='italic')
ax7.text(0.5, 0.1, 'is critical!', ha='center', va='top', fontsize=9, 
         transform=ax7.transAxes, style='italic')
ax7.axis('off')
ax7.add_patch(mpatches.FancyBboxPatch((0.1, 0.05), 0.8, 0.8, 
              boxstyle="round,pad=0.05", edgecolor='#3498DB', 
              facecolor='#EBF5FB', linewidth=2, transform=ax7.transAxes))

plt.savefig(OUTPUT_DIR / 'hurricane_enhancement_comparison.png', dpi=150, bbox_inches='tight')
print(f"✓ Saved comparison visualization: {OUTPUT_DIR / 'hurricane_enhancement_comparison.png'}")
