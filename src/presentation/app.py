import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# .env ファイルを自動ロード（システム環境変数が既に存在する場合は上書きしない）
from dotenv import load_dotenv
load_dotenv(override=False)

import streamlit as st
import numpy as np
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
import plotly.graph_objects as go
from src.infrastructure.persistence.db_connector import DatabaseConnector

# 페이지 기본 설정 (다크모드 글라스모피즘 미학 연출을 위해 레이아웃 와이드 설정)
st.set_page_config(
    page_title="예방 돌봄 AI 에이전트 안심 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 0. 마스터 패스워드 로그인 세션 가드 작동
from src.presentation.auth_guard import require_master_password
require_master_password()

# 1. HSL 기반 다크 모드 글라스모피즘 미학 CSS 주입 (Wow Factor)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 전역 글꼴 지정 */
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
        background-color: #0d0f12 !important;
        color: #e2e8f0 !important;
    }
    
    /* 메인 컨테이너 글라스모피즘 스타일링 */
    .stApp {
        background: linear-gradient(135deg, #090a0f 0%, #151821 100%) !important;
    }
    
    /* 카드 글라스모피즘 구현 */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
    }
    
    /* 호버 애니메이션 */
    .glass-card:hover {
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        transform: translateY(-2px);
        transition: all 0.3s ease-in-out;
    }
    
    /* 상태별 그라데이션 타이틀 배지 */
    .status-badge-normal {
        background: linear-gradient(135deg, hsla(145, 80%, 40%, 0.15) 0%, hsla(145, 80%, 30%, 0.25) 100%);
        border: 1px solid hsla(145, 80%, 50%, 0.4);
        color: #2ecc71;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-warning {
        background: linear-gradient(135deg, hsla(38, 90%, 45%, 0.15) 0%, hsla(38, 90%, 35%, 0.25) 100%);
        border: 1px solid hsla(38, 90%, 50%, 0.4);
        color: #f39c12;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-danger {
        background: linear-gradient(135deg, hsla(0, 85%, 45%, 0.15) 0%, hsla(0, 85%, 35%, 0.25) 100%);
        border: 1px solid hsla(0, 85%, 50%, 0.4);
        color: #e74c3c;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    /* 의료 경고 보조지표 헤더 스타일 */
    .medical-disclaimer-box {
        background: rgba(231, 76, 60, 0.08);
        border-left: 4px solid #e74c3c;
        padding: 15px;
        border-radius: 4px;
        color: #f19f9a;
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터베이스 연결 관리 (스레드 세이프 연결 싱글톤 어댑터 활용)
@st.cache_resource
def get_db_connection() -> DatabaseConnector:
    return DatabaseConnector()

db = get_db_connection()

# 3. 사이드바 - 실무 관리자 세션 정보 및 노인 요약 필터
st.sidebar.markdown("<h2 style='text-align: center; color: #fff;'>🛡️ 안심 돌봄 관리 포트</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.07);'>", unsafe_allow_html=True)

# 모의 사회복지사 세션 정보 표출 (MVP scope 제약 준수)
st.sidebar.markdown("""
    <div class='glass-card' style='padding: 15px;'>
        <p style='margin: 0; font-size: 0.8rem; color: #a0aec0;'>접속 관리자</p>
        <h4 style='margin: 5px 0 0 0; color: #fff;'>한아름 사회복지사</h4>
        <p style='margin: 5px 0 0 0; font-size: 0.75rem; color: #2ecc71;'>● 스마트시티 안심 보드 세션 활성</p>
    </div>
""", unsafe_allow_html=True)

# 피돌봄 주민 데이터 조회 및 통계 계측
with db.get_connection() as conn:
    residents = conn.execute("SELECT * FROM residents;").fetchall()
    residents = [dict(r) for r in residents]
    
    # 1. 조치 대기 PENDING 건수 계측
    pending_alerts_count = conn.execute("SELECT COUNT(*) FROM caregiver_alerts WHERE action_status = 'PENDING';").fetchone()[0]
    
    # 2. 오늘 우선 확인 대상자 조회 (DANGER 또는 WARNING 대상자 중 조치 상태가 PENDING인 사람)
    priority_alerts_rows = conn.execute("""
        SELECT r.virtual_code, r.current_status, ar.boxplot_violations
        FROM residents r
        JOIN anomaly_reports ar ON r.id = ar.resident_id
        JOIN caregiver_alerts ca ON ar.id = ca.anomaly_report_id
        WHERE r.current_status IN ('DANGER', 'WARNING') AND ca.action_status = 'PENDING'
        GROUP BY r.id
        ORDER BY ar.analysis_date DESC;
    """).fetchall()
    priority_alerts = [dict(row) for row in priority_alerts_rows]

if not residents:
    st.error("데이터베이스에 등록된 주민 데이터가 없습니다. 먼저 seed 스크립트를 작동하십시오.")
    st.stop()

# ---------------------------------------------------------------
# 비식별 표시명 매핑 테이블 (UI 표현 레이어 전용)
# DB 구조·PII 정책·테스트는 일체 무변경
# ---------------------------------------------------------------
DISPLAY_NAME_MAP: dict = {
    "RES-MASK-2026A": "박○○ 어르신",
    "RES-MASK-2026B": "김○○ 어르신",
    "RES-MASK-2026C": "이○○ 어르신",
    "RES-MASK-2026D": "최○○ 어르신",
    "RES-MASK-2026E": "정○○ 어르신",
}

def get_display_name(code: str) -> str:
    """virtual_code를 비식별 표시명으로 변환. 매핑 없으면 코드 그대로 반환."""
    return DISPLAY_NAME_MAP.get(code, code)

# 우선 확인 대상자 영역 추가
st.sidebar.markdown("<p style='font-size: 0.95rem; font-weight: 600; margin-top: 15px; margin-bottom: 8px;'>🚨 오늘 우선 확인 대상자</p>", unsafe_allow_html=True)
if priority_alerts:
    for pa in priority_alerts:
        emoji = "🔴" if pa["current_status"] == "DANGER" else "🟡"
        try:
            viols = json.loads(pa["boxplot_violations"])
            viol_names = ", ".join([v["activity"] for v in viols])
        except Exception:
            viol_names = "이상패턴"
        status_label = "고위험" if pa["current_status"] == "DANGER" else "주의"
        st.sidebar.markdown(f"""
            <div style='background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='font-weight: bold; color: #fff;'>{emoji} {get_display_name(pa["virtual_code"])}</span>
                    <span style='font-size: 0.75rem; color: {"#e74c3c" if pa["current_status"] == "DANGER" else "#f39c12"}; font-weight: bold;'>{status_label}</span>
                </div>
                <div style='font-size: 0.72rem; color: #a0aec0; margin-top: 4px;'>
                    이상: {viol_names} (대기)
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("<div style='font-size: 0.85rem; color: #a0aec0; padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px;'>현재 우선 확인 대상자는 없습니다.</div>", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.07);'>", unsafe_allow_html=True)

# 주민 등급별 대시보드 상태 필터 기능
status_filter = st.sidebar.selectbox(
    "위험 상태별 분류 필터",
    ["전체보기", "DANGER (고위험)", "WARNING (주의)", "NORMAL (정상)"]
)

# 필터 처리
filtered_residents = []
for res in residents:
    if status_filter == "전체보기":
        filtered_residents.append(res)
    elif status_filter == "DANGER (고위험)" and res["current_status"] == "DANGER":
        filtered_residents.append(res)
    elif status_filter == "WARNING (주의)" and res["current_status"] == "WARNING":
        filtered_residents.append(res)
    elif status_filter == "NORMAL (정상)" and res["current_status"] == "NORMAL":
        filtered_residents.append(res)

# 필터 처리 결과 검증 (StopIteration 예외 예방 가드)
if not filtered_residents:
    st.markdown("""
        <div class='glass-card' style='margin-top: 40px; text-align: center; border-style: dashed;'>
            <h3 style='color: #f39c12;'>⚠ 대상 주민 부재</h3>
            <p style='color: #a0aec0; margin: 0;'>선택하신 위험 등급 필터에 해당하는 피돌봄 노인이 현재 존재하지 않습니다.</p>
            <p style='color: #2ecc71; margin-top: 10px; font-weight: bold;'>← 왼쪽 사이드바에서 '위험 상태별 분류 필터'를 '전체보기' 또는 '주의 (WARNING)'로 변경해 주십시오.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# 사이드바 주민 선택 카드 리스트 구성
st.sidebar.markdown("<p style='font-size: 0.9rem; font-weight: 600; margin-bottom: 5px;'>피돌봄 대상 노인 선택</p>", unsafe_allow_html=True)

# 이모지 포맷팅 함수 정의 (사이드바 라디오용)
resident_status_map = {r["virtual_code"]: r["current_status"] for r in residents}
def format_resident_label(code: str) -> str:
    status = resident_status_map.get(code, "NORMAL")
    name = get_display_name(code)
    if status == "DANGER":
        return f"🔴 {name} (고위험)"
    elif status == "WARNING":
        return f"🟡 {name} (주의)"
    return f"🟢 {name} (정상)"

selected_res_code = st.sidebar.radio(
    label="돌봄 대상 어르신 선택",
    options=[r["virtual_code"] for r in filtered_residents],
    format_func=format_resident_label,
    label_visibility="collapsed"
)

# 선택된 노인의 상세 엔터티 매핑 (StopIteration 방지 가드 장착)
selected_resident = next((r for r in residents if r["virtual_code"] == selected_res_code), None)
if not selected_resident:
    st.warning("선택하신 주민이 존재하지 않습니다.")
    st.stop()
    
resident_id = selected_resident["id"]

# 4. 메인 대시보드 - 헤더 타이틀 및 등급 배지 렌더링
col_header, col_badge = st.columns([4, 1])
with col_header:
    display_name = get_display_name(selected_res_code)
    st.markdown(f"<h1 style='margin:0; font-weight:800; color:#fff;'>🧓 {display_name}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #718096; font-size: 0.8rem; margin-top: 2px;'>관리 코드: {selected_res_code}</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a0aec0; margin-top: 4px;'>AttentionRNN 시계열 예측과 Double-step IQR 통계 기반의 독거노인 일상생활 예방 예보 관리 화면</p>", unsafe_allow_html=True)

with col_badge:
    status = selected_resident["current_status"]
    if status == "DANGER":
        st.markdown("<div style='text-align: right; margin-top: 15px;'><span class='status-badge-danger'>고위험 DANGER</span></div>", unsafe_allow_html=True)
    elif status == "WARNING":
        st.markdown("<div style='text-align: right; margin-top: 15px;'><span class='status-badge-warning'>주의 WARNING</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: right; margin-top: 15px;'><span class='status-badge-normal'>정상 NORMAL</span></div>", unsafe_allow_html=True)

st.markdown("<hr style='border-color: rgba(255,255,255,0.07); margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# 4.1. 상단 Summary Metric Cards 추가
col_tot, col_dan, col_warn, col_norm, col_pend = st.columns(5)

with col_tot:
    st.markdown(f"""
        <div class='glass-card' style='padding: 15px; text-align: center; margin-bottom: 15px;'>
            <p style='margin: 0; font-size: 0.8rem; color: #a0aec0;'>전체 대상자</p>
            <h2 style='margin: 5px 0 0 0; color: #fff;'>{len(residents)}명</h2>
        </div>
    """, unsafe_allow_html=True)

with col_dan:
    danger_count = sum(1 for r in residents if r["current_status"] == "DANGER")
    st.markdown(f"""
        <div class='glass-card' style='padding: 15px; text-align: center; border-color: rgba(231, 76, 60, 0.3); margin-bottom: 15px;'>
            <p style='margin: 0; font-size: 0.8rem; color: #f19f9a;'>🔴 고위험 DANGER</p>
            <h2 style='margin: 5px 0 0 0; color: #e74c3c;'>{danger_count}명</h2>
        </div>
    """, unsafe_allow_html=True)

with col_warn:
    warning_count = sum(1 for r in residents if r["current_status"] == "WARNING")
    st.markdown(f"""
        <div class='glass-card' style='padding: 15px; text-align: center; border-color: rgba(243, 156, 18, 0.3); margin-bottom: 15px;'>
            <p style='margin: 0; font-size: 0.8rem; color: #f9d59b;'>🟡 주의 WARNING</p>
            <h2 style='margin: 5px 0 0 0; color: #f39c12;'>{warning_count}명</h2>
        </div>
    """, unsafe_allow_html=True)

with col_norm:
    normal_count = sum(1 for r in residents if r["current_status"] == "NORMAL")
    st.markdown(f"""
        <div class='glass-card' style='padding: 15px; text-align: center; border-color: rgba(46, 204, 113, 0.3); margin-bottom: 15px;'>
            <p style='margin: 0; font-size: 0.8rem; color: #a3e4d7;'>🟢 정상 NORMAL</p>
            <h2 style='margin: 5px 0 0 0; color: #2ecc71;'>{normal_count}명</h2>
        </div>
    """, unsafe_allow_html=True)

with col_pend:
    st.markdown(f"""
        <div class='glass-card' style='padding: 15px; text-align: center; border-color: rgba(155, 89, 182, 0.3); margin-bottom: 15px;'>
            <p style='margin: 0; font-size: 0.8rem; color: #d7bde2;'>⚡ 조치 대기 PENDING</p>
            <h2 style='margin: 5px 0 0 0; color: #9b59b6;'>{pending_alerts_count}건</h2>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border-color: rgba(255,255,255,0.07); margin-top: 15px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# 5. DB에서 해당 노인의 최신 이상 탐지 보고서 정보 로드
with db.get_connection() as conn:
    latest_report = conn.execute(
        "SELECT * FROM anomaly_reports WHERE resident_id = ? ORDER BY analysis_date DESC LIMIT 1;",
        (resident_id,)
    ).fetchone()
    
if not latest_report:
    st.warning("선택한 주민에 대한 분석 완료된 이상 탐지 보고서(Anomaly Report)가 존재하지 않습니다.")
    st.stop()

latest_report = dict(latest_report)
report_id = latest_report["id"]
z_score = latest_report["z_score"]
attention_weights = json.loads(latest_report["attention_weights"])
boxplot_violations = json.loads(latest_report["boxplot_violations"])
xai_report = latest_report["xai_report_content"]

# 복지사용 알림 및 피드백 상태 조회
with db.get_connection() as conn:
    alert = conn.execute(
        "SELECT * FROM caregiver_alerts WHERE anomaly_report_id = ? LIMIT 1;",
        (report_id,)
    ).fetchone()

if alert:
    alert = dict(alert)
    alert_id = alert["id"]
else:
    alert_id = None

# 6. 통계 시각화 패널 레이아웃 구성
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("<h3 style='color: #fff;'>📈 AttentionRNN 과거 15일 기여도 분석</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a0aec0; font-size: 0.85rem;'>GRU 예측 시 16일 차 행동 예측에 강한 변동 영향력을 제공한 일자별 어텐션 가중치 그래프</p>", unsafe_allow_html=True)
    
    # Plotly 어텐션 바차트 디자인
    fig_att = go.Figure()
    days_labels = [f"D-{15 - i}일 전" for i in range(15)]
    fig_att.add_trace(go.Bar(
        x=days_labels,
        y=attention_weights,
        marker=dict(
            color=attention_weights,
            colorscale='Viridis',
            line=dict(color='rgba(255,255,255,0.1)', width=1)
        ),
        hovertemplate='기여 가중치: %{y:.3f}<extra></extra>'
    ))
    fig_att.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', showline=False),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', showline=False),
        height=260
    )
    st.plotly_chart(fig_att, use_container_width=True)

with col_right:
    st.markdown("<h3 style='color: #fff;'>📊 개별 활동 Boxplot 임계 범위 이탈(IQR)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a0aec0; font-size: 0.85rem;'>2단계 Boxplot IQR 판정에서 역사적 사분위수 범위를 극단적으로 이탈한 활동별 수치 편차</p>", unsafe_allow_html=True)
    
    if not boxplot_violations:
        st.markdown("""
            <div class='glass-card' style='height: 230px; display: flex; align-items: center; justify-content: center; border-style: dashed;'>
                <p style='color: #2ecc71; font-weight: 600; margin: 0;'>✔ 모든 활동이 역사적 Boxplot 사분위수 안심 범위 내에 존재합니다.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # 이탈 위반 수치 차트화
        fig_vio = go.Figure()
        acts = [v["activity"] for v in boxplot_violations]
        deviations = [v["deviation"] for v in boxplot_violations]
        
        # 음수 이탈(Low), 양수 이탈(High)에 따라 색상 매핑
        colors = ['#e74c3c' if d < 0 else '#e67e22' for d in deviations]
        
        fig_vio.add_trace(go.Bar(
            x=acts,
            y=deviations,
            marker_color=colors,
            marker_line=dict(color='rgba(255,255,255,0.1)', width=1),
            hovertemplate='임계 범위 이탈 편차: %{y:.2f}%<extra></extra>'
        ))
        fig_vio.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="이탈 편차 (%)"),
            height=260
        )
        st.plotly_chart(fig_vio, use_container_width=True)

# 7. XAI 자연어 보고서 디스플레이 및 피드백 폼 연동 레이아웃
st.markdown("<hr style='border-color: rgba(255,255,255,0.07); margin-top: 20px; margin-bottom: 25px;'>", unsafe_allow_html=True)

col_xai, col_feedback = st.columns([3, 2])

with col_xai:
    st.markdown("<h3 style='color: #fff;'>📝 맥락 주입형 LLM XAI 예방 안심 보고서</h3>", unsafe_allow_html=True)
    
    # 의료 보조지표 고정 헤더 인쇄
    st.markdown("""
        <div class='medical-disclaimer-box'>
            [의사결정 보조지표] 본 문서는 의료진의 최종 임상적 진단을 대체할 수 없으며, 예방 및 모니터링 보조 목적으로만 활용해야 합니다.
        </div>
    """, unsafe_allow_html=True)
    
    # 요약 및 상세 분석 탭 분할
    tab_summary, tab_details = st.tabs(["📋 핵심 요약", "🔍 상세 분석 보고서"])
    
    with tab_summary:
        # 위험도 등급에 따른 배지 스타일
        badge_html = ""
        if status == "DANGER":
            badge_html = "<span class='status-badge-danger'>고위험 DANGER</span>"
        elif status == "WARNING":
            badge_html = "<span class='status-badge-warning'>주의 WARNING</span>"
        else:
            badge_html = "<span class='status-badge-normal'>정상 NORMAL</span>"
            
        # 이상 감지 세부 요약 리포팅
        violation_texts = []
        for v in boxplot_violations:
            activity = v.get("activity", "Unknown")
            outlier = v.get("outlier", "Normal")
            dev = v.get("deviation", 0.0)
            sign = "+" if dev > 0 else ""
            violation_texts.append(f"- **{activity}** 활동 점유율 {outlier} 이탈 (편차: {sign}{dev:.2f}%)")
            
        violations_summary = "\n".join(violation_texts) if violation_texts else "- 특이한 Boxplot 이탈 활동이 감지되지 않았습니다."
        
        # 복지사 권장 행동 초안
        ai_recommendation = alert.get("feedback_message") if alert else "권장 행동 정보가 없습니다."
        if not ai_recommendation:
            ai_recommendation = "대기 상태로 분석 중입니다."
            
        st.markdown(f"""
            <div class='glass-card' style='background: rgba(255, 255, 255, 0.02); border-color: rgba(255,255,255,0.05); margin-top: 10px;'>
                <p style='margin: 0 0 10px 0; font-size: 0.9rem; color: #a0aec0;'>🚨 분석 위험 상태</p>
                <div style='margin-bottom: 15px;'>{badge_html} &nbsp;&nbsp; <b>Z-score: {z_score:.2f}</b></div>
                <hr style='border-color: rgba(255,255,255,0.07); margin: 10px 0;'>
                <p style='margin: 10px 0 5px 0; font-size: 0.9rem; color: #a0aec0;'>📊 통계 범위 이탈(IQR) 요약</p>
                <div style='font-size: 0.9rem; line-height: 1.6;'>{violations_summary}</div>
                <hr style='border-color: rgba(255,255,255,0.07); margin: 10px 0;'>
                <p style='margin: 10px 0 5px 0; font-size: 0.9rem; color: #a0aec0;'>💡 AI 권장 조치 메모</p>
                <div style='font-size: 0.9rem; line-height: 1.6; background: rgba(155, 89, 182, 0.05); border-left: 3px solid #9b59b6; padding: 10px; border-radius: 4px;'>
                    {ai_recommendation}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    with tab_details:
        # 리포트 콘텐츠 표시 (글라스모피즘 스타일 카드)
        clean_report = xai_report.replace("[의사결정 보조지표] 본 문서는 의료진의 최종 임상적 진단을 대체할 수 없으며, 예방 및 모니터링 보조 목적으로만 활용해야 합니다.\n\n", "")
        st.markdown(f"""
            <div class='glass-card' style='background: rgba(255, 255, 255, 0.02); line-height: 1.6; white-space: pre-wrap; font-size: 0.95rem; border-color: rgba(255,255,255,0.05); margin-top: 10px;'>
                {clean_report}
            </div>
        """, unsafe_allow_html=True)

with col_feedback:
    st.markdown("<h3 style='color: #fff;'>⚡ 사회복지사 예방 조치 관문</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a0aec0; font-size: 0.85rem;'>경보 정탐/오탐 판정 및 안부 확인 결과 영속 저장</p>", unsafe_allow_html=True)

    if not alert:
        st.info("해당 보고서와 연결된 복지사 알림 객체가 존재하지 않습니다.")
    else:
        # 현재 조치 상태 알림 배너 노출
        if alert["action_status"] == "PENDING":
            st.warning("⚠️ 현재 조치 대기 중 (Action: PENDING)")
        elif alert["action_status"] == "APPROVED":
            st.success("✅ 정탐 승인 완료 및 보호자 비상 경보 활성화 (Action: APPROVED)")
        elif alert["action_status"] == "REJECTED":
            st.info("ℹ️ 오탐 감지 및 경보 반려 완료 (Action: REJECTED)")

        # 폼 구조 바인딩
        with st.form("feedback_form"):
            # 라디오 버튼 정탐/오탐 매핑
            action_options = {
                "PENDING": "대기 중 (Pending)",
                "APPROVED": "정탐 승인 및 보호자 비상 전송 (Approve)",
                "REJECTED": "오탐 감지 및 경보 반려 (Reject)"
            }
            
            # 초기 인덱스값 계산
            default_index = 0
            if alert["action_status"] == "APPROVED":
                default_index = 1
            elif alert["action_status"] == "REJECTED":
                default_index = 2
                
            selected_action = st.radio(
                "조치 결과 의사결정",
                options=list(action_options.keys()),
                format_func=lambda x: action_options[x],
                index=default_index
            )
            
            # 피드백 텍스트란
            feedback_text = st.text_area(
                "조치록 및 반려 피드백 사유",
                value=alert["feedback_message"] or "",
                placeholder="예: 단순 감기약 복용으로 인한 취침 패턴 편차 감지되어 반려 조치함. 혹은 안부 확인 결과 이상 무."
            )
            
            # 폼 제출 버튼
            submit_btn = st.form_submit_button("💾 피드백 저장 및 조치 완료")
            
            if submit_btn:
                # SQLite UPDATE 쿼리 동기 영속성 쓰기 실행
                # 다중 세션 락(Lock) 충돌 방지를 위해 단일 글로벌 커넥션 래퍼 활용
                db.update_caregiver_feedback(alert_id, selected_action, feedback_text)
                
                # 피드백 종류에 따라 알맞은 알림 배너 렌더링 (BDD 테스트 통과 수용 기준)
                if selected_action == "REJECTED":
                    st.success("반려 피드백이 성공적으로 전송되었습니다. (Action: REJECTED)")
                    # 실시간 주민 리스트 화면 갱신을 위해 주민 상태 등급을 'NORMAL'로 안전 복구
                    db.update_resident_status(resident_id, "NORMAL")
                elif selected_action == "APPROVED":
                    st.success("정탐 승인이 성공적으로 완료되었으며 보호자 위험 경보가 활성화되었습니다. (Action: APPROVED)")
                    db.update_resident_status(resident_id, "DANGER")
                else:
                    st.info("대기 상태로 조치 내용이 안전하게 보존되었습니다. (Action: PENDING)")
                
                # 화면 즉시 재갱신(Re-run)
                st.rerun()
