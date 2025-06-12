import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Data for the Gantt chart
tasks = [
    "Finalize problem & tech stack",
    "Collect datasets & setup APIs",
    "Preprocess images & apply NER",
    "Geocoding & MongoDB integration",
    "Train YOLOv8 & setup drone testing",
    "Model validation with drone data",
    "Build initial dashboard",
    "Integrate population & map data",
    "System integration & testing",
    "Prepare final report & presentation"
]

start_dates = [
    "2025-04-28", "2025-05-05", "2025-05-12", "2025-05-19", "2025-05-26",
    "2025-06-02", "2025-06-09", "2025-06-16", "2025-06-23", "2025-06-30"
]

end_dates = [
    "2025-05-03", "2025-05-10", "2025-05-17", "2025-05-25", "2025-05-31",
    "2025-06-07", "2025-06-14", "2025-06-21", "2025-06-28", "2025-07-05"
]

# Convert date strings to datetime objects
start_dates = [datetime.strptime(date, "%Y-%m-%d") for date in start_dates]
end_dates = [datetime.strptime(date, "%Y-%m-%d") for date in end_dates]

# Create a DataFrame
df = pd.DataFrame({
    "Task": tasks,
    "Start": start_dates,
    "End": end_dates
})

# Plotting
fig, ax = plt.subplots(figsize=(12, 6))
for i, (task, start, end) in enumerate(zip(df["Task"], df["Start"], df["End"])):
    ax.barh(task, (end - start).days, left=start, color='skyblue', edgecolor='black')

# Format x-axis
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
plt.xticks(rotation=45)
plt.title("Gantt Chart - Interdisciplinary Project Timeline")
plt.xlabel("Date")
plt.ylabel("Tasks")
plt.tight_layout()

plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.show()
