import pandas as pd
import plotly.graph_objects as go

INPUT = "temperature_daily.csv"
OUTPUT = "level2.html"

RECENT_YEARS = 10

COLOR_SCALE = [[0, "#313695"], [0.1, "#4575b4"], [0.25, "#74add1"], [0.4, "#abd9e9"], [0.5, "#ffffbf"], [0.65, "#fee090"], [0.75, "#fdae61"], [0.87, "#f46d43"], [1, "#a50026"]]

LABEL_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

#Map a day index to x coordinate that is inside cell_col column in the heatmap
def day_x(day_ind: int, totalDays: int, cell_col: int):
    fraction = day_ind / max(totalDays - 1, 1)

    return (cell_col - 0.44) + fraction * (2 * 0.44)

#Map a temperature val to y coordinate that is inside cell_row row in the heatmap
def temp_y(temp: float, tLow: float, tHigh: float, cell_row: int):
    if tHigh == tLow:
        fraction = 0.5
    else:
        fraction = (temp - tLow) / (tHigh - tLow)

    return (cell_row + 0.44) - fraction * (2 * 0.44)

#Load raw data
def load_records(filepath: str):
    #Read CSV file and add Year, Month, and Day columns
    df = pd.read_csv(filepath, parse_dates = ["date"])

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day

    return df

#Filter recent years
def filter_recent_years(dailyDF: pd.DataFrame, n: int):
    years = sorted(dailyDF["year"].unique())
    recent_years = years[-n:]

    return dailyDF[dailyDF["year"].isin(recent_years)].copy()

#Aggregate by month by collapsing daily records into one summary row per (year, month)
def aggregate_by_month(dailyDF: pd.DataFrame):
    dailyDF = dailyDF.copy()
    dailyDF["daily_avg"] = (dailyDF["max_temperature"] + dailyDF["min_temperature"]) / 2

    monthly = (dailyDF.groupby(["year", "month"], as_index = False).agg(month_max = ("max_temperature", "max"), month_min = ("min_temperature", "min"), month_avg = ("daily_avg", "mean")))

    monthly["label"] = (monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2))
    return monthly

def make_heatmap_matrix(monthlyDF: pd.DataFrame, years_sorted: list):
    
    lookup = {}

    for col, row in monthlyDF.iterrows():
        key = (int(row["year"]), int(row["month"]))

        lookup[key] = {"label": row["label"], "month_max": int(row["month_max"]), "month_min": int(row["month_min"]), "month_avg": float(row["month_avg"])}

    avg_matrix = []
    customdata = []

    for monthNum in range(1, 13):
        avg_row = []
        info_row = []
        for year in years_sorted:
            r = lookup.get((year, monthNum))

            if r is not None:
                avg_row.append(float(r["month_avg"]))
                info_row.append([r["label"], int(r["month_max"]), int(r["month_min"])])
            else:
                avg_row.append(None)
                info_row.append(["", None, None])

        avg_matrix.append(avg_row)
        customdata.append(info_row)

    return avg_matrix, customdata


def build_mini_line_data(recentDF: pd.DataFrame, years_sorted: list):
    #Iterate over every cell and compute normalized x/y coords for both max and min temperature lines
    max_x = []
    max_y = []
    max_text = []

    min_x = []
    min_y = []
    min_text = []

    for month_ind in range(12):
        for year_ind, year in enumerate(years_sorted):
            #Pull daily data for the specific cell, sorted by day

            cellDF = (recentDF[(recentDF["year"] == year) & (recentDF["month"] == month_ind + 1)].sort_values("day"))

            if len(cellDF) == 0:
                continue

            #Tool text for every point in the cell
            mmax = int(cellDF["max_temperature"].max())
            mmin = int(cellDF["min_temperature"].min())
            label = f"{year}-{str(month_ind + 1).zfill(2)}"
            tip = f"Date: {label}, Max: {mmax}, Min: {mmin}"

            #Temperature range for y-axis normalization inside the cell
            temp_low = cellDF["min_temperature"].min() - 1
            temp_high = cellDF["max_temperature"].max() + 1

            n_days = len(cellDF)

            #Compute normalized coords for each day in the month
            xs = []
            y_max = []
            y_min = []

            for i in range(n_days):
                xs.append(day_x(i, n_days, year_ind))

            for t in cellDF["max_temperature"]:
                y_max.append(temp_y(t, temp_low, temp_high, month_ind))

            for t in cellDF["min_temperature"]:
                y_min.append(temp_y(t, temp_low, temp_high, month_ind))

            #Append cell data
            max_x += xs + [None]
            min_x += xs + [None]
            max_y += y_max + [None]
            min_y += y_min + [None]
            max_text += [tip] * n_days + [None]
            min_text += [tip] * n_days + [None]

    return max_x, min_x, max_y, min_y, max_text, min_text

#Assemble components
def build_figure(avg_matrix: list, customdata: list, years_sorted: list, max_x, min_x, max_y, min_y, max_text, min_text):
    #Create the heatmap, then include both the daily max lines in green and daily min lines in silver

    fig = go.Figure()

    #Create heatmap
    fig.add_trace(go.Heatmap(z = avg_matrix, x = list(range(len(years_sorted))), y = list(range(12)), colorscale = COLOR_SCALE, zmin = 0, zmax = 40, customdata = customdata, hovertemplate = ("Date: %{customdata[0]}, Max: %{customdata[1]}, Min: %{customdata[2]}<extra></extra>"), xgap = 4, ygap = 4, colorbar = dict(thickness = 16, tickvals = [0, 10, 20, 30, 40], ticktext = ["0°C", "10°C", "20°C", "30°C", "40°C"], title = dict(text = "", side = "top"))))

    #Daily max temperature lines in green
    fig.add_trace(go.Scatter(x = max_x, y = max_y, mode = "lines", line = dict(color = "#2ecc40", width = 1.3), text = max_text, hovertemplate = "%{text}<extra></extra>", showlegend = False))

    #Daily min temperature lines in silver
    fig.add_trace(go.Scatter(x = min_x, y = min_y, mode = "lines", line = dict(color = "rgba(200, 200, 220, 0.85)", width = 1.3), text = min_text, hovertemplate = "%{text}<extra></extra>", showlegend = False))

    #Layout
    num_years = len(years_sorted)

    fig.update_layout(title = dict(text = "Hong Kong Monthly Temperature - Daily Detail", font = dict(size = 15), x = 0.5, xanchor = "center"), xaxis = dict(side = "top", tickmode = "array", tickvals = list(range(num_years)), ticktext = [str(y) for y in years_sorted], tickfont = dict(size = 11), range = [-0.5, num_years - 0.5], showgrid = False, zeroline = False), yaxis = dict(autorange = "reversed", tickmode = "array", tickvals = list(range(12)), ticktext = LABEL_MONTHS, tickfont = dict(size = 11), range = [-0.5, 11.5], showgrid = False, zeroline = False), margin = dict(t = 110, l = 110, r = 120, b = 20), plot_bgcolor = "white", paper_bgcolor = "white", hovermode = "closest")

    return fig


def main():
    #Load data and keep most recent n years
    dailyDF = load_records(INPUT)
    recentDF = filter_recent_years(dailyDF, RECENT_YEARS)

    #Make monthly summaries for heatmap, then build heatmap and customdata tool
    monthlyDF = aggregate_by_month(recentDF)
    years_sorted = sorted(monthlyDF["year"].unique())

    avg_matrix, customdata = make_heatmap_matrix(monthlyDF, years_sorted)

    #Build mini line chart coord data, then create and save figure
    max_x, min_x, max_y, min_y, max_text, min_text = build_mini_line_data(recentDF, years_sorted)

    fig = build_figure(avg_matrix, customdata, years_sorted, max_x, min_x, max_y, min_y, max_text, min_text)
    fig.write_html(OUTPUT, include_plotlyjs = "cdn")

    print(f"Saved -> {OUTPUT}")

if __name__ == "__main__":
    main()