
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="ESS 날짜별 충전량과 방전량",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 ESS 날짜별 충전량과 방전량")


# =========================================================
# CSV 파일 경로
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR.parent / "data"

FILE_2024 = DATA_DIR / "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2024.csv"
FILE_2025 = DATA_DIR / "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2025.csv"


# =========================================================
# 데이터 불러오기
# =========================================================

@st.cache_data
def load_data():

    df_2024 = pd.read_csv(FILE_2024, encoding="utf-8-sig")
    df_2025 = pd.read_csv(FILE_2025, encoding="utf-8-sig")

    df = pd.concat(
        [df_2024, df_2025],
        ignore_index=True
    )

    return df


if not FILE_2024.exists() or not FILE_2025.exists():
    st.error("CSV 파일을 찾을 수 없습니다.")
    st.stop()

try:
    df = load_data()

except Exception as e:
    st.error(f"데이터 불러오기 오류: {e}")
    st.stop()


# =========================================================
# 실제 CSV 열 이름
# =========================================================

date_col = "거래일"
charge_col = "충전량 합계(kWh)"
discharge_col = "방전량 합계(kWh)"

required_cols = [
    date_col,
    charge_col,
    discharge_col
]

if not all(col in df.columns for col in required_cols):
    st.error("CSV 열 이름을 확인해 주세요.")
    st.write("현재 CSV 열 이름:", df.columns.tolist())
    st.stop()


# =========================================================
# 데이터 전처리
# =========================================================

# 날짜 변환
df[date_col] = pd.to_datetime(
    df[date_col],
    errors="coerce"
)

# 충전량과 방전량 숫자 변환
df[charge_col] = pd.to_numeric(
    df[charge_col],
    errors="coerce"
)

df[discharge_col] = pd.to_numeric(
    df[discharge_col],
    errors="coerce"
)

# 날짜가 없는 행 제거
df = df.dropna(subset=[date_col])


# =========================================================
# 날짜별 충전량과 방전량 합계
# =========================================================

daily = (
    df.groupby(date_col)
    .agg({
        charge_col: lambda x: x.sum(min_count=1),
        discharge_col: lambda x: x.sum(min_count=1)
    })
    .reset_index()
)

daily = daily.sort_values(date_col)


# =========================================================
# 날짜별 충전량과 방전량 그래프
# =========================================================

fig = go.Figure()

# 충전량
fig.add_trace(
    go.Scatter(
        x=daily[date_col],
        y=daily[charge_col],
        mode="lines",
        name="충전량",
        connectgaps=False
    )
)

# 방전량
fig.add_trace(
    go.Scatter(
        x=daily[date_col],
        y=daily[discharge_col],
        mode="lines",
        name="방전량",
        connectgaps=False
    )
)

fig.update_layout(
    title="2024~2025년 ESS 날짜별 충전량과 방전량",
    xaxis_title="거래일",
    yaxis_title="전력량 (kWh)",
    hovermode="x unified",
    template="plotly_white",
    legend_title="구분"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
