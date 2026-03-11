import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import io

# Set Saudi Arabia timezone
saudi_tz = pytz.timezone('Asia/Riyadh')

st.set_page_config(layout="wide", page_title="Hormuz Route Monitoring")

st.title("🚢 Hormuz Route Cargo Monitoring System")

# 1. User Login (Sidebar)
st.sidebar.header("👤 User Login")
# Selectbox for Department
affiliation = st.sidebar.selectbox(
    "Department", 
    ["SR Logistics", "SJ Logistics", "FF Business", "Management"]
)
user_name = st.sidebar.text_input("Name")

# Define all columns
columns = [
    "Customer", "Product", "POL", "POD(Original)", "POD(Changed)", "Change Reason", 
    "Vessel Name", "Carrier", "Sea", "Arrived(before unloading)", "Terminal", 
    "CY", "In Transit", "Delivered", "ETA", "ATA", "Lead Time", 
    "Delivery Plan", "Total Cost"
]

# Initialize session state for storing log data
if 'log_data' not in st.session_state:
    st.session_state.log_data = pd.DataFrame(columns=["Update Time(KSA)", "Updater Info"] + columns)

if affiliation and user_name:
    st.sidebar.success(f"✅ Access Confirmed: {affiliation} / {user_name}")
    
    # ---------------------------------------------------------
    # 🔒 Role-based Access Control: Management vs Operations
    # ---------------------------------------------------------
    if affiliation == "Management":
        st.warning("🔒 Logged in with Management access. Data viewing and downloading only.")
        
        st.markdown("### 📥 Download Current Data")
        log_buffer = io.BytesIO()
        with pd.ExcelWriter(log_buffer, engine='openpyxl') as writer:
            st.session_state.log_data.to_excel(writer, index=False, sheet_name='Monitoring_Data')
        log_buffer.seek(0)
        
        st.download_button(
            label="📊 Download Full Log Data (Excel)",
            data=log_buffer,
            file_name=f"Hormuz_Monitoring_Log_{datetime.now(saudi_tz).strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Update History Log (Read-only)")
        # Management는 읽기 전용 표 제공
        st.dataframe(st.session_state.log_data, use_container_width=True)
        
    else:
        # ---------------------------------------------------------
        # 2. Batch Excel Upload / Download Section (For Operations)
        # ---------------------------------------------------------
        st.markdown("### 📥 Batch Excel Update")
        
        template_df = pd.DataFrame(columns=columns)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            template_df.to_excel(writer, index=False, sheet_name='Template')
        buffer.seek(0)
        
        col_down, col_up = st.columns([1, 2])
        
        with col_down:
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📊 Download Blank Excel Template",
                data=buffer,
                file_name="Hormuz_Monitoring_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        with col_up:
            uploaded_file = st.file_uploader("Upload Completed Excel File", type=['xlsx'])
            if uploaded_file is not None:
                try:
                    df_uploaded = pd.read_excel(uploaded_file)
                    
                    current_ksa_time = datetime.now(saudi_tz).strftime("%Y-%m-%d %H:%M:%S")
                    updater_info = f"{affiliation} - {user_name}"
                    
                    df_uploaded.insert(0, "Update Time(KSA)", current_ksa_time)
                    df_uploaded.insert(1, "Updater Info", updater_info)
                    
                    st.session_state.log_data = pd.concat([df_uploaded, st.session_state.log_data], ignore_index=True)
                    st.success(f"✅ {len(df_uploaded)} records successfully uploaded! (Log Time: {current_ksa_time})")
                except Exception as e:
                    st.error(f"Error processing file: {e}")

        st.markdown("---")
        
        # ---------------------------------------------------------
        # 3. Individual Cargo Update Form (For Operations)
        # ---------------------------------------------------------
        st.markdown("### 📝 Individual Cargo Update Form")
        
        with st.form("monitoring_form"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                customer = st.text_input("Customer")
                product = st.text_input("Product")
                pol = st.text_input("POL")
                pod_origin = st.text_input("POD (Original)")
                pod_changed = st.text_input("POD (Changed)")
                
            with col2:
                change_reason = st.selectbox("Change Reason", ["EOV", "COD"])
                delivery_plan = st.selectbox(
                    "Delivery Plan", 
                    ["Not decided", "Feeder", "Bonded(transit clearance)", "CC & Transloading", "Ship back"]
                )
                vessel_name = st.text_input("Vessel Name")
                carrier = st.text_input("Carrier")
                
            with col3:
                st.markdown("**Number of Containers**")
                cntr_sea = st.number_input("Sea", min_value=0, step=1)
                cntr_arrived = st.number_input("Arrived(before unloading)", min_value=0, step=1)
                cntr_terminal = st.number_input("Terminal", min_value=0, step=1)
                cntr_cy = st.number_input("CY", min_value=0, step=1)
                
            with col4:
                st.markdown("**Schedule & Cost**")
                eta = st.date_input("ETA")
                ata = st.date_input("ATA")
                total_cost = st.number_input("Total Cost ($)", min_value=0.0)

            submitted = st.form_submit_button("Update Single Record")

            if submitted:
                current_ksa_time = datetime.now(saudi_tz).strftime("%Y-%m-%d %H:%M:%S")
                updater_info = f"{affiliation} - {user_name}"
                
                new_entry = {
                    "Update Time(KSA)": current_ksa_time,
                    "Updater Info": updater_info,
                    "Customer": customer,
                    "Product": product,
                    "POL": pol,
                    "POD(Original)": pod_origin,
                    "POD(Changed)": pod_changed,
                    "Change Reason": change_reason,
                    "Delivery Plan": delivery_plan,
                    "Vessel Name": vessel_name,
                    "Carrier": carrier,
                    "Sea": cntr_sea,
                    "Arrived(before unloading)": cntr_arrived,
                    "Terminal": cntr_terminal,
                    "CY": cntr_cy,
                    "ETA": eta,
                    "ATA": ata,
                    "Total Cost": total_cost
                }
                
                st.session_state.log_data = pd.concat(
                    [pd.DataFrame([new_entry]), st.session_state.log_data], 
                    ignore_index=True
                )
                st.success(f"✅ Record successfully updated. (Log Time: {current_ksa_time})")

        st.markdown("---")
        
        # ---------------------------------------------------------
        # 4. Comprehensive Monitoring Dashboard (Editable)
        # ---------------------------------------------------------
        st.markdown("### 📊 Update History Log (Editable)")
        st.info("💡 You can edit cells directly in the table below. You can also add or delete rows using the UI.")
        
        # st.dataframe을 st.data_editor로 변경하여 엑셀처럼 인라인 수정 가능하게 설정
        st.session_state.log_data = st.data_editor(
            st.session_state.log_data,
            use_container_width=True,
            num_rows="dynamic", # 행 추가 및 삭제 가능
            key="data_editor"
        )

else:
    st.info("👈 Please select your department and enter your name in the sidebar to start.")
