#!/usr/bin/env python3
"""
Generate FINAL paper figures for TrafficRuleBench.
These are the polished, publication-ready versions.
"""

import json
import warnings
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
from scipy import stats

warnings.filterwarnings('ignore')

# Publication settings
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.8,
})

# Color scheme
NUPLAN = "#6B5B95"   # Purple for nuPlan
GEN = "#009688"      # Teal for generated
ACCENT1 = "#E76F51"  # Coral
ACCENT2 = "#FCAD38"  # Orange
ACCENT3 = "#A1CB35"  # Green


def load_data(base_dir):
    """Load scenarios and nuPlan stats."""
    runs_dir = base_dir / 'data' / 'runs'
    stats_dir = base_dir / 'traffic_bench' / 'eval' / 'engine' / 'traffic' / 'nuplan_statistics'
    
    # Load scenarios
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
    df = pd.DataFrame(records)
    
    # Load nuPlan
    nuplan = {
        'densities': pd.read_csv(stats_dir / 'densities.csv.gz')['count_r150'].dropna().values,
        'initial_speeds': pd.read_csv(stats_dir / 'routes.csv.gz')['initial_speed'].dropna().values,
        'following': pd.read_csv(stats_dir / 'following.csv.gz')['following_distance'].dropna().values,
        'acc_pos': pd.read_csv(stats_dir / 'acc_pos.csv.gz')['acceleration'].dropna().values,
    }
    
    return df, nuplan


def create_main_paper_figure(df, nuplan, output_dir):
    """
    Create the MAIN paper figure: 2-row layout showing nuPlan alignment.
    Top: CDF comparisons (most rigorous)
    Bottom: Histograms with quantile markers (more intuitive)
    """
    fig = plt.figure(figsize=(10, 7))
    gs = GridSpec(2, 4, figure=fig, hspace=0.35, wspace=0.35, 
                  height_ratios=[1, 1])
    
    # Data preparation
    metrics = [
        ('Traffic Density', 
         nuplan['densities'][nuplan['densities'] > 0], 
         df['nuplan_vehicles_per_frame'].dropna().values,
         'Vehicles (150m)', (0, 70)),
        ('Initial Ego Speed',
         nuplan['initial_speeds'],
         df['spawn_velocity_ms'].dropna().values,
         'Speed (m/s)', (0, 18)),
        ('Following Distance',
         nuplan['following'][(nuplan['following'] > 0) & (nuplan['following'] < 50)],
         df['profile_DISTANCE_WANTED'].dropna().values,
         'Distance (m)', (0, 45)),
        ('IDM Acceleration',
         nuplan['acc_pos'][(nuplan['acc_pos'] > 0) & (nuplan['acc_pos'] < 4)],
         df['profile_ACC_FACTOR'].dropna().values,
         'Accel. (m/s²)', (0, 3.5)),
    ]
    
    # ROW 1: CDF comparisons
    for i, (title, np_data, gen_data, xlabel, xlim) in enumerate(metrics):
        ax = fig.add_subplot(gs[0, i])
        
        # Clean data
        gen_clean = gen_data[(gen_data >= xlim[0]) & (gen_data <= xlim[1])]
        np_clean = np_data[(np_data >= xlim[0]) & (np_data <= xlim[1])]
        
        # CDFs
        np_sorted = np.sort(np_clean)
        np_cdf = np.arange(1, len(np_sorted)+1) / len(np_sorted)
        gen_sorted = np.sort(gen_clean)
        gen_cdf = np.arange(1, len(gen_sorted)+1) / len(gen_sorted)
        
        ax.plot(np_sorted, np_cdf, color=NUPLAN, lw=2, label='nuPlan', alpha=0.9)
        ax.plot(gen_sorted, gen_cdf, color=GEN, lw=2, label='Generated', alpha=0.9)
        
        # Quartile markers
        for q, color in [(0.25, ACCENT1), (0.5, ACCENT2), (0.75, ACCENT3)]:
            qval = np.quantile(np_clean, q)
            ax.axvline(qval, color=color, ls=':', lw=1.2, alpha=0.7)
            ax.scatter([qval], [q], color=color, s=30, zorder=5)
        
        # KS statistic
        ks_stat, _ = stats.ks_2samp(np_clean[:30000], gen_clean)
        
        ax.set_xlabel(xlabel)
        if i == 0:
            ax.set_ylabel('CDF')
        ax.set_title(f'({chr(97+i)}) {title}', fontweight='bold')
        ax.set_xlim(xlim)
        ax.set_ylim(0, 1.05)
        ax.grid(True, alpha=0.2)
        
        # KS annotation
        ax.text(0.97, 0.05, f'KS={ks_stat:.2f}', transform=ax.transAxes,
               fontsize=8, ha='right', va='bottom',
               bbox=dict(facecolor='white', edgecolor='gray', 
                        boxstyle='round,pad=0.2', alpha=0.8))
        
        if i == 0:
            ax.legend(loc='lower right', frameon=True, fancybox=False)
    
    # ROW 2: Histograms with quantile markers
    for i, (title, np_data, gen_data, xlabel, xlim) in enumerate(metrics):
        ax = fig.add_subplot(gs[1, i])
        
        gen_clean = gen_data[(gen_data >= xlim[0]) & (gen_data <= xlim[1])]
        np_clean = np_data[(np_data >= xlim[0]) & (np_data <= xlim[1])]
        
        bins = np.linspace(xlim[0], xlim[1], 35)
        
        # Histograms
        ax.hist(np_clean, bins=bins, density=True, alpha=0.5, 
               color=NUPLAN, label='nuPlan', edgecolor='white', lw=0.3)
        ax.hist(gen_clean, bins=bins, density=True, alpha=0.5, 
               color=GEN, label='Generated', edgecolor='white', lw=0.3)
        
        # Quantile lines
        ymax = ax.get_ylim()[1]
        for q, color, label in [(0.25, ACCENT1, 'Q25'), (0.5, ACCENT2, 'Q50'), (0.75, ACCENT3, 'Q75')]:
            qval_np = np.quantile(np_clean, q)
            ax.axvline(qval_np, color=color, ls='--', lw=1.5, alpha=0.8)
        
        ax.set_xlabel(xlabel)
        if i == 0:
            ax.set_ylabel('Density')
        ax.set_title(f'({chr(101+i)}) {title}', fontweight='bold')
        ax.set_xlim(xlim)
        ax.grid(True, alpha=0.2, axis='y')
        
        if i == 0:
            ax.legend(loc='upper right', frameon=True, fancybox=False)
    
    plt.savefig(output_dir / 'nuplan_alignment_main.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'nuplan_alignment_main.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Created: nuplan_alignment_main.pdf")


def create_compact_3panel(df, nuplan, output_dir):
    """
    Create ultra-compact 1x3 figure for severe space constraints.
    Shows only the most important metrics.
    """
    fig, axes = plt.subplots(1, 3, figsize=(10, 3))
    
    # Key metrics only
    metrics = [
        ('Traffic Density', 
         nuplan['densities'][nuplan['densities'] > 0],
         df['nuplan_vehicles_per_frame'].dropna().values,
         'Vehicles (150m)', (0, 70)),
        ('Initial Ego Speed',
         nuplan['initial_speeds'],
         df['spawn_velocity_ms'].dropna().values,
         'Speed (m/s)', (0, 18)),
        ('Following Distance',
         nuplan['following'][(nuplan['following'] > 0) & (nuplan['following'] < 50)],
         df['profile_DISTANCE_WANTED'].dropna().values,
         'Distance (m)', (0, 45)),
    ]
    
    for ax, (title, np_data, gen_data, xlabel, xlim) in zip(axes, metrics):
        gen_clean = gen_data[(gen_data >= xlim[0]) & (gen_data <= xlim[1])]
        np_clean = np_data[(np_data >= xlim[0]) & (np_data <= xlim[1])]
        
        # CDFs
        np_sorted = np.sort(np_clean)
        np_cdf = np.arange(1, len(np_sorted)+1) / len(np_sorted)
        gen_sorted = np.sort(gen_clean)
        gen_cdf = np.arange(1, len(gen_sorted)+1) / len(gen_sorted)
        
        ax.plot(np_sorted, np_cdf, color=NUPLAN, lw=2.5, label='nuPlan')
        ax.plot(gen_sorted, gen_cdf, color=GEN, lw=2.5, label='Generated')
        
        # Fill area between
        # ax.fill_between(np_sorted, np_cdf, alpha=0.2, color=NUPLAN)
        
        ax.set_xlabel(xlabel)
        ax.set_ylabel('CDF')
        ax.set_title(title, fontweight='bold')
        ax.set_xlim(xlim)
        ax.set_ylim(0, 1.05)
        ax.legend(loc='lower right', frameon=True)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'nuplan_compact_3panel.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'nuplan_compact_3panel.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Created: nuplan_compact_3panel.pdf")


def create_scenario_overview_figure(df, output_dir):
    """
    Create a comprehensive scenario overview figure.
    Shows sign distribution, geographic coverage, and augmentation axes.
    """
    fig = plt.figure(figsize=(12, 4))
    gs = GridSpec(1, 4, figure=fig, wspace=0.35)
    
    # (a) Sign category distribution
    ax1 = fig.add_subplot(gs[0, 0])
    
    categories = {
        'Priority': ['main_road', 'secondary_road', 'stop', 'yield', 'roundabout'],
        'Direction': ['direction_left', 'direction_right', 'direction_straight', 
                     'direction_left_right', 'direction_straight_left', 'direction_straight_right',
                     'one_way_left', 'one_way_right'],
        'Prohibition': ['no_entry', 'no_turn_left', 'no_turn_right', 'blocked_road'],
        'Speed': ['speed_limit'],
        'Special': ['crosswalk', 'detour_right'],
    }
    
    family_counts = df['_sign_family'].value_counts()
    cat_counts = {cat: sum(family_counts.get(s, 0) for s in signs) 
                  for cat, signs in categories.items()}
    
    colors = ['#E76F51', '#4A90A4', '#A1CB35', '#FCAD38', '#9B59B6']
    
    # Horizontal bar chart
    cats = list(cat_counts.keys())
    vals = list(cat_counts.values())
    y_pos = np.arange(len(cats))
    
    bars = ax1.barh(y_pos, vals, color=colors, edgecolor='white', lw=0.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(cats)
    ax1.set_xlabel('Number of Scenarios')
    ax1.set_title('(a) Sign Categories', fontweight='bold')
    ax1.invert_yaxis()
    
    # Add percentages
    total = sum(vals)
    for bar, val in zip(bars, vals):
        ax1.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                f'{val/total*100:.0f}%', va='center', fontsize=8)
    
    # (b) Geographic distribution
    ax2 = fig.add_subplot(gs[0, 1])
    
    lats = df['latitude'].dropna().values
    lons = df['longitude'].dropna().values
    
    # Filter Moscow region
    mask = (lats > 55.5) & (lats < 56.1) & (lons > 37.2) & (lons < 38.0)
    lats_c, lons_c = lats[mask], lons[mask]
    
    # Hexbin for density
    hb = ax2.hexbin(lons_c, lats_c, gridsize=20, cmap='YlOrRd', mincnt=1)
    ax2.scatter([37.6173], [55.7558], marker='*', s=100, c='black', 
               label='Moscow', zorder=10)
    
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.set_title('(b) Geographic Coverage', fontweight='bold')
    ax2.legend(loc='upper left', fontsize=8)
    
    # (c) Traffic density levels
    ax3 = fig.add_subplot(gs[0, 2])
    
    # Create density level breakdown
    density_levels = df['density_level_name'].value_counts()
    order = ['sparse', 'typical', 'dense']
    vals = [density_levels.get(d, 0) for d in order]
    
    bars = ax3.bar(order, vals, color=[ACCENT1, ACCENT2, ACCENT3], 
                  edgecolor='white', lw=0.5)
    ax3.set_xlabel('Density Level')
    ax3.set_ylabel('Scenarios')
    ax3.set_title('(c) Traffic Density', fontweight='bold')
    
    # Percentages
    for bar, val in zip(bars, vals):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                f'{val/sum(vals)*100:.0f}%', ha='center', fontsize=9)
    
    # (d) Scenario augmentation breakdown
    ax4 = fig.add_subplot(gs[0, 3])
    
    # Compute variation stats
    unique_maps = df['scene_name'].nunique()
    total_scenarios = len(df)
    avg_per_map = total_scenarios / unique_maps
    
    # Augmentation axes breakdown
    aug_data = {
        'Spawn Lane': df['spawn_lane_num'].nunique(),
        'Route Length': df['route_length_level_m'].nunique() if 'route_length_level_m' in df else 3,
        'Init. Speed': df['spawn_velocity_level_id'].nunique() if 'spawn_velocity_level_id' in df else 3,
        'Traffic Dens.': df['density_level_id'].nunique() if 'density_level_id' in df else 3,
    }
    
    ax4.barh(list(aug_data.keys()), list(aug_data.values()), 
            color='#4A90A4', edgecolor='white', lw=0.5)
    ax4.set_xlabel('Unique Values')
    ax4.set_title('(d) Augmentation Axes', fontweight='bold')
    
    # Add summary stats as text
    ax4.text(0.95, 0.05, f'{unique_maps:,} maps\n{total_scenarios:,} scenarios\n~{avg_per_map:.0f}× expansion',
            transform=ax4.transAxes, ha='right', va='bottom', fontsize=8,
            bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.3'))
    
    plt.savefig(output_dir / 'scenario_overview.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'scenario_overview.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Created: scenario_overview.pdf")


def create_combined_paper_figure(df, nuplan, output_dir):
    """
    Create combined figure: nuPlan alignment + scenario overview.
    This is the FINAL figure for the paper.
    """
    fig = plt.figure(figsize=(12, 8))
    
    # Create a 3-row layout
    gs = GridSpec(3, 4, figure=fig, hspace=0.4, wspace=0.35,
                  height_ratios=[1, 0.9, 0.9])
    
    # ==== ROW 1: CDF comparisons ====
    metrics = [
        ('Traffic Density', 
         nuplan['densities'][nuplan['densities'] > 0],
         df['nuplan_vehicles_per_frame'].dropna().values,
         'Vehicles (150m)', (0, 70)),
        ('Initial Ego Speed',
         nuplan['initial_speeds'],
         df['spawn_velocity_ms'].dropna().values,
         'Speed (m/s)', (0, 18)),
        ('Following Distance',
         nuplan['following'][(nuplan['following'] > 0) & (nuplan['following'] < 50)],
         df['profile_DISTANCE_WANTED'].dropna().values,
         'Distance (m)', (0, 45)),
        ('IDM Acceleration',
         nuplan['acc_pos'][(nuplan['acc_pos'] > 0) & (nuplan['acc_pos'] < 4)],
         df['profile_ACC_FACTOR'].dropna().values,
         'Accel. (m/s²)', (0, 3.5)),
    ]
    
    for i, (title, np_data, gen_data, xlabel, xlim) in enumerate(metrics):
        ax = fig.add_subplot(gs[0, i])
        
        gen_clean = gen_data[(gen_data >= xlim[0]) & (gen_data <= xlim[1])]
        np_clean = np_data[(np_data >= xlim[0]) & (np_data <= xlim[1])]
        
        np_sorted = np.sort(np_clean)
        np_cdf = np.arange(1, len(np_sorted)+1) / len(np_sorted)
        gen_sorted = np.sort(gen_clean)
        gen_cdf = np.arange(1, len(gen_sorted)+1) / len(gen_sorted)
        
        ax.plot(np_sorted, np_cdf, color=NUPLAN, lw=2, label='nuPlan')
        ax.plot(gen_sorted, gen_cdf, color=GEN, lw=2, label='Generated')
        
        ax.set_xlabel(xlabel)
        if i == 0:
            ax.set_ylabel('CDF')
        ax.set_title(f'({chr(97+i)}) {title}', fontweight='bold', fontsize=10)
        ax.set_xlim(xlim)
        ax.set_ylim(0, 1.05)
        ax.grid(True, alpha=0.2)
        
        if i == 0:
            ax.legend(loc='lower right', frameon=True, fontsize=8)
    
    # ==== ROW 2: Sign categories + Geographic + Train/Test ====
    # Sign categories
    ax = fig.add_subplot(gs[1, :2])
    
    categories = {
        'Priority': ['main_road', 'secondary_road', 'stop', 'yield', 'roundabout'],
        'Direction': ['direction_left', 'direction_right', 'direction_straight', 
                     'direction_left_right', 'direction_straight_left', 'direction_straight_right',
                     'one_way_left', 'one_way_right'],
        'Prohibition': ['no_entry', 'no_turn_left', 'no_turn_right', 'blocked_road'],
        'Speed': ['speed_limit'],
        'Special': ['crosswalk', 'detour_right'],
    }
    
    family_counts = df['_sign_family'].value_counts()
    cat_counts = {cat: sum(family_counts.get(s, 0) for s in signs) 
                  for cat, signs in categories.items()}
    
    colors = ['#E76F51', '#4A90A4', '#A1CB35', '#FCAD38', '#9B59B6']
    wedges, texts, autotexts = ax.pie(cat_counts.values(), labels=cat_counts.keys(),
                                       autopct='%1.0f%%', colors=colors,
                                       pctdistance=0.75)
    ax.set_title('(e) Sign Category Distribution', fontweight='bold', fontsize=10)
    
    # Geographic
    ax = fig.add_subplot(gs[1, 2:])
    
    lats = df['latitude'].dropna().values
    lons = df['longitude'].dropna().values
    mask = (lats > 55.5) & (lats < 56.1) & (lons > 37.2) & (lons < 38.0)
    
    ax.hexbin(lons[mask], lats[mask], gridsize=25, cmap='YlOrRd', mincnt=1)
    ax.scatter([37.6173], [55.7558], marker='*', s=150, c='black', 
              label='Moscow Center', zorder=10)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('(f) Geographic Coverage', fontweight='bold', fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    
    # ==== ROW 3: Density levels + Summary stats ====
    ax = fig.add_subplot(gs[2, :2])
    
    density_levels = df['density_level_name'].value_counts()
    order = ['sparse', 'typical', 'dense']
    vals = [density_levels.get(d, 0) for d in order]
    percentiles = ['25th %ile', '50th %ile', '75th %ile']
    
    x = np.arange(len(order))
    bars = ax.bar(x, vals, color=[ACCENT1, ACCENT2, ACCENT3], 
                 edgecolor='white', lw=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{o}\n({p})' for o, p in zip(order, percentiles)])
    ax.set_ylabel('Number of Scenarios')
    ax.set_title('(g) Traffic Density Distribution', fontweight='bold', fontsize=10)
    
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
               f'{val/sum(vals)*100:.0f}%', ha='center', fontsize=9)
    
    # Summary statistics
    ax = fig.add_subplot(gs[2, 2:])
    ax.axis('off')
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Scenarios', f'{len(df):,}'],
        ['Train / Test', f'{len(df[df["_split"]=="train"]):,} / {len(df[df["_split"]=="test"]):,}'],
        ['Unique Maps', f'{df["scene_name"].nunique():,}'],
        ['Sign Types', f'{df["_sign_family"].nunique()}'],
        ['Avg. Background Vehicles', f'{df["nuplan_vehicles_per_frame"].mean():.1f}'],
        ['Avg. Initial Speed', f'{df["spawn_velocity_ms"].mean():.1f} m/s'],
    ]
    
    table = ax.table(cellText=summary_data[1:], colLabels=summary_data[0],
                    loc='center', cellLoc='center',
                    colColours=['#E8E8E8']*2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.3, 1.6)
    
    ax.set_title('(h) Dataset Summary', fontweight='bold', fontsize=10, pad=20)
    
    plt.savefig(output_dir / 'scene_statistics_combined.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'scene_statistics_combined.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("Created: scene_statistics_combined.pdf (FULL PAPER FIGURE)")


def main():
    base_dir = Path('/home/jovyan/shares/SR006.nfs2/zinkovich/zinkovich/traffic-rule-bench')
    output_dir = base_dir / 'scripts' / 'scene_analysis' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    df, nuplan = load_data(base_dir)
    print(f"Loaded {len(df)} scenarios")
    
    print("\nGenerating final paper figures...")
    create_main_paper_figure(df, nuplan, output_dir)
    create_compact_3panel(df, nuplan, output_dir)
    create_scenario_overview_figure(df, output_dir)
    create_combined_paper_figure(df, nuplan, output_dir)
    
    print("\nAll figures generated!")


if __name__ == '__main__':
    main()
