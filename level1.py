import pandas as pd
import plotly.graph_objects as go

INPUT = "temperature_daily.csv"
OUTPUT = "level1.html"

LABEL_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]



#Load raw data
def load_records(filepath: str):
    #Read CSV file and add Year and Month columns, returning one row per calendar day
    df = pd.read_csv(filepath, parse_dates = ["date"])

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    return df


#Aggregate by month
def aggregate_by_month(dailyDF: pd.DataFrame):
    monthly = (dailyDF.groupby(["year", "month"], as_index = False).agg(month_max = ("max_temperature", "max"), month_min = ("min_temperature", "min")))

    monthly["label"] = (monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2))

    return monthly

#Reshape for heatmap
def matrix_pivot(monthlyDF: pd.DataFrame, value_col: str):
    #Pivot monthly DataFrame into 2D list
    years_sorted = sorted(monthlyDF["year"].unique())

    #Guarantee a row for every month and a column for every year
    pivot = (monthlyDF.pivot_table(index = "month", columns = "year", values = value_col).reindex(index = range(1, 13)).reindex(columns = years_sorted))

    return pivot.values.tolist(), years_sorted

def build_tool_customdata(monthlyDF: pd.DataFrame, years_sorted: list):
    #Make an array where each innermost list holds [date_label, month_max, month_min] so tool always shows both max and min
    cell_lookup = {}

    for col, row in monthlyDF.iterrows():
        key = (int(row["year"]), int(row["month"]))

        cell_lookup[key] = (row["label"], int(row["month_max"]), int(row["month_min"]))

    customdata = []

    for monthNum in range(1, 13):
        row_data = []
        for year in years_sorted:
            entry = cell_lookup.get((year, monthNum), ("", None, None))
            row_data.append(list(entry))

        customdata.append(row_data)

    return customdata

#Make figure components
def make_heatmap(z_matrix: list, years_sorted: list, customdata: list):
    #Create the Plotly heatmap trace with a hover tool that shows the date, max, and min

    return go.Heatmap(z = z_matrix, x = years_sorted, y = LABEL_MONTHS, colorscale = "YlOrRd", customdata = customdata, zmin = 10, zmax = 37, hovertemplate = ("Date: %{customdata[0]}, Max: %{customdata[1]}, Min: %{customdata[2]}<extra></extra>"), xgap = 3, ygap = 3, colorbar = dict(thickness = 16, title = dict(text = "°C", side = "top"), tickformat = ".0f"))

def make_toggle_buttons(max_matrix: list, min_matrix: list):
    #Add two buttons above the chart to restyle chart and see Max temp or Min temp without reloading the page

    return dict(type = "buttons", direction = "right", x = 0.0, y = 1.12, xanchor = "left", yanchor = "bottom", bgcolor = "#f0f0f0", bordercolor = "#bbb", borderwidth = 1, font = dict(size = 13), showactive = True, buttons = [dict(label = "Max Temperature", method = "restyle", args = [{"z": [max_matrix]}]), dict(label = "Min Temperature", method = "restyle", args = [{"z": [min_matrix]}])])

def make_layout(years_sorted: list, toggle_buttons: dict):
    #Create chart layout with axes, title, margins, and buttons

    return go.Layout(title = dict(text = "Hong Kong Monthly Temperature Heatmap", font = dict(size = 15), x = 0.5, xanchor = "center"), xaxis = dict(side = "top", tickmode = "array", tickvals = years_sorted, ticktext = [str(y) for y in years_sorted], tickfont = dict(size = 11), showgrid = False, zeroline = False), yaxis = dict(autorange = "reversed", tickfont = dict(size = 11), showgrid = False, zeroline = False), updatemenus = [toggle_buttons], margin = dict(t = 110, l = 110, r = 100, b = 20), plot_bgcolor = "white", paper_bgcolor = "white")

def main():
    #Load data and collapse to monthly summaries
    dailyDF = load_records(INPUT)
    monthlyDF = aggregate_by_month(dailyDF)

    #Make 2D matrices for min/max temps
    max_matrix, years_sorted = matrix_pivot(monthlyDF, "month_max")
    min_matrix, ignore = matrix_pivot(monthlyDF, "month_min")

    customdata = build_tool_customdata(monthlyDF, years_sorted)
    heatmap = make_heatmap(max_matrix, years_sorted, customdata)
    toggle_buttons = make_toggle_buttons(max_matrix, min_matrix)

    #Assemble figure
    fig = go.Figure(data = [heatmap], layout = make_layout(years_sorted, toggle_buttons))

    fig.write_html(OUTPUT, include_plotlyjs = "cdn")
    print(f"Saved -> {OUTPUT}")

if __name__ == "__main__":
    main()