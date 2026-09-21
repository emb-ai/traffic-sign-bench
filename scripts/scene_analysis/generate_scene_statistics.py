#!/usr/bin/env python3
"""
High-level Statistical Overview of Generated Scenes for TrafficRuleBench Paper.

Generates publication-quality figures comparing generated scenarios with nuPlan
and showing diversity across multiple axes.
"""

import json
import warnings
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from scipy import stats
from scipy.stats import gaussian_kde

warnings.filterwarnings('ignore')

# Set publication style
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# Color palette matching the paper style
COLORS = {
    "primary": "#4A90A4",      # Teal-blue
    "secondary": "#E76F51",    # Coral
    "tertiary": "#A1CB35",     # Green
    "quaternary": "#FCAD38",   # Orange
    "nuplan": "#7B68EE",       # Medium slate blue for nuPlan
    "generated": "#2E8B57",    # Sea green for generated
    "light_fill": "#90CAF9",   # Light blue fill
}

# Additional colors for multi-category plots
CATEGORY_COLORS = [
    "#4A90A4", "#E76F51", "#A1CB35", "#FCAD38", 
    "#9B59B6", "#3498DB", "#E74C3C", "#1ABC9C"
]


def load_all_scenarios(runs_dir):
    """Load all scenario manifests."""
    all_records = []
    
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
                            all_records.append(rec)
                        except json.JSONDecodeError:
                            continue
    
    return pd.DataFrame(all_records)


def load_nuplan_statistics(stats_dir):
    """Load nuPlan reference statistics."""
    data = {}
    
    # Load densities
    dens = pd.read_csv(stats_dir / 'densities.csv.gz')
    data['densities'] = dens['count_r150'].dropna().values
    
    # Load speeds
    speeds = pd.read_csv(stats_dir / 'speeds.csv.gz')
    data['speeds'] = speeds['speed'].dropna().values
    
    # Load routes (initial speeds)
    routes = pd.read_csv(stats_dir / 'routes.csv.gz')
    data['initial_speeds'] = routes['initial_speed'].dropna().values
    data['durations'] = routes['duration'].dropna().values
    data['distances'] = routes['distance'].dropna().values
    
    # Load following distances
    following = pd.read_csv(stats_dir / 'following.csv.gz')
    data['following'] = following['following_distance'].dropna().values
    
    # Load accelerations
    acc_pos = pd.read_csv(stats_dir / 'acc_pos.csv.gz')
    data['acc_pos'] = acc_pos['acceleration'].dropna().values
    
    acc_neg = pd.read_csv(stats_dir / 'acc_neg.csv.gz')
    data['acc_neg'] = acc_neg['deceleration'].dropna().values
    
    return data


def create_nuplan_comparison_figure(df, nuplan_data, output_dir):
    """
    Create a comprehensive nuPlan vs Generated comparison figure.
    This is the key figure showing our scenarios match real-world distributions.
    """
    fig = plt.figure(figsize=(12, 8))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)
    
    # 1. Traffic density comparison (vehicles per frame within 150m)
    ax1 = fig.add_subplot(gs[0, 0])
    
    # nuPlan densities
    nuplan_dens = nuplan_data['densities']
    nuplan_dens = nuplan_dens[nuplan_dens > 0]  # Filter zeros
    
    # Generated densities (nuplan_vehicles_per_frame)
    gen_dens = df['nuplan_vehicles_per_frame'].dropna().values
    gen_dens = gen_dens[gen_dens > 0]
    
    # Plot histograms with KDE
    bins = np.linspace(0, 80, 40)
    
    ax1.hist(nuplan_dens, bins=bins, density=True, alpha=0.5, 
             color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.5)
    ax1.hist(gen_dens, bins=bins, density=True, alpha=0.5, 
             color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.5)
    
    # Add KDE curves
    if len(nuplan_dens) > 100:
        kde_nuplan = gaussian_kde(nuplan_dens, bw_method='scott')
        x_range = np.linspace(0, 80, 200)
        ax1.plot(x_range, kde_nuplan(x_range), color=COLORS['nuplan'], lw=2, ls='--')
    
    if len(gen_dens) > 100:
        kde_gen = gaussian_kde(gen_dens, bw_method='scott')
        ax1.plot(x_range, kde_gen(x_range), color=COLORS['generated'], lw=2, ls='--')
    
    ax1.set_xlabel('Vehicles within 150m')
    ax1.set_ylabel('Density')
    ax1.set_title('(a) Traffic Density')
    ax1.legend(loc='upper right', frameon=False)
    ax1.set_xlim(0, 80)
    
    # Add statistics
    ks_stat, ks_pval = stats.ks_2samp(nuplan_dens[:10000], gen_dens)
    ax1.text(0.98, 0.75, f'KS stat: {ks_stat:.3f}', transform=ax1.transAxes, 
             ha='right', fontsize=8, color='gray')
    
    # 2. Initial ego speed comparison
    ax2 = fig.add_subplot(gs[0, 1])
    
    nuplan_speeds = nuplan_data['initial_speeds']
    gen_speeds = df['spawn_velocity_ms'].dropna().values
    
    bins = np.linspace(0, 20, 30)
    
    ax2.hist(nuplan_speeds, bins=bins, density=True, alpha=0.5, 
             color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.5)
    ax2.hist(gen_speeds, bins=bins, density=True, alpha=0.5, 
             color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.5)
    
    if len(nuplan_speeds) > 100:
        kde_nuplan = gaussian_kde(nuplan_speeds[nuplan_speeds < 20], bw_method='scott')
        x_range = np.linspace(0, 20, 200)
        ax2.plot(x_range, kde_nuplan(x_range), color=COLORS['nuplan'], lw=2, ls='--')
    
    if len(gen_speeds) > 100:
        kde_gen = gaussian_kde(gen_speeds[gen_speeds < 20], bw_method='scott')
        ax2.plot(x_range, kde_gen(x_range), color=COLORS['generated'], lw=2, ls='--')
    
    ax2.set_xlabel('Initial Speed (m/s)')
    ax2.set_ylabel('Density')
    ax2.set_title('(b) Initial Ego Speed')
    ax2.legend(loc='upper right', frameon=False)
    ax2.set_xlim(0, 20)
    
    # 3. IDM Acceleration factor comparison
    ax3 = fig.add_subplot(gs[0, 2])
    
    nuplan_acc = nuplan_data['acc_pos']
    gen_acc = df['profile_ACC_FACTOR'].dropna().values
    
    bins = np.linspace(0, 4, 30)
    
    ax3.hist(nuplan_acc[(nuplan_acc > 0) & (nuplan_acc < 4)], bins=bins, density=True, alpha=0.5, 
             color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.5)
    ax3.hist(gen_acc[(gen_acc > 0) & (gen_acc < 4)], bins=bins, density=True, alpha=0.5, 
             color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.5)
    
    ax3.set_xlabel('Acceleration (m/s²)')
    ax3.set_ylabel('Density')
    ax3.set_title('(c) IDM Acceleration')
    ax3.legend(loc='upper right', frameon=False)
    ax3.set_xlim(0, 4)
    
    # 4. IDM Deceleration factor comparison
    ax4 = fig.add_subplot(gs[1, 0])
    
    nuplan_deacc = nuplan_data['acc_neg']
    gen_deacc = df['profile_DEACC_FACTOR'].dropna().values
    
    bins = np.linspace(0, 5, 30)
    
    ax4.hist(nuplan_deacc[(nuplan_deacc > 0) & (nuplan_deacc < 5)], bins=bins, density=True, alpha=0.5, 
             color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.5)
    ax4.hist(gen_deacc[(gen_deacc > 0) & (gen_deacc < 5)], bins=bins, density=True, alpha=0.5, 
             color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.5)
    
    ax4.set_xlabel('Deceleration (m/s²)')
    ax4.set_ylabel('Density')
    ax4.set_title('(d) IDM Deceleration')
    ax4.legend(loc='upper right', frameon=False)
    ax4.set_xlim(0, 5)
    
    # 5. Following distance comparison
    ax5 = fig.add_subplot(gs[1, 1])
    
    nuplan_follow = nuplan_data['following']
    gen_follow = df['profile_DISTANCE_WANTED'].dropna().values
    
    bins = np.linspace(0, 50, 30)
    
    ax5.hist(nuplan_follow[(nuplan_follow > 0) & (nuplan_follow < 50)], bins=bins, density=True, alpha=0.5, 
             color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.5)
    ax5.hist(gen_follow[(gen_follow > 0) & (gen_follow < 50)], bins=bins, density=True, alpha=0.5, 
             color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.5)
    
    ax5.set_xlabel('Following Distance (m)')
    ax5.set_ylabel('Density')
    ax5.set_title('(e) IDM Following Distance')
    ax5.legend(loc='upper right', frameon=False)
    ax5.set_xlim(0, 50)
    
    # 6. Summary statistics table
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')
    
    # Calculate summary statistics
    summary_data = [
        ['Metric', 'nuPlan', 'Generated'],
        ['Traffic Density', f'{np.median(nuplan_dens):.1f}', f'{np.median(gen_dens):.1f}'],
        ['Init. Speed (m/s)', f'{np.median(nuplan_speeds):.1f}', f'{np.median(gen_speeds):.1f}'],
        ['Accel. (m/s²)', f'{np.median(nuplan_acc):.2f}', f'{np.median(gen_acc):.2f}'],
        ['Decel. (m/s²)', f'{np.median(nuplan_deacc):.2f}', f'{np.median(gen_deacc):.2f}'],
        ['Follow Dist. (m)', f'{np.median(nuplan_follow):.1f}', f'{np.median(gen_follow):.1f}'],
    ]
    
    table = ax6.table(cellText=summary_data[1:], colLabels=summary_data[0],
                      loc='center', cellLoc='center',
                      colColours=[COLORS['light_fill']]*3)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    
    ax6.set_title('(f) Median Statistics', pad=20)
    
    plt.savefig(output_dir / 'nuplan_calibration_comparison.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'nuplan_calibration_comparison.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    print("Created: nuplan_calibration_comparison.pdf")


def create_scenario_diversity_figure(df, output_dir):
    """
    Create a figure showing scenario diversity across multiple axes.
    """
    fig = plt.figure(figsize=(14, 5))
    gs = GridSpec(1, 4, figure=fig, wspace=0.3)
    
    # 1. Sign family distribution
    ax1 = fig.add_subplot(gs[0, 0])
    
    family_counts = df['_sign_family'].value_counts()
    
    # Group into categories
    categories = {
        'Priority': ['main_road', 'secondary_road', 'stop', 'yield', 'roundabout'],
        'Direction': ['direction_left', 'direction_right', 'direction_straight', 
                     'direction_left_right', 'direction_straight_left', 'direction_straight_right',
                     'one_way_left', 'one_way_right'],
        'Prohibition': ['no_entry', 'no_turn_left', 'no_turn_right', 'blocked_road'],
        'Speed': ['speed_limit'],
        'Special': ['crosswalk', 'detour_right'],
    }
    
    cat_counts = {}
    for cat, signs in categories.items():
        cat_counts[cat] = sum(family_counts.get(s, 0) for s in signs)
    
    colors = [CATEGORY_COLORS[i] for i in range(len(cat_counts))]
    wedges, texts, autotexts = ax1.pie(cat_counts.values(), labels=cat_counts.keys(),
                                        autopct='%1.0f%%', colors=colors,
                                        pctdistance=0.75, labeldistance=1.15)
    
    for autotext in autotexts:
        autotext.set_fontsize(8)
    
    ax1.set_title('Sign Category\nDistribution')
    
    # 2. Traffic density levels
    ax2 = fig.add_subplot(gs[0, 1])
    
    density_levels = df['density_level_name'].value_counts()
    density_order = ['sparse', 'typical', 'dense']
    density_vals = [density_levels.get(d, 0) for d in density_order]
    
    bars = ax2.bar(density_order, density_vals, color=[COLORS['primary'], COLORS['tertiary'], COLORS['secondary']])
    ax2.set_xlabel('Density Level')
    ax2.set_ylabel('Number of Scenarios')
    ax2.set_title('Traffic Density\nDistribution')
    
    # Add percentages
    total = sum(density_vals)
    for bar, val in zip(bars, density_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{val/total*100:.0f}%', ha='center', fontsize=9)
    
    # 3. Route length distribution
    ax3 = fig.add_subplot(gs[0, 2])
    
    route_lengths = df['route_length_level_m'].dropna().values
    
    ax3.hist(route_lengths, bins=20, color=COLORS['primary'], 
             edgecolor='white', linewidth=0.5, alpha=0.8)
    ax3.axvline(np.median(route_lengths), color=COLORS['secondary'], 
                linestyle='--', lw=2, label=f'Median: {np.median(route_lengths):.0f}m')
    ax3.set_xlabel('Route Length (m)')
    ax3.set_ylabel('Number of Scenarios')
    ax3.set_title('Route Length\nDistribution')
    ax3.legend(loc='upper right', frameon=False)
    
    # 4. Train/Test split by sign
    ax4 = fig.add_subplot(gs[0, 3])
    
    split_data = df.groupby(['_sign_family', '_split']).size().unstack(fill_value=0)
    
    # Show only unique sign families
    top_signs = df['_sign_family'].value_counts().head(10).index.tolist()
    split_data = split_data.loc[split_data.index.isin(top_signs)]
    
    x = np.arange(len(split_data))
    width = 0.35
    
    bars1 = ax4.barh(x - width/2, split_data['train'], width, label='Train', color=COLORS['primary'])
    bars2 = ax4.barh(x + width/2, split_data['test'], width, label='Test', color=COLORS['secondary'])
    
    ax4.set_yticks(x)
    ax4.set_yticklabels([s.replace('_', '\n') for s in split_data.index], fontsize=7)
    ax4.set_xlabel('Number of Scenarios')
    ax4.set_title('Train/Test Split\nby Sign Type')
    ax4.legend(loc='lower right', frameon=False)
    ax4.invert_yaxis()
    
    plt.savefig(output_dir / 'scenario_diversity.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'scenario_diversity.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    print("Created: scenario_diversity.pdf")


def create_geographic_diversity_figure(df, output_dir):
    """
    Create a figure showing geographic coverage of map crops.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 1. Geographic scatter (Moscow)
    ax1 = axes[0]
    
    lats = df['latitude'].dropna().values
    lons = df['longitude'].dropna().values
    
    # Remove outliers
    lat_mask = (lats > 55.5) & (lats < 56.1)
    lon_mask = (lons > 37.2) & (lons < 38.0)
    mask = lat_mask & lon_mask
    
    lats_clean = lats[mask]
    lons_clean = lons[mask]
    
    # Create density heatmap
    from scipy.stats import gaussian_kde
    
    if len(lats_clean) > 100:
        xy = np.vstack([lons_clean, lats_clean])
        z = gaussian_kde(xy)(xy)
        
        # Sort by density for proper layering
        idx = z.argsort()
        lons_sorted, lats_sorted, z_sorted = lons_clean[idx], lats_clean[idx], z[idx]
        
        scatter = ax1.scatter(lons_sorted, lats_sorted, c=z_sorted, s=5, 
                             cmap='YlOrRd', alpha=0.7)
        plt.colorbar(scatter, ax=ax1, label='Density', shrink=0.8)
    else:
        ax1.scatter(lons_clean, lats_clean, s=5, color=COLORS['primary'], alpha=0.5)
    
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.set_title('Geographic Distribution of Map Crops\n(Moscow Region)')
    
    # Add Moscow center marker
    ax1.scatter([37.6173], [55.7558], marker='*', s=200, c='black', 
               label='Moscow Center', zorder=10)
    ax1.legend(loc='upper left', frameon=True)
    
    # 2. Unique maps per sign family
    ax2 = axes[1]
    
    unique_maps = df.groupby('_sign_family')['scene_name'].nunique().sort_values(ascending=True)
    
    colors = [COLORS['primary'] if i % 2 == 0 else COLORS['tertiary'] 
              for i in range(len(unique_maps))]
    
    bars = ax2.barh(range(len(unique_maps)), unique_maps.values, color=colors)
    ax2.set_yticks(range(len(unique_maps)))
    ax2.set_yticklabels([s.replace('_', ' ').title() for s in unique_maps.index], fontsize=8)
    ax2.set_xlabel('Number of Unique Maps')
    ax2.set_title('Map Diversity per Sign Type')
    
    # Add total count
    total_unique = df['scene_name'].nunique()
    ax2.text(0.95, 0.05, f'Total unique maps: {total_unique}', transform=ax2.transAxes,
            ha='right', fontsize=9, style='italic')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'geographic_diversity.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'geographic_diversity.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    print("Created: geographic_diversity.pdf")


def create_augmentation_coverage_figure(df, output_dir):
    """
    Create a figure showing how augmentation creates diverse scenarios.
    """
    fig = plt.figure(figsize=(12, 4))
    gs = GridSpec(1, 3, figure=fig, wspace=0.35)
    
    # 1. Spawn lane distribution
    ax1 = fig.add_subplot(gs[0, 0])
    
    lane_counts = df['spawn_lane_num'].value_counts().sort_index()
    
    ax1.bar(lane_counts.index, lane_counts.values, color=COLORS['primary'], 
            edgecolor='white', linewidth=0.5)
    ax1.set_xlabel('Spawn Lane Index')
    ax1.set_ylabel('Number of Scenarios')
    ax1.set_title('(a) Spawn Lane Variation')
    ax1.set_xticks(lane_counts.index)
    
    # 2. Speed percentile distribution
    ax2 = fig.add_subplot(gs[0, 1])
    
    speed_levels = df['spawn_velocity_level_id'].value_counts().sort_index()
    level_names = ['25th %ile', '50th %ile', '75th %ile']
    
    colors_speed = [COLORS['tertiary'], COLORS['quaternary'], COLORS['secondary']]
    ax2.bar(range(len(speed_levels)), speed_levels.values, 
            color=colors_speed[:len(speed_levels)], edgecolor='white', linewidth=0.5)
    ax2.set_xlabel('Speed Percentile Level')
    ax2.set_ylabel('Number of Scenarios')
    ax2.set_title('(b) Initial Speed Variation')
    ax2.set_xticks(range(len(speed_levels)))
    ax2.set_xticklabels(level_names[:len(speed_levels)])
    
    # 3. Density percentile distribution  
    ax3 = fig.add_subplot(gs[0, 2])
    
    density_percs = df['density_percentile'].value_counts().sort_index()
    
    colors_dens = [COLORS['primary'], COLORS['tertiary'], COLORS['secondary']]
    ax3.bar(range(len(density_percs)), density_percs.values, 
            color=colors_dens[:len(density_percs)], edgecolor='white', linewidth=0.5)
    ax3.set_xlabel('Traffic Density Percentile')
    ax3.set_ylabel('Number of Scenarios')
    ax3.set_title('(c) Traffic Density Variation')
    ax3.set_xticks(range(len(density_percs)))
    ax3.set_xticklabels([f'{p}th' for p in density_percs.index])
    
    plt.savefig(output_dir / 'augmentation_coverage.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'augmentation_coverage.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    print("Created: augmentation_coverage.pdf")


def create_summary_table(df, nuplan_data, output_dir):
    """Generate LaTeX summary table."""
    
    # Calculate statistics
    stats_dict = {
        'Total Scenarios': len(df),
        'Training Scenarios': len(df[df['_split'] == 'train']),
        'Test Scenarios': len(df[df['_split'] == 'test']),
        'Unique Map Crops': df['scene_name'].nunique(),
        'Sign Types': df['_sign_family'].nunique(),
        'Avg Background Vehicles': f"{df['nuplan_vehicles_per_frame'].mean():.1f}",
        'Avg Initial Speed (m/s)': f"{df['spawn_velocity_ms'].mean():.1f}",
        'Avg Route Length (m)': f"{df['route_length_level_m'].mean():.0f}",
    }
    
    # Write to file
    with open(output_dir / 'scene_summary_stats.txt', 'w') as f:
        f.write("=" * 50 + "\n")
        f.write("TrafficRuleBench Scene Statistics Summary\n")
        f.write("=" * 50 + "\n\n")
        
        for key, val in stats_dict.items():
            f.write(f"{key:30s}: {val}\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write("Distribution Alignment (nuPlan vs Generated)\n")
        f.write("=" * 50 + "\n\n")
        
        # KS tests
        nuplan_dens = nuplan_data['densities'][nuplan_data['densities'] > 0]
        gen_dens = df['nuplan_vehicles_per_frame'].dropna().values
        gen_dens = gen_dens[gen_dens > 0]
        
        ks_stat, ks_pval = stats.ks_2samp(nuplan_dens[:10000], gen_dens)
        f.write(f"Traffic Density KS statistic: {ks_stat:.4f}\n")
        
        nuplan_speeds = nuplan_data['initial_speeds']
        gen_speeds = df['spawn_velocity_ms'].dropna().values
        ks_stat2, _ = stats.ks_2samp(nuplan_speeds, gen_speeds)
        f.write(f"Initial Speed KS statistic: {ks_stat2:.4f}\n")
    
    # Generate LaTeX table
    latex_content = r"""
\begin{table}[t]
\centering
\caption{Generated Scene Statistics}
\label{tab:scene_stats}
\begin{tabular}{lr}
\toprule
\textbf{Metric} & \textbf{Value} \\
\midrule
Total Scenarios & %s \\
Training / Test & %s / %s \\
Unique Map Crops & %s \\
Sign Types & %s \\
\midrule
Avg. Background Vehicles & %s \\
Avg. Initial Speed (m/s) & %s \\
Avg. Route Length (m) & %s \\
\bottomrule
\end{tabular}
\end{table}
""" % (
        f"{stats_dict['Total Scenarios']:,}",
        f"{stats_dict['Training Scenarios']:,}",
        f"{stats_dict['Test Scenarios']:,}",
        f"{stats_dict['Unique Map Crops']:,}",
        stats_dict['Sign Types'],
        stats_dict['Avg Background Vehicles'],
        stats_dict['Avg Initial Speed (m/s)'],
        stats_dict['Avg Route Length (m)'],
    )
    
    with open(output_dir / 'scene_summary_table.tex', 'w') as f:
        f.write(latex_content)
    
    print("Created: scene_summary_stats.txt, scene_summary_table.tex")


def create_compact_nuplan_figure(df, nuplan_data, output_dir):
    """
    Create a compact 2x2 figure for the main paper (limited space).
    This is the PRIMARY figure for the paper.
    """
    fig, axes = plt.subplots(2, 2, figsize=(8, 6))
    
    # Common settings
    alpha_hist = 0.6
    lw_kde = 2
    
    # 1. Traffic Density (top-left) - KEY metric
    ax = axes[0, 0]
    nuplan_dens = nuplan_data['densities']
    nuplan_dens = nuplan_dens[nuplan_dens > 0][:50000]  # Sample for speed
    gen_dens = df['nuplan_vehicles_per_frame'].dropna().values
    gen_dens = gen_dens[gen_dens > 0]
    
    bins = np.linspace(0, 70, 35)
    ax.hist(nuplan_dens, bins=bins, density=True, alpha=alpha_hist, 
            color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.3)
    ax.hist(gen_dens, bins=bins, density=True, alpha=alpha_hist, 
            color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.3)
    
    ax.set_xlabel('Vehicles within 150m')
    ax.set_ylabel('Density')
    ax.set_title('(a) Traffic Density')
    ax.legend(loc='upper right', frameon=False, fontsize=8)
    ax.set_xlim(0, 70)
    
    # 2. Initial Speed (top-right)
    ax = axes[0, 1]
    nuplan_speeds = nuplan_data['initial_speeds']
    gen_speeds = df['spawn_velocity_ms'].dropna().values
    
    bins = np.linspace(0, 18, 25)
    ax.hist(nuplan_speeds, bins=bins, density=True, alpha=alpha_hist, 
            color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.3)
    ax.hist(gen_speeds, bins=bins, density=True, alpha=alpha_hist, 
            color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.3)
    
    ax.set_xlabel('Initial Speed (m/s)')
    ax.set_ylabel('Density')
    ax.set_title('(b) Initial Ego Speed')
    ax.legend(loc='upper right', frameon=False, fontsize=8)
    ax.set_xlim(0, 18)
    
    # 3. Following Distance (bottom-left)
    ax = axes[1, 0]
    nuplan_follow = nuplan_data['following']
    gen_follow = df['profile_DISTANCE_WANTED'].dropna().values
    
    bins = np.linspace(0, 45, 30)
    nuplan_filt = nuplan_follow[(nuplan_follow > 0) & (nuplan_follow < 45)]
    gen_filt = gen_follow[(gen_follow > 0) & (gen_follow < 45)]
    
    ax.hist(nuplan_filt, bins=bins, density=True, alpha=alpha_hist, 
            color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.3)
    ax.hist(gen_filt, bins=bins, density=True, alpha=alpha_hist, 
            color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.3)
    
    ax.set_xlabel('Following Distance (m)')
    ax.set_ylabel('Density')
    ax.set_title('(c) IDM Following Distance')
    ax.legend(loc='upper right', frameon=False, fontsize=8)
    ax.set_xlim(0, 45)
    
    # 4. Acceleration (bottom-right)
    ax = axes[1, 1]
    nuplan_acc = nuplan_data['acc_pos']
    gen_acc = df['profile_ACC_FACTOR'].dropna().values
    
    bins = np.linspace(0, 3.5, 25)
    nuplan_filt = nuplan_acc[(nuplan_acc > 0) & (nuplan_acc < 3.5)]
    gen_filt = gen_acc[(gen_acc > 0) & (gen_acc < 3.5)]
    
    ax.hist(nuplan_filt, bins=bins, density=True, alpha=alpha_hist, 
            color=COLORS['nuplan'], label='nuPlan', edgecolor='white', linewidth=0.3)
    ax.hist(gen_filt, bins=bins, density=True, alpha=alpha_hist, 
            color=COLORS['generated'], label='Generated', edgecolor='white', linewidth=0.3)
    
    ax.set_xlabel('Acceleration (m/s²)')
    ax.set_ylabel('Density')
    ax.set_title('(d) IDM Acceleration')
    ax.legend(loc='upper right', frameon=False, fontsize=8)
    ax.set_xlim(0, 3.5)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'nuplan_comparison_compact.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'nuplan_comparison_compact.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    print("Created: nuplan_comparison_compact.pdf (MAIN PAPER FIGURE)")


def create_quantile_comparison_table(df, nuplan_data, output_dir):
    """
    Create a table comparing quantiles between nuPlan and generated data.
    """
    metrics = [
        ('Traffic Density', 'count_r150', 'nuplan_vehicles_per_frame'),
        ('Initial Speed (m/s)', 'initial_speeds', 'spawn_velocity_ms'),
        ('Following Dist. (m)', 'following', 'profile_DISTANCE_WANTED'),
        ('Acceleration (m/s²)', 'acc_pos', 'profile_ACC_FACTOR'),
        ('Deceleration (m/s²)', 'acc_neg', 'profile_DEACC_FACTOR'),
    ]
    
    quantiles = [0.25, 0.50, 0.75]
    
    rows = []
    for metric_name, nuplan_key, gen_key in metrics:
        if nuplan_key == 'count_r150':
            nuplan_vals = nuplan_data['densities']
        else:
            nuplan_vals = nuplan_data.get(nuplan_key, np.array([]))
        
        gen_vals = df[gen_key].dropna().values
        
        row = {'Metric': metric_name}
        for q in quantiles:
            qname = f'Q{int(q*100)}'
            row[f'nuPlan {qname}'] = f'{np.quantile(nuplan_vals, q):.2f}' if len(nuplan_vals) > 0 else 'N/A'
            row[f'Gen {qname}'] = f'{np.quantile(gen_vals, q):.2f}' if len(gen_vals) > 0 else 'N/A'
        
        rows.append(row)
    
    result_df = pd.DataFrame(rows)
    result_df.to_csv(output_dir / 'quantile_comparison.csv', index=False)
    
    # Also create LaTeX version
    latex = result_df.to_latex(index=False, escape=False)
    with open(output_dir / 'quantile_comparison.tex', 'w') as f:
        f.write(latex)
    
    print("Created: quantile_comparison.csv, quantile_comparison.tex")
    return result_df


def main():
    # Paths
    base_dir = Path('/home/jovyan/shares/SR006.nfs2/zinkovich/zinkovich/traffic-rule-bench')
    runs_dir = base_dir / 'data' / 'runs'
    nuplan_stats_dir = base_dir / 'traffic_bench' / 'eval' / 'engine' / 'traffic' / 'nuplan_statistics'
    output_dir = base_dir / 'scripts' / 'scene_analysis' / 'figures'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading scenario data...")
    df = load_all_scenarios(runs_dir)
    print(f"Loaded {len(df)} scenarios from {df['_sign_family'].nunique()} sign families")
    
    print("\nLoading nuPlan statistics...")
    nuplan_data = load_nuplan_statistics(nuplan_stats_dir)
    print(f"Loaded nuPlan data: {len(nuplan_data['densities'])} density samples, "
          f"{len(nuplan_data['speeds'])} speed samples")
    
    print("\n" + "="*60)
    print("Generating figures...")
    print("="*60 + "\n")
    
    # Generate all figures
    create_compact_nuplan_figure(df, nuplan_data, output_dir)
    create_nuplan_comparison_figure(df, nuplan_data, output_dir)
    create_scenario_diversity_figure(df, output_dir)
    create_geographic_diversity_figure(df, output_dir)
    create_augmentation_coverage_figure(df, output_dir)
    create_summary_table(df, nuplan_data, output_dir)
    
    print("\nCreating quantile comparison table...")
    qtable = create_quantile_comparison_table(df, nuplan_data, output_dir)
    print(qtable.to_string())
    
    print("\n" + "="*60)
    print(f"All figures saved to: {output_dir}")
    print("="*60)


if __name__ == '__main__':
    main()
