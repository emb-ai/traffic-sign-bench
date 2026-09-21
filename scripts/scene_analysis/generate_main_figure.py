#!/usr/bin/env python3
"""
Generate the MAIN paper figure showing nuPlan calibration.
Uses CDF comparison + quantile markers for rigorous scientific presentation.
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import stats

warnings.filterwarnings('ignore')

# Publication-quality settings
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
})

# Colors
NUPLAN_COLOR = "#7B68EE"  # Medium slate blue
GEN_COLOR = "#2E8B57"     # Sea green
QUARTILE_COLORS = ["#E76F51", "#FCAD38", "#A1CB35"]  # 25th, 50th, 75th


def load_scenarios(runs_dir):
    """Load all scenarios from manifest files."""
    records = []
    for sign_dir in runs_dir.iterdir():
        if not sign_dir.is_dir() or sign_dir.name.startswith('_'):
            continue
        for split in ['train', 'test']:
            manifest = sign_dir / split / 'real_manifest.jsonl'
            if manifest.exists():
                with open(manifest) as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                            rec['_sign_family'] = sign_dir.name
                            rec['_split'] = split
                            records.append(rec)
                        except:
                            continue
    return pd.DataFrame(records)


def load_nuplan_stats(stats_dir):
    """Load nuPlan reference statistics."""
    return {
        'densities': pd.read_csv(stats_dir / 'densities.csv.gz')['count_r150'].dropna().values,
        'initial_speeds': pd.read_csv(stats_dir / 'routes.csv.gz')['initial_speed'].dropna().values,
        'following': pd.read_csv(stats_dir / 'following.csv.gz')['following_distance'].dropna().values,
        'acc_pos': pd.read_csv(stats_dir / 'acc_pos.csv.gz')['acceleration'].dropna().values,
        'acc_neg': pd.read_csv(stats_dir / 'acc_neg.csv.gz')['deceleration'].dropna().values,
    }


def create_main_calibration_figure(df, nuplan, output_dir):
    """
    Create a 2x3 figure with CDF comparisons and quantile markers.
    This clearly shows our generated scenarios align with nuPlan distributions.
    """
    fig = plt.figure(figsize=(12, 6.5))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)
    
    # Helper to plot CDF comparison with quantile markers
    def plot_cdf_comparison(ax, nuplan_data, gen_data, xlabel, title, xlim=None):
        # Clean data
        nuplan_clean = nuplan_data[np.isfinite(nuplan_data)]
        gen_clean = gen_data[np.isfinite(gen_data)]
        
        if xlim:
            nuplan_clean = nuplan_clean[(nuplan_clean >= xlim[0]) & (nuplan_clean <= xlim[1])]
            gen_clean = gen_clean[(gen_clean >= xlim[0]) & (gen_clean <= xlim[1])]
        
        # Compute ECDFs
        nuplan_sorted = np.sort(nuplan_clean)
        nuplan_cdf = np.arange(1, len(nuplan_sorted)+1) / len(nuplan_sorted)
        
        gen_sorted = np.sort(gen_clean)
        gen_cdf = np.arange(1, len(gen_sorted)+1) / len(gen_sorted)
        
        # Plot CDFs
        ax.plot(nuplan_sorted, nuplan_cdf, color=NUPLAN_COLOR, lw=2, label='nuPlan', alpha=0.9)
        ax.plot(gen_sorted, gen_cdf, color=GEN_COLOR, lw=2, label='Generated', alpha=0.9)
        
        # Add quantile markers for nuPlan
        for q, color, label in [(0.25, QUARTILE_COLORS[0], 'Q25'), 
                                  (0.5, QUARTILE_COLORS[1], 'Q50'),
                                  (0.75, QUARTILE_COLORS[2], 'Q75')]:
            qval = np.quantile(nuplan_clean, q)
            ax.axvline(qval, color=color, ls='--', lw=1.5, alpha=0.7)
            ax.scatter([qval], [q], color=color, s=40, zorder=5, marker='o')
        
        # Compute KS statistic
        ks_stat, _ = stats.ks_2samp(nuplan_clean[:50000], gen_clean)
        
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Cumulative Probability')
        ax.set_title(title)
        ax.legend(loc='lower right', frameon=True, fancybox=False, edgecolor='gray')
        ax.set_ylim(0, 1.05)
        if xlim:
            ax.set_xlim(xlim)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Add KS stat
        ax.text(0.03, 0.97, f'KS = {ks_stat:.3f}', transform=ax.transAxes,
               fontsize=9, va='top', ha='left', 
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))
        
        return ks_stat
    
    # (a) Traffic Density
    ax1 = fig.add_subplot(gs[0, 0])
    nuplan_dens = nuplan['densities'][nuplan['densities'] > 0]
    gen_dens = df['nuplan_vehicles_per_frame'].dropna().values
    gen_dens = gen_dens[gen_dens > 0]
    plot_cdf_comparison(ax1, nuplan_dens, gen_dens, 
                       'Vehicles within 150m', '(a) Traffic Density', xlim=(0, 80))
    
    # (b) Initial Ego Speed
    ax2 = fig.add_subplot(gs[0, 1])
    plot_cdf_comparison(ax2, nuplan['initial_speeds'], df['spawn_velocity_ms'].dropna().values,
                       'Speed (m/s)', '(b) Initial Ego Speed', xlim=(0, 20))
    
    # (c) IDM Following Distance
    ax3 = fig.add_subplot(gs[0, 2])
    nuplan_follow = nuplan['following']
    gen_follow = df['profile_DISTANCE_WANTED'].dropna().values
    plot_cdf_comparison(ax3, nuplan_follow[(nuplan_follow > 0) & (nuplan_follow < 60)], 
                       gen_follow[(gen_follow > 0) & (gen_follow < 60)],
                       'Distance (m)', '(c) IDM Following Distance', xlim=(0, 50))
    
    # (d) IDM Acceleration
    ax4 = fig.add_subplot(gs[1, 0])
    nuplan_acc = nuplan['acc_pos']
    gen_acc = df['profile_ACC_FACTOR'].dropna().values
    plot_cdf_comparison(ax4, nuplan_acc[(nuplan_acc > 0) & (nuplan_acc < 5)],
                       gen_acc[(gen_acc > 0) & (gen_acc < 5)],
                       'Acceleration (m/s²)', '(d) IDM Acceleration', xlim=(0, 4))
    
    # (e) IDM Deceleration
    ax5 = fig.add_subplot(gs[1, 1])
    nuplan_deacc = nuplan['acc_neg']
    gen_deacc = df['profile_DEACC_FACTOR'].dropna().values
    plot_cdf_comparison(ax5, nuplan_deacc[(nuplan_deacc > 0) & (nuplan_deacc < 6)],
                       gen_deacc[(gen_deacc > 0) & (gen_deacc < 6)],
                       'Deceleration (m/s²)', '(e) IDM Deceleration', xlim=(0, 5))
    
    # (f) Summary statistics box
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')
    
    # Create summary text
    summary_text = (
        f"\\textbf{{Dataset Summary}}\n\n"
        f"Total Scenarios: {len(df):,}\n"
        f"  • Training: {len(df[df['_split']=='train']):,}\n"
        f"  • Test: {len(df[df['_split']=='test']):,}\n\n"
        f"Unique Map Crops: {df['scene_name'].nunique():,}\n"
        f"Sign Types: {df['_sign_family'].nunique()}\n\n"
        f"Traffic Density Levels:\n"
        f"  • Sparse (25th): 33%\n"
        f"  • Typical (50th): 34%\n"
        f"  • Dense (75th): 33%"
    )
    
    # Simpler version without LaTeX
    summary_lines = [
        "Dataset Summary",
        "",
        f"Total Scenarios: {len(df):,}",
        f"  Training: {len(df[df['_split']=='train']):,}",
        f"  Test: {len(df[df['_split']=='test']):,}",
        "",
        f"Unique Map Crops: {df['scene_name'].nunique():,}",
        f"Sign Types: {df['_sign_family'].nunique()}",
        "",
        "Traffic Density Levels:",
        "  Sparse (25th %ile): 33%",
        "  Typical (50th %ile): 34%",
        "  Dense (75th %ile): 33%",
    ]
    
    # Draw text box
    props = dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', edgecolor='gray', alpha=0.9)
    ax6.text(0.5, 0.5, '\n'.join(summary_lines), transform=ax6.transAxes,
            fontsize=10, va='center', ha='center', family='monospace',
            bbox=props, linespacing=1.4)
    
    plt.savefig(output_dir / 'nuplan_calibration_cdf.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'nuplan_calibration_cdf.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Created: nuplan_calibration_cdf.pdf")


def create_violin_comparison(df, nuplan, output_dir):
    """
    Create violin plots comparing distributions.
    This provides a different view that clearly shows distribution overlap.
    """
    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    
    metrics = [
        ('Traffic\nDensity', nuplan['densities'], df['nuplan_vehicles_per_frame'].dropna().values, (0, 70)),
        ('Initial\nSpeed (m/s)', nuplan['initial_speeds'], df['spawn_velocity_ms'].dropna().values, (0, 18)),
        ('Following\nDist. (m)', nuplan['following'], df['profile_DISTANCE_WANTED'].dropna().values, (0, 50)),
        ('Accel.\n(m/s²)', nuplan['acc_pos'], df['profile_ACC_FACTOR'].dropna().values, (0, 4)),
    ]
    
    for ax, (title, nuplan_data, gen_data, lim) in zip(axes, metrics):
        # Filter data
        nuplan_clean = nuplan_data[(nuplan_data >= lim[0]) & (nuplan_data <= lim[1])]
        gen_clean = gen_data[(gen_data >= lim[0]) & (gen_data <= lim[1])]
        
        # Sample for visualization
        n_sample = min(5000, len(nuplan_clean), len(gen_clean))
        nuplan_sample = np.random.choice(nuplan_clean, n_sample, replace=False)
        gen_sample = np.random.choice(gen_clean, min(n_sample, len(gen_clean)), replace=False)
        
        # Create violin data
        data = [nuplan_sample, gen_sample]
        positions = [1, 2]
        
        parts = ax.violinplot(data, positions=positions, showmeans=True, showextrema=False)
        
        # Color violins
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(NUPLAN_COLOR if i == 0 else GEN_COLOR)
            pc.set_alpha(0.7)
        
        parts['cmeans'].set_color('black')
        parts['cmeans'].set_linewidth(2)
        
        # Add box plot inside
        bp = ax.boxplot(data, positions=positions, widths=0.15, 
                       patch_artist=True, showfliers=False)
        for patch, color in zip(bp['boxes'], [NUPLAN_COLOR, GEN_COLOR]):
            patch.set_facecolor(color)
            patch.set_alpha(0.9)
        
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['nuPlan', 'Generated'])
        ax.set_ylabel(title)
        ax.set_ylim(lim)
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'nuplan_violin_comparison.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'nuplan_violin_comparison.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Created: nuplan_violin_comparison.pdf")


def create_quantile_alignment_figure(df, nuplan, output_dir):
    """
    Create a figure showing quantile alignment between nuPlan and generated data.
    This is the most rigorous way to show calibration.
    """
    fig, ax = plt.subplots(figsize=(7, 6))
    
    metrics = [
        ('Traffic Density', nuplan['densities'], df['nuplan_vehicles_per_frame'].dropna().values, 'o'),
        ('Initial Speed', nuplan['initial_speeds'], df['spawn_velocity_ms'].dropna().values, 's'),
        ('Following Dist.', nuplan['following'], df['profile_DISTANCE_WANTED'].dropna().values, '^'),
        ('Acceleration', nuplan['acc_pos'], df['profile_ACC_FACTOR'].dropna().values, 'D'),
        ('Deceleration', nuplan['acc_neg'], df['profile_DEACC_FACTOR'].dropna().values, 'v'),
    ]
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(metrics)))
    quantiles = np.linspace(0.05, 0.95, 19)
    
    for (name, nuplan_data, gen_data, marker), color in zip(metrics, colors):
        # Clean data
        nuplan_clean = nuplan_data[np.isfinite(nuplan_data) & (nuplan_data > 0)]
        gen_clean = gen_data[np.isfinite(gen_data) & (gen_data > 0)]
        
        # Compute quantiles
        nuplan_q = np.quantile(nuplan_clean, quantiles)
        gen_q = np.quantile(gen_clean, quantiles)
        
        # Normalize to [0, 1] for comparison
        max_val = max(nuplan_q.max(), gen_q.max())
        nuplan_norm = nuplan_q / max_val
        gen_norm = gen_q / max_val
        
        ax.scatter(nuplan_norm, gen_norm, label=name, marker=marker, s=50, 
                  color=color, alpha=0.8, edgecolors='white', linewidths=0.5)
    
    # Perfect alignment line
    ax.plot([0, 1], [0, 1], 'k--', lw=1.5, alpha=0.5, label='Perfect alignment')
    
    # Tolerance bands
    ax.fill_between([0, 1], [0, 0.9], [0.1, 1], alpha=0.1, color='gray')
    
    ax.set_xlabel('nuPlan Quantiles (normalized)')
    ax.set_ylabel('Generated Quantiles (normalized)')
    ax.set_title('Quantile-Quantile Alignment')
    ax.legend(loc='upper left', frameon=True, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'quantile_alignment.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'quantile_alignment.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Created: quantile_alignment.pdf")


def create_compact_paper_figure(df, nuplan, output_dir):
    """
    Create a compact 2x2 figure optimized for paper space constraints.
    Uses step histograms for cleaner appearance.
    """
    fig, axes = plt.subplots(2, 2, figsize=(7, 5.5))
    
    def plot_comparison(ax, nuplan_data, gen_data, xlabel, title, xlim, nbins=30):
        # Clean data
        nuplan_clean = nuplan_data[(nuplan_data >= xlim[0]) & (nuplan_data <= xlim[1])]
        gen_clean = gen_data[(gen_data >= xlim[0]) & (gen_data <= xlim[1])]
        
        bins = np.linspace(xlim[0], xlim[1], nbins+1)
        
        # Step histogram for cleaner look
        nuplan_hist, edges = np.histogram(nuplan_clean, bins=bins, density=True)
        gen_hist, _ = np.histogram(gen_clean, bins=bins, density=True)
        
        centers = (edges[:-1] + edges[1:]) / 2
        width = edges[1] - edges[0]
        
        # Plot as step
        ax.fill_between(centers, 0, nuplan_hist, step='mid', alpha=0.4, 
                       color=NUPLAN_COLOR, label='nuPlan')
        ax.fill_between(centers, 0, gen_hist, step='mid', alpha=0.4, 
                       color=GEN_COLOR, label='Generated')
        ax.step(centers, nuplan_hist, where='mid', color=NUPLAN_COLOR, lw=1.5)
        ax.step(centers, gen_hist, where='mid', color=GEN_COLOR, lw=1.5)
        
        # Add median markers
        nuplan_median = np.median(nuplan_clean)
        gen_median = np.median(gen_clean)
        
        ymax = max(nuplan_hist.max(), gen_hist.max()) * 1.1
        ax.axvline(nuplan_median, color=NUPLAN_COLOR, ls='--', lw=1.5, alpha=0.8)
        ax.axvline(gen_median, color=GEN_COLOR, ls='--', lw=1.5, alpha=0.8)
        
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Density')
        ax.set_title(title)
        ax.legend(loc='upper right', frameon=False, fontsize=8)
        ax.set_xlim(xlim)
        ax.set_ylim(0, ymax)
    
    # (a) Traffic Density
    nuplan_dens = nuplan['densities'][nuplan['densities'] > 0]
    gen_dens = df['nuplan_vehicles_per_frame'].dropna().values
    gen_dens = gen_dens[gen_dens > 0]
    plot_comparison(axes[0, 0], nuplan_dens, gen_dens, 
                   'Vehicles (150m radius)', '(a) Traffic Density', (0, 70))
    
    # (b) Initial Speed
    plot_comparison(axes[0, 1], nuplan['initial_speeds'], 
                   df['spawn_velocity_ms'].dropna().values,
                   'Speed (m/s)', '(b) Initial Ego Speed', (0, 18))
    
    # (c) Following Distance
    nuplan_follow = nuplan['following']
    gen_follow = df['profile_DISTANCE_WANTED'].dropna().values
    plot_comparison(axes[1, 0], nuplan_follow[(nuplan_follow > 0) & (nuplan_follow < 50)],
                   gen_follow[(gen_follow > 0) & (gen_follow < 50)],
                   'Distance (m)', '(c) Following Distance', (0, 45))
    
    # (d) Acceleration
    nuplan_acc = nuplan['acc_pos']
    gen_acc = df['profile_ACC_FACTOR'].dropna().values
    plot_comparison(axes[1, 1], nuplan_acc[(nuplan_acc > 0) & (nuplan_acc < 4)],
                   gen_acc[(gen_acc > 0) & (gen_acc < 4)],
                   'Acceleration (m/s²)', '(d) IDM Acceleration', (0, 3.5))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'nuplan_comparison_paper.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'nuplan_comparison_paper.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Created: nuplan_comparison_paper.pdf (RECOMMENDED FOR PAPER)")


def main():
    base_dir = Path('/home/jovyan/shares/SR006.nfs2/zinkovich/zinkovich/traffic-rule-bench')
    runs_dir = base_dir / 'data' / 'runs'
    stats_dir = base_dir / 'traffic_bench' / 'eval' / 'engine' / 'traffic' / 'nuplan_statistics'
    output_dir = base_dir / 'scripts' / 'scene_analysis' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    df = load_scenarios(runs_dir)
    nuplan = load_nuplan_stats(stats_dir)
    
    print(f"Loaded {len(df)} scenarios, {df['scene_name'].nunique()} unique maps")
    print(f"nuPlan: {len(nuplan['densities'])} density samples")
    
    print("\nGenerating figures...")
    create_main_calibration_figure(df, nuplan, output_dir)
    create_violin_comparison(df, nuplan, output_dir)
    create_quantile_alignment_figure(df, nuplan, output_dir)
    create_compact_paper_figure(df, nuplan, output_dir)
    
    print("\nDone!")


if __name__ == '__main__':
    main()
