import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import io

# 사우디아라비아 시간대 설정
saudi_tz = pytz.timezone('Asia/Riyadh')

st.set_page_config(layout="wide", page_title="Hormuz Route Monitoring")

st.title("🚢 우회/지연 화물 모니터링 시스템")

# 1. 사용자 정보 입력 (사이드바)
st.sidebar.header("👤 담당자 로그인")
# 소속을 3가지 옵션 중 선택하도록 변경 (기본 텍스트 입력창 제거)
affiliation = st.sidebar.selectbox(
    "소속 (Department)", 
    ["SR Logistics", "SJ Logistics", "FF Business"]
)
# 이름 기본값 제거 (빈칸으로 시작)
user_name = st.sidebar.text_input("이름 (Name)")

# 전체 필드 정의
columns = [
    "Product", "POL", "POD(Original)", "POD(Changed)", "Change Reason", 
    "Vessel Name", "Carrier", "Sea", "Arrived(before unloading)", "Terminal", 
    "CY", "In Transit", "Delivered", "ETA", "ATA", "Lead Time", 
    "Delivery Plan", "Total Cost"
]

# 데이터 저장을 위한 초기화
if 'log_data' not in st.session_state:
    st.session_state.log_data = pd.DataFrame(columns=["Update Time(KSA)", "Updater Info"] + columns)

if affiliation and user_name:
    st.sidebar.success(f"✅ 접속 확인: {affiliation} / {user_name} 님")
    
    # ---------------------------------------------------------
    # 2. 엑셀 일괄 업로드 / 다운로드 섹션
    # ---------------------------------------------------------
    st.markdown("### 📥 엑셀 일괄 업데이트")
    
    template_df = pd.DataFrame(columns=columns)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Template')
    buffer.seek(0)
    
    col_down, col_up = st.columns([1, 2])
    
    with col_down:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📊 엑셀 양식 다운로드",
            data=buffer,
            file_name="Hormuz_Monitoring_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with col_up:
        uploaded_file = st.file_uploader("작성 완료된 엑셀 파일 업로드", type=['xlsx'])
        if uploaded_file is not None:
            try:
                df_uploaded = pd.read_excel(uploaded_file)
                
                current_ksa_time = datetime.now(saudi_tz).strftime("%Y-%m-%d %H:%M:%S")
                updater_info = f"{affiliation} - {user_name}"
                
                df_uploaded.insert(0, "Update Time(KSA)", current_ksa_time)
                df_uploaded.insert(1, "Updater Info", updater_info)
                
                st.session_state.log_data = pd.concat([df_uploaded, st.session_state.log_data], ignore_index=True)
                st.success(f"✅ {len(df_uploaded)}건의 데이터가 성공적으로 업로드되었습니다! (기록 시간: {current_ksa_time})")
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    
    # ---------------------------------------------------------
    # 3. 개별 화물 수기 업데이트 폼
    # ---------------------------------------------------------
    st.markdown("### 📝 개별 화물 업데이트 폼")
    
    with st.form("monitoring_form"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            product = st.text_input("Product")
            pol = st.text_input("POL")
            pod_origin = st.text_input("POD (Original)")
            pod_changed = st.text_input("POD (Changed)")
            
        with col2:
            change_reason = st.selectbox("Change Reason", ["EOV", "COD"])
            delivery_plan = st.selectbox(
                "Delivery Plan", 
                ["Not decided", "Feeder", "Bonded(transit clearance)", "CC & Transloading"]
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

        submitted = st.form_submit_button("단건 데이터 업데이트")

        if submitted:
            current_ksa_time = datetime.now(saudi_tz).strftime("%Y-%m-%d %H:%M:%S")
            updater_info = f"{affiliation} - {user_name}"
            
            new_entry = {
                "Update Time(KSA)": current_ksa_time,
                "Updater Info": updater_info,
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
            st.success(f"✅ 개별 업데이트 완료 (기록 시간: {current_ksa_time})")

    # ---------------------------------------------------------
    # 4. 종합 모니터링 대시보드
    # ---------------------------------------------------------
    st.markdown("### 📊 Update History Log")
    st.dataframe(st.session_state.log_data, use_container_width=True)

else:
    st.info("👈 사이드바에 본인의 소속을 선택하고 이름을 입력하여 시스템을 시작하세요.")
