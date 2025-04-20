import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
df = pd.read_csv("batch_results/results_20250420_155417.csv")  # Replace with your actual file name

# Create a column for number of robots (same for green/yellow/red)
df["num_robots"] = df["num_green"]

# 1. Win Rate vs Number of Robots (per Heuristic)
plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x="num_robots", y="win_rate", hue="heuristic", style="green_waste", markers=True, dashes=False)
plt.title("Win Rate vs Number of Robots")
plt.xlabel("Number of Robots")
plt.ylabel("Win Rate")
plt.legend(title="Heuristic / Waste")
plt.grid(True)
plt.tight_layout()
plt.savefig("plot_1_winrate_vs_robots.png")
plt.show()

# 2. Total Distance vs Number of Robots
plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x="num_robots", y="avg_total_distance", hue="heuristic", style="green_waste", markers=True)
plt.title("Average Total Distance vs Number of Robots")
plt.xlabel("Number of Robots")
plt.ylabel("Average Total Distance")
plt.legend(title="Heuristic / Waste")
plt.grid(True)
plt.tight_layout()
plt.savefig("plot_2_distance_vs_robots.png")
plt.show()

# 3. Scatter Plot: Steps vs Total Distance
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=df,
    x="avg_steps_to_finish",
    y="avg_total_distance",
    hue="heuristic",
    size="num_robots",
    style="green_waste",
    sizes=(50, 200)
)
plt.title("Steps vs Total Distance (System Efficiency)")
plt.xlabel("Average Steps to Finish")
plt.ylabel("Average Total Distance")
plt.legend(title="Heuristic")
plt.grid(True)
plt.tight_layout()
plt.savefig("plot_3_steps_vs_distance.png")
plt.show()

# 4. Barplot: Average Win Rate per Heuristic
plt.figure(figsize=(8, 6))
sns.barplot(data=df, x="heuristic", y="win_rate", ci="sd")
plt.title("Average Win Rate per Heuristic")
plt.ylabel("Average Win Rate")
plt.xlabel("Heuristic")
plt.tight_layout()
plt.savefig("plot_4_barplot_winrate.png")
plt.show()

# 5. Heatmaps: Win Rate by Robots × Waste for each Heuristic
for heuristic in df["heuristic"].unique():
    pivot = df[df["heuristic"] == heuristic].pivot(
        index="green_waste", columns="num_robots", values="win_rate"
    )
    plt.figure(figsize=(6, 5))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu")
    plt.title(f"Win Rate Heatmap – {heuristic}")
    plt.xlabel("Number of Robots")
    plt.ylabel("Waste Amount")
    plt.tight_layout()
    plt.savefig(f"plot_5_heatmap_{heuristic}.png")
    plt.show()
