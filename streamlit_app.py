import json
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.ticker import FuncFormatter


def extract_json_value(df, column, selected_key):
    def extract_value(row):
        try:
            json_data = json.loads(row)
            return json_data[selected_key] if selected_key in json_data else None
        except (json.JSONDecodeError, KeyError):
            return None

    return df[column].apply(extract_value)


def dynamic_json_extraction(df):
    st.text("Extract item(s) from JSON Stats")

    selected_column = st.selectbox("Select column to extract from", df.columns)

    # Extract unique keys from the selected column
    unique_keys = set()
    for row in df[selected_column]:
        try:
            json_data = json.loads(row)
            unique_keys.update(json_data.keys())
        except Exception as ex:
            break

    # Allow the user to select multiple keys
    selected_keys = st.multiselect(
        "Select JSON Key(s) to extract", sorted(list(unique_keys))
    )
    if not selected_keys:
        st.warning("No keys selected. Please choose one or more keys for extract")
        return df

    # Extract the selected JSON keys and create new columns
    if selected_keys:
        if st.button("Extract"):
            # Extract the selected JSON keys and create new columns
            for key in selected_keys:
                new_column_name = f"{selected_column}_{key}"
                df[new_column_name] = extract_json_value(df, selected_column, key)
                st.success(f"Successfully extracted {key} from {selected_column}.")

        return df


# Function to plot the chart based on user selections
def plot_chart(df, x_column, y_columns, plot_type, title, chart_properties):
    fig, ax = plt.subplots(figsize=(12, 6))

    if plot_type == "line":
        for i, column in enumerate(y_columns):
            ax.plot(
                df[x_column],
                df[column],
                label=column,
                marker=chart_properties["marker"],
                linestyle=chart_properties["linestyle"],
            )
    elif plot_type == "bar":
        df.plot(
            x=x_column,
            y=y_columns,
            kind="bar",
            stacked=True,
            width=chart_properties["bar_width"],
            ax=ax,
        )
    elif plot_type == "scatter":
        for i, column in enumerate(y_columns):
            ax.scatter(
                df[x_column],
                df[column],
                label=column,
                marker=chart_properties["marker"],
            )

    ax.set_title(title)
    ax.set_xlabel(x_column)
    ax.set_ylabel("Values")
    ax.legend()

    return fig, ax


# Main Streamlit app
def main():
    # Placeholder for df

    df = pd.DataFrame()
    st.sidebar.title("OSMSG Stats Visualizer")
    st.sidebar.subheader("Choose Data")
    data_source = st.sidebar.radio(
        "Select data source", ("Upload CSV", "Use Sample Data")
    )

    if data_source == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
    else:
        # Use sample data
        df = pd.read_csv(
            "https://raw.githubusercontent.com/kshitijrajsharma/OSMSG/master/stats/turkeyeq/Daily/stats_summary.csv"
        )

    st.sidebar.title("Choose Chart Options")
    selected_columns = st.sidebar.multiselect("Select columns for chart", df.columns)

    if not selected_columns:
        st.warning("Please select at least one column for the chart.")
        st.stop()

    plot_type = st.sidebar.selectbox("Select chart type", ["line", "bar", "scatter"])

    # Ask user for chart title
    chart_title = st.text_input("Enter Chart Title", "My Customized Chart")
    show_table = st.sidebar.checkbox("Show Table", value=True)
    if "tags_create" in selected_columns or "tags_modify" in selected_columns:
        selected_key = st.sidebar.text_input("Enter JSON Key for Tags", "name")

        if "tags_create" in selected_columns:
            df["tags_create"] = extract_json_value(df, "tags_create", selected_key)
            selected_columns.remove("tags_create")
            selected_columns.append("tags_create")

        if "tags_modify" in selected_columns:
            df["tags_modify"] = extract_json_value(df, "tags_modify", selected_key)
            selected_columns.remove("tags_modify")
            selected_columns.append("tags_modify")

    chart_properties = {}
    if plot_type == "line":
        chart_properties["marker"] = st.sidebar.selectbox(
            "Select Marker Type", options=["o", "s", "^"], index=0, key="marker"
        )
        chart_properties["linestyle"] = st.sidebar.selectbox(
            "Select Line Style", options=["-", "--", "-."], index=0, key="linestyle"
        )
    elif plot_type == "bar":
        chart_properties["bar_width"] = st.sidebar.slider(
            "Select Bar Width",
            min_value=0.1,
            max_value=1.0,
            value=0.8,
            step=0.1,
            key="bar_width",
        )
    elif plot_type == "scatter":
        chart_properties["marker"] = st.sidebar.selectbox(
            "Select Marker Type", options=["o", "s", "^"], index=0, key="marker"
        )

    # Allow users to select x-axis interval based on data type
    x_column = st.selectbox("Select X-axis column", df.columns)
    # st.title(chart_title)
    y_columns = st.multiselect("Select Y-axis column(s)", selected_columns)

    if pd.api.types.is_numeric_dtype(df[x_column]):
        x_min = st.slider(
            "Select X-axis Interval (Min)",
            min_value=df[x_column].min(),
            max_value=df[x_column].max(),
            value=df[x_column].min(),
        )

        x_max = st.slider(
            "Select X-axis Interval (Max)",
            min_value=df[x_column].min(),
            max_value=df[x_column].max(),
            value=df[x_column].max(),
        )
    else:
        x_min = st.slider(
            "Select X-axis Interval (Min)",
            min_value=datetime.strptime(df[x_column].min(), "%Y-%m-%d").date(),
            max_value=datetime.strptime(df[x_column].max(), "%Y-%m-%d").date(),
            value=datetime.strptime(df[x_column].min(), "%Y-%m-%d").date(),
            format="MMM DD, YYYY",
        )

        x_max = st.slider(
            "Select X-axis Interval (Max)",
            min_value=datetime.strptime(df[x_column].min(), "%Y-%m-%d").date(),
            max_value=datetime.strptime(df[x_column].max(), "%Y-%m-%d").date(),
            value=datetime.strptime(df[x_column].max(), "%Y-%m-%d").date(),
            format="MMM DD, YYYY",
        )
        df[x_column] = pd.to_datetime(df[x_column]).dt.date
    # Filter the DataFrame based on the selected x-axis interval
    df_filtered = df[(df[x_column] >= x_min) & (df[x_column] <= x_max)]

    fig, ax = plot_chart(
        df_filtered, x_column, y_columns, plot_type, chart_title, chart_properties
    )
    st.pyplot(fig)

    if show_table:
        # Display the table with interactive features
        st.subheader("Data Table:")
        displayed_df = dynamic_json_extraction(df)

        # Additional options for the displayed table
        if st.checkbox("Show Selected Columns"):
            selected_columns = st.multiselect("Select columns", df.columns)
            displayed_df = df[selected_columns]

        if st.checkbox("Sort Data"):
            selected_column = st.selectbox("Select column to sort by", df.columns)
            ascending = st.checkbox("Sort in Ascending Order", True)
            displayed_df = df.sort_values(by=selected_column, ascending=ascending)

        if st.checkbox("Filter Data"):
            column_name = st.selectbox("Select column to filter", df.columns)
            filter_value = st.text_input("Enter filter value", "")
            displayed_df = df[df[column_name] == filter_value]

        # Display the modified DataFrame based on user selections
        st.write(displayed_df)


if __name__ == "__main__":
    main()
