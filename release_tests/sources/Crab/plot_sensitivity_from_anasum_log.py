"""Plot sensitivity diagnostics from anasum log files.

Reads anasum log files from an input directory and writes a PNG summary figure.

Usage: python plot_sensitivity_from_anasum_log.py [input_dir] [output_png]
"""

import argparse
import glob
import os
import re

import matplotlib.pyplot as plt
import numpy as np

# Parse input directory argument
parser = argparse.ArgumentParser(description="Plot sensitivity metrics from anasum log files.")
parser.add_argument(
    "input_dir",
    nargs="?",
    default=".",
    help="Directory containing anasum log files (default: current directory)",
)
parser.add_argument(
    "output_png",
    nargs="?",
    default="anasum_analysis_plots.png",
    help="Output PNG filename (default: anasum_analysis_plots.png)",
)
args = parser.parse_args()

if not os.path.isdir(args.input_dir):
    raise SystemExit(f"Input directory does not exist: {args.input_dir}")

log_files = sorted(glob.glob(os.path.join(args.input_dir, "*anasum*.log")))

if not log_files:
    raise SystemExit(f"No anasum log files found in: {args.input_dir}")

epochs = []
on_off_summary_rates = []
off_summary_rates = []
crab_001_times = []
all_elevations = []
all_on_rates = []
all_off_rates = []

for filepath in log_files:
    with open(filepath, "r") as f:
        content = f.read()

        # Extract epoch from filename (e.g., V6_2023_2023s_ATM62 or V6_2014_2015_ATM61)
        basename = os.path.basename(filepath)
        epoch_match = re.search(r"(V6_[^_]+_\d+[a-z]*)_ATM\d+", basename)
        if not epoch_match:
            # Try alternative pattern for ATM61 files
            epoch_match = re.search(
                r"(V6_[^_]+_\d+[a-z]*)_ATM\d+", basename.replace("_SZE_0.5deg.combined", "")
            )
        if not epoch_match:
            continue
        epoch = epoch_match.group(1)

        # Extract summary on/off rates
        rate_match = re.search(r"Rates \(on/Off\): (\d+\.\d+)\s+(\d+\.\d+)", content)

        # Extract 0.01 Crab time in hours from the sensitivity table
        lines = content.split("\n")
        crab_time = None
        in_table = False
        for line in lines:
            if "[h]" in line:
                in_table = True
                continue
            if in_table and line.strip().startswith("0.01"):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        crab_time = float(parts[-1])
                    except ValueError:
                        pass
                break

        # Extract all elevation and rate values from RUN lines
        el_values = []
        on_rates = []
        off_rates = []
        for line in lines:
            el_match = re.search(r"RUN\s+\d+.*at\s+(\d+),\s+(-?\d+)\s+deg\s+El\.,\s+Az", line)
            rate_match_line = re.search(r"Rates:\s+([\d.]+).*background:\s+([\d.]+)", line)
            if el_match:
                el_values.append(int(el_match.group(1)))
            if rate_match_line:
                on_rates.append(float(rate_match_line.group(1)))
                off_rates.append(float(rate_match_line.group(2)))

        # Only add data if we have all values and non-empty arrays
        if rate_match and crab_time is not None and el_values and on_rates and off_rates:
            epochs.append(epoch)
            on_off_summary_rates.append(float(rate_match.group(1)))
            off_summary_rates.append(float(rate_match.group(2)))
            crab_001_times.append(crab_time)
            all_elevations.append(np.array(el_values))
            all_on_rates.append(np.array(on_rates))
            all_off_rates.append(np.array(off_rates))

# Calculate average elevation per epoch for sensitivity plot
avg_elevations = [np.mean(el) for el in all_elevations]

# Create plots - 4 rows: 2x2 + 2 extra
fig, axs = plt.subplots(4, 2, figsize=(14, 20))

# Plot 1: On Rate vs Epoch
axs[0, 0].plot(epochs, on_off_summary_rates, "o-", color="blue")
axs[0, 0].set_xlabel("Epoch")
axs[0, 0].set_ylabel("On Rate")
axs[0, 0].set_title("On Rate vs Epoch")
axs[0, 0].tick_params(axis="x", rotation=45)

# Plot 2: Off Rate vs Epoch
axs[0, 1].plot(epochs, off_summary_rates, "s-", color="orange")
axs[0, 1].set_xlabel("Epoch")
axs[0, 1].set_ylabel("Off Rate")
axs[0, 1].set_title("Off Rate vs Epoch")
axs[0, 1].tick_params(axis="x", rotation=45)

# Plot 3: Violin plot of Elevations per Epoch
axs[1, 0].violinplot(all_elevations, positions=range(len(epochs)), widths=0.8, showmeans=True)
axs[1, 0].set_xticks(range(len(epochs)))
axs[1, 0].set_xticklabels(epochs, rotation=45, ha="right")
axs[1, 0].set_xlabel("Epoch")
axs[1, 0].set_ylabel("Elevation [deg]")
axs[1, 0].set_title("Elevation Distribution per Epoch")

# Plot 4: Violin plot of On Rates per Epoch
axs[1, 1].violinplot(all_on_rates, positions=range(len(epochs)), widths=0.8, showmeans=True)
axs[1, 1].set_xticks(range(len(epochs)))
axs[1, 1].set_xticklabels(epochs, rotation=45, ha="right")
axs[1, 1].set_xlabel("Epoch")
axs[1, 1].set_ylabel("On Rate")
axs[1, 1].set_title("On Rate Distribution per Epoch")

# Plot 5: Violin plot of Off Rates per Epoch
axs[2, 0].violinplot(all_off_rates, positions=range(len(epochs)), widths=0.8, showmeans=True)
axs[2, 0].set_xticks(range(len(epochs)))
axs[2, 0].set_xticklabels(epochs, rotation=45, ha="right")
axs[2, 0].set_xlabel("Epoch")
axs[2, 0].set_ylabel("Off Rate")
axs[2, 0].set_title("Off Rate Distribution per Epoch")

# Plot 6: 0.01 Crab Sensitivity Time vs Epoch
axs[2, 1].plot(epochs, crab_001_times, "s-", color="purple")
axs[2, 1].set_xlabel("Epoch")
axs[2, 1].set_ylabel("0.01 Crab Time [h]")
axs[2, 1].set_title("0.01 Crab Sensitivity Time vs Epoch")
axs[2, 1].tick_params(axis="x", rotation=45)

# Plot 7: Sensitivity vs Average Elevation
# Color points red if epoch year >= 2020
colors = [
    (
        "red"
        if "2020" in epoch
        or "2021" in epoch
        or "2022" in epoch
        or "2023" in epoch
        or "2024" in epoch
        or "2025" in epoch
        or "2026" in epoch
        else "blue"
    )
    for epoch in epochs
]
axs[3, 0].scatter(avg_elevations, crab_001_times, c=colors, alpha=0.7)
axs[3, 0].set_xlabel("Average Elevation [deg]")
axs[3, 0].set_ylabel("0.01 Crab Time [h]")
axs[3, 0].set_title("Sensitivity vs Elevation")

# Hide the empty subplot
axs[3, 1].axis("off")

plt.tight_layout()
plt.savefig(args.output_png, dpi=300, bbox_inches="tight")
print(f"Processed {len(epochs)} files. Plots saved as {args.output_png}")
