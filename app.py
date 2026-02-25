import streamlit as st

st.set_page_config(
    page_title="Haleon Awareness Tool",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

from datetime import datetime
from datetime import timedelta
#import streamlit as st
import pandas as pd
import requests
from io import StringIO
#st.logo("haleon_logo.png")

col1, col2 = st.columns([1, 8])

with col1:
    st.image("haleon_logo.png", width=60)

with col2:
    st.markdown("## Haleon Awareness Tool")


#st.markdown("""
#<h1 style="display: flex; align-items: center;">
 #   <img src="haleon_logo.png" height="60" style="margin-right: 10px;">
  #  Haleon Awareness Tool
#</h1>
#""", unsafe_allow_html=True)
# Dictionary of sheet names 
SHEETS = {
    "Report": "https://gist.githubusercontent.com/dimijaf/41ded8133ff12eceb0f18138a0073df7/raw/6e3305174b6158f6a41b7b672416921463422e76/gistfile1.txt",
    "RealTime": "https://awarenesstool.azurewebsites.net/api/DatabaseBridge/GetAllReport?s=2hp2wNIDkzVgfwxak5719VtGn8FE1VQG90KHuh1tjJsOYjNI",
    "Questions": "https://gist.githubusercontent.com/dimijaf/3d4725c7b69e825eb5f41c2cf41487ce/raw/ada86adb2239795890c5b3fa8d937993778d6764/gistfile1.txt"
}
def load_data(url):
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text))

for name, url in SHEETS.items():
    if name not in st.session_state:
        st.session_state[name] = load_data(url)

#sheet_name = st.selectbox("Select Sheet", list(SHEETS.keys()))
tabs = st.tabs(["Report", "RealTime", "Questions", "Graph"])



for i, sheet_name in enumerate(["Report", "RealTime", "Questions", "Graph"]):
    with tabs[i]:
        if sheet_name in SHEETS:  # Only for sheets with data URLs
            if st.button(f"🔄 Refresh {sheet_name}", key=f"refresh_{sheet_name}"):
                st.session_state[sheet_name] = load_data(SHEETS[sheet_name])
            df = st.session_state[sheet_name]
        
 
      
        
        ###url = SHEETS[sheet_name]

        #if sheet_name not in st.session_state:
         #   st.session_state[sheet_name] = load_data(url)

        #if st.button(f"🔄 Refresh {sheet_name}", key=f"refresh_{sheet_name}"):
         #   st.session_state[sheet_name] = load_data(url)

        #df = st.session_state[sheet_name]
        #if sheet_name == "RealTime":
         #   st.dataframe(df, use_container_width=True)
    
        #st.session_state["RealTime"]['QuestionnaireDate'] = pd.to_datetime(
         #   st.session_state["RealTime"]['QuestionnaireDate'], 
          #  errors='coerce'
        #).dt.strftime('%d/%m/%y')
        st.session_state["Report"]['Installed Day'] = pd.to_datetime(
            st.session_state["Report"]['Installed Day'],dayfirst=True, 
            errors='coerce'
        ).dt.strftime('%d/%m/%y')
        if sheet_name == "Report":
            counts = st.session_state["RealTime"]["DeviceId"].astype(str).value_counts()
            df_t = df.T.copy()
            sum_row = df_t.iloc[0].astype(str).map(counts).fillna(0).astype(int)
            df_t.loc['Sum'] = sum_row
            days_row = pd.Series(0, index=df_t.columns, name='Days Installed')
            installed_row = df_t.loc['Installed Day']
            for col in df_t.columns:
                date_str = str(installed_row[col]).strip()
                if date_str and '/' in date_str:
                    try:
                        days_row[col] = (datetime.now() - pd.to_datetime(date_str,dayfirst=True)).days
                    except:
                        try:
                            days_row[col] = (datetime.now() - pd.to_datetime(date_str,dayfirst=True)).days
                        except:
                            pass
            df_t.loc['Days Installed'] = days_row
            realtime = st.session_state["RealTime"]
            realtime['QuestionnaireDate_parsed'] = pd.to_datetime(realtime['QuestionnaireDate'], errors='coerce')

            last_seen_row = pd.Series('', index=df_t.columns, name='Last Seen')
            device_ids_row = df_t.loc['DeviceId']  # Exact row name
            
            for device_id in device_ids_row.index:  # Loop through DeviceIDs row
                device_id_val = str(device_ids_row[device_id]).strip()
                matching_rows = realtime[realtime['DeviceId'].astype(str).str.strip() == device_id_val]
                if not matching_rows.empty:
                    dates = pd.to_datetime(matching_rows['QuestionnaireDate_parsed'], errors='coerce')
                    max_date = dates.max()
                    if pd.notna(max_date):
                        last_seen_row[device_id] = max_date.strftime('%d/%m/%y')
                    else:
                        last_seen_row[device_id] = 'No date'
            df_t.loc['Last Seen'] = last_seen_row
            avg_row = (
                pd.to_numeric(df_t.loc["Sum"], errors="coerce") /
                pd.to_numeric(df_t.loc["Days Installed"], errors="coerce")
            ).round(3)
            df_t.loc['Avg_today'] = avg_row
            
            
            
            
            today = datetime.now().date()
            dates_10days = [(today - timedelta(days=10*i)).strftime('%d/%m/%y') for i in range(2, 10)]

  
           
            realtime['Month'] = realtime['QuestionnaireDate_parsed'].dt.to_period('M')
            
            for month in realtime['Month'].dropna().unique():
                month_avg = pd.Series(0.0, index=df_t.columns, name=f'Avg_{month}')
                month_end = month.to_timestamp('M').date()
            
                for col in df_t.columns:
                    device_id = str(df_t.loc['DeviceId', col]).strip()
                    install_date_str = str(df_t.loc['Installed Day', col]).strip()
            
                    historical_data = realtime[
                        (realtime['DeviceId'].astype(str) == device_id) &
                        (realtime['Month'] <= month)
                    ]
                    sum_up_to_month = len(historical_data)
            
                    try:
                        install_date = datetime.strptime(install_date_str, '%d/%m/%y').date()
                        days_installed = max((month_end - install_date).days, 1)
                    except:
                        days_installed = 1
            
                    month_avg[col] = round(sum_up_to_month / days_installed, 2)

                    df_t.loc[f'Avg_{month}'] = month_avg
                    
                    

                    #date_avg[col] = round(sum_up_to_date / days_installed, 2)

               
                #df_t.loc[f'Avg_{date_str}'] = date_avg

            
            styled_df = (df_t.style.set_properties(
                **{
                    'background-color': 'black',
                    'color': 'white',
                    'font-weight': 'bold'
                }
            ).format(precision=2))
            
            
            st.dataframe(
                styled_df,
                height=500,
                use_container_width=True,
                column_config={
                    col: st.column_config.Column(width="120") 
                    for col in df_t.columns
                }
            )
            st.session_state["Report_df_t"] = df_t



        if sheet_name == "RealTime":
            df = st.session_state["RealTime"]
            st.dataframe(df, use_container_width=True)  
            
        if sheet_name == "Questions":
            realtime = st.session_state["RealTime"]
            question_names = df['Question number'].tolist()
            df['NAI_Count'] = 0
            df['NAI_%'] = 0.0
    
    # Count NAI for each Q1, Q2, etc. column from RealTime
            for idx, row in df.iterrows():
                q_name = row['Question number']
                if q_name in realtime.columns:
                    q_col = realtime[q_name]
            
                    nai_count = (q_col == 'NAI').sum()  # or realtime[q_name].eq('ΝΑΙ').sum()
                    total_count = q_col.notna().sum()
                    
                    df.loc[idx, 'NAI_Count'] = nai_count
                    df.loc[idx, 'NAI_%'] = round((nai_count / total_count * 100), 2) if total_count > 0 else 0
            
            st.dataframe(df, use_container_width=True, height=600)
#



        
        








        if sheet_name == "Graph":
            df_t = st.session_state.get("Report_df_t")
              
            if df_t is not None:
                cities = df_t.loc['City'].dropna()
        
              
                avg_rows = [str(r).strip() for r in df_t.index if str(r).startswith('Avg_')]
        
        
                def parse_avg(r):
                    if r == 'Avg_today':
                        return datetime.now()
                    return pd.to_datetime(r.replace('Avg_', ''), dayfirst=True, errors='coerce')
        
                avg_rows_sorted = sorted(avg_rows, key=parse_avg)
        
                chart_data = pd.DataFrame(index=cities.index)
                chart_data['City'] = cities.values
        
                for r in avg_rows_sorted:
                    chart_data[r] = pd.to_numeric(df_t.loc[r, cities.index], errors='coerce')
        
            
                chart_data = chart_data[['City'] + avg_rows_sorted]
        
           
                chart_data = chart_data.copy()
        
                
                #st.write("FINAL COL ORDER:", chart_data.columns.tolist())
        
           
                st.bar_chart(chart_data.set_index('City'),use_container_width=True, stack=False)



