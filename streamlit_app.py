import streamlit as st
import sqlite3
import pandas as pd
import os

# 데이터베이스 경로 설정
DB_FOLDER = "db"
DB_FILE = os.path.join(DB_FOLDER, "SJ_TM2360E_v2.sqlite3")

# 데이터베이스 폴더가 없으면 생성
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

# SQLite3에 CSV 데이터 저장 함수
def save_csv_to_db(df, table_name):
    """
    Pandas DataFrame을 SQLite3 테이블에 저장합니다.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        return True
    except Exception as e:
        st.error(f"데이터베이스 저장 중 오류 발생: {e}")
        return False

# Streamlit 앱 시작
st.title("CSV 파일 업로드 및 SQLite3 등록")

# 파일 업로더 위젯
uploaded_file = st.file_uploader("CSV 파일을 선택해주세요.", type="csv")

if uploaded_file is not None:
    try:
        # CSV 파일을 DataFrame으로 읽기
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        st.success("파일이 성공적으로 업로드되었습니다.")
        st.write("업로드된 데이터 미리보기:")
        st.dataframe(df.head())

        # 테이블명 입력
        table_name = st.text_input("데이터를 저장할 테이블명을 입력하세요.", value="historyinspection")

        if st.button("데이터베이스에 저장"):
            if table_name:
                # 데이터베이스에 데이터 저장
                if save_csv_to_db(df, table_name):
                    st.success(f"CSV 데이터가 '{DB_FILE}'의 '{table_name}' 테이블에 성공적으로 저장되었습니다.")
            else:
                st.warning("테이블명을 입력해주세요.")
    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

# 저장된 데이터 확인 (선택 사항)
if os.path.exists(DB_FILE):
    st.markdown("---")
    st.header("저장된 데이터베이스 확인")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 테이블 목록 가져오기
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [tbl[0] for tbl in cursor.fetchall()]
    
    if tables:
        selected_table = st.selectbox("확인할 테이블을 선택하세요.", tables)
        if selected_table:
            df_db = pd.read_sql(f"SELECT * FROM {selected_table}", conn)
            st.dataframe(df_db)
    else:
        st.info("데이터베이스에 테이블이 없습니다.")
    
    conn.close()
