
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="대전시 ESS 충전량과 방전량",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 대전시 ESS 날짜별 충전량과 방전량")
st.write(
    "2024년부터 2025년까지 대전시의 ESS 일단위 충전 및 방전 실적을 확인합니다."
)


# =========================================================
# CSV 파일 경로 설정
# =========================================================

file_2024 = "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2024.csv"
file_2025 = "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2025.csv"

base_dir = Path(__file__).resolve().parent

possible_dirs = [
    base_dir / "data",
    base_dir.parent / "data",
    base_dir
]


def find_file(filename):
    for folder in possible_dirs:
        path = folder / filename
        if path.exists():
            return path
    return None


path_2024 = find_file(file_2024)
path_2025 = find_file(file_2025)


# =========================================================
# 데이터 불러오기
# =========================================================

if path_2024 is None or path_2025 is None:
    st.error(
        "CSV 파일을 찾을 수 없습니다. "
        "data 폴더와 파일 이름을 확인해 주세요."
    )
    st.stop()

try:
    df_2024 = pd.read_csv(path_2024, encoding="utf-8-sig")
    df_2025 = pd.read_csv(path_2025, encoding="utf-8-sig")

    df = pd.concat(
        [df_2024, df_2025],
        ignore_index=True
    )

except Exception as e:
    st.error(f"CSV 파일을 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# =========================================================
# 열 이름 확인
# =========================================================

required_columns = [
    "거래일",
    "충전량 합계(kWh)",
    "방전량 합계(kWh)"
]

for column in required_columns:
    if column not in df.columns:
        st.error(f"필요한 열을 찾을 수 없습니다: {column}")
        st.write("현재 CSV 열 이름:", df.columns.tolist())
        st.stop()


# 지역 열 자동 확인
region_candidates = [
    "지역",
    "시도",
    "지역명",
    "시도명"
]

region_column = next(
    (col for col in region_candidates if col in df.columns),
    None
)

if region_column is None:
    st.error("지역을 구분하는 열을 찾지 못했습니다.")
    st.write("현재 CSV 열 이름:", df.columns.tolist())
    st.stop()


# =========================================================
# 데이터 전처리
# =========================================================

df["거래일"] = pd.to_datetime(
    df["거래일"],
    errors="coerce"
)

df["충전량 합계(kWh)"] = pd.to_numeric(
    df["충전량 합계(kWh)"],
    errors="coerce"
)

df["방전량 합계(kWh)"] = pd.to_numeric(
    df["방전량 합계(kWh)"],
    errors="coerce"
)


# =========================================================
# 대전시 데이터만 추출
# =========================================================

df[region_column] = df[region_column].astype(str).str.strip()

gyeonggi_df = df[
    df[region_column] == "대전시"
].copy()

if gyeonggi_df.empty:
    st.error("대전시 데이터를 찾을 수 없습니다.")
    st.write(
        "CSV에 들어 있는 지역 목록:",
        sorted(df[region_column].dropna().unique().tolist())
    )
    st.stop()


# =========================================================
# 데이터 개요
# =========================================================

st.subheader("📊 대전시 데이터 개요")

st.write(
    "2024년과 2025년 CSV에서 대전시 데이터만 추출했습니다."
)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "대전시 전체 행 수",
        f"{gyeonggi_df.shape[0]:,}개"
    )

with col2:
    st.metric(
        "전체 열 수",
        f"{gyeonggi_df.shape[1]:,}개"
    )

overview = pd.DataFrame({
    "열 이름": gyeonggi_df.columns,
    "자료형": [
        str(gyeonggi_df[column].dtype)
        for column in gyeonggi_df.columns
    ],
    "빈 값 개수": [
        int(gyeonggi_df[column].isna().sum())
        for column in gyeonggi_df.columns
    ]
})

st.dataframe(
    overview,
    use_container_width=True,
    hide_index=True
)

st.divider()


# =========================================================
# 날짜별 충전량과 방전량 계산
# =========================================================

daily_df = (
    gyeonggi_df
    .dropna(subset=["거래일"])
    .groupby("거래일", as_index=False)[
        ["충전량 합계(kWh)", "방전량 합계(kWh)"]
    ]
    .sum(min_count=1)
)

daily_df = daily_df.sort_values("거래일").reset_index(drop=True)


# =========================================================
# 0값 확인
# =========================================================

st.subheader("🔎 0값 확인")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "충전량이 0인 날짜",
        f"{int((daily_df['충전량 합계(kWh)'] == 0).sum()):,}일"
    )

with col2:
    st.metric(
        "방전량이 0인 날짜",
        f"{int((daily_df['방전량 합계(kWh)'] == 0).sum()):,}일"
    )

st.caption(
    "0값은 결측치로 처리하지 않고 실제 데이터로 유지합니다."
)

st.divider()


# =========================================================
# 날짜별 충전량과 방전량 그래프
# =========================================================

st.subheader("📈 2024~2025년 대전시 ESS 날짜별 충전량과 방전량")

fig = go.Figure()

# 충전량
fig.add_trace(
    go.Scatter(
        x=daily_df["거래일"],
        y=daily_df["충전량 합계(kWh)"],
        mode="lines+markers",
        name="충전량",
        line=dict(color="#636EFA", width=2),
        marker=dict(size=5),
        hovertemplate=(
            "날짜: %{x|%Y-%m-%d}<br>"
            "충전량: %{y:,.0f} kWh<extra></extra>"
        )
    )
)

# 방전량
fig.add_trace(
    go.Scatter(
        x=daily_df["거래일"],
        y=daily_df["방전량 합계(kWh)"],
        mode="lines+markers",
        name="방전량",
        line=dict(color="#FF4B4B", width=2),
        marker=dict(size=5),
        hovertemplate=(
            "날짜: %{x|%Y-%m-%d}<br>"
            "방전량: %{y:,.0f} kWh<extra></extra>"
        )
    )
)

fig.update_layout(
    xaxis_title="거래일",
    yaxis_title="전력량(kWh)",
    hovermode="x unified",
    legend_title="구분",
    height=550,
    template="plotly_white"
)

# y축에 0 포함
fig.update_yaxes(
    tickformat=".2s",
    rangemode="tozero"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================================================
# 날짜별 데이터 확인
# =========================================================

with st.expander("📋 대전시 날짜별 충전량과 방전량 데이터 확인"):
    st.dataframe(
        daily_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 원본 대전시 데이터 확인
# =========================================================

with st.expander("📂 대전시 원본 데이터 확인"):
    st.dataframe(
        gyeonggi_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 자료 출처
# =========================================================

st.caption(
    "자료 출처: 지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적"
)
