import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

# Load data
file_path = 'daily_temp.csv'  # Update this with the correct path
data = pd.read_csv(file_path)

# Clean and prepare data
data['날짜'] = pd.to_datetime(data['날짜'].str.strip())
data = data.dropna(subset=['날짜'])
data['연도'] = data['날짜'].dt.year

# Calculate yearly statistics
yearly_stats = data.groupby('연도').agg({
    '평균기온(℃)': 'mean',
    '최저기온(℃)': 'min',
    '최고기온(℃)': 'max'
}).reset_index()

# Streamlit title
st.title("Yearly Temperature Trends")

# User choice for graph type
chart_type = st.selectbox("Select chart type:", ("Line Chart", "Bar Chart"))

if chart_type == "Line Chart":
    # Plot line chart
    plt.figure(figsize=(12, 6))
    plt.plot(yearly_stats['연도'], yearly_stats['평균기온(℃)'], label='Average Temperature (℃)', marker='o')
    plt.plot(yearly_stats['연도'], yearly_stats['최저기온(℃)'], label='Minimum Temperature (℃)', marker='o')
    plt.plot(yearly_stats['연도'], yearly_stats['최고기온(℃)'], label='Maximum Temperature (℃)', marker='o')
    plt.xlabel('Year')
    plt.ylabel('Temperature (℃)')
    plt.title('Yearly Temperature Trends')
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

elif chart_type == "Bar Chart":
    # Plot bar chart
    plt.figure(figsize=(12, 6))
    plt.bar(yearly_stats['연도'] - 0.2, yearly_stats['평균기온(℃)'], width=0.2, label='Average Temperature (℃)')
    plt.bar(yearly_stats['연도'], yearly_stats['최저기온(℃)'], width=0.2, label='Minimum Temperature (℃)')
    plt.bar(yearly_stats['연도'] + 0.2, yearly_stats['최고기온(℃)'], width=0.2, label='Maximum Temperature (℃)')
    plt.xlabel('Year')
    plt.ylabel('Temperature (℃)')
    plt.title('Yearly Temperature Trends')
    plt.legend()
    st.pyplot(plt)
