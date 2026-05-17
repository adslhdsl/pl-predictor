import streamlit as st
import requests
import openpyxl
from pathlib import Path

TEAM_NAME_KO = {
    'Arsenal': '아스날',
    'Manchester City': '맨시티',
    'Manchester United': '맨유',
    'Aston Villa': '빌라',
    'Liverpool': '리버풀',
    'Bournemouth': '본머스',
    'AFC Bournemouth': '본머스',
    'Brighton and Hove Albion': '브라이튼',
    'Brighton & Hove Albion': '브라이튼',
    'Brentford': '브랜트포드',
    'Chelsea': '첼시',
    'Everton': '에버튼',
    'Fulham': '풀럼',
    'Sunderland': '선더랜드',
    'Newcastle United': '뉴캐슬',
    'Leeds United': '리즈',
    'Crystal Palace': '크리스탈팰리스',
    'Nottingham Forest': '노팅엄',
    'Tottenham Hotspur': '토트넘',
    'West Ham United': '웨스트햄',
    'Burnley': '번리',
    'Wolverhampton Wanderers': '울버햄튼',
}

def load_predictions():
    path = Path(__file__).parent / 'predictions.xlsx'
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    names = [h for h in rows[0] if h]
    predictions = {name: [] for name in names}
    for row in rows[1:]:
        for idx, name in enumerate(names):
            predictions[name].append(row[idx + 1])
    return predictions

PREDICTIONS = load_predictions()


@st.cache_data(ttl=3600)
def fetch_actual():
    url = "https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    standings = []
    for group in data.get("children", []):
        for entry in group.get("standings", {}).get("entries", []):
            name_en = entry["team"]["displayName"]
            name_ko = TEAM_NAME_KO.get(name_en, name_en)
            pts = next(s["value"] for s in entry["stats"] if s["name"] == "points")
            standings.append((pts, name_ko))

    standings.sort(key=lambda x: -x[0])
    return [(team, int(pts)) for pts, team in standings[:20]]


def compare(actual, predictions):
    scores = {}
    for name, pred in predictions.items():
        scores[name] = sum(1 for i in range(20) if pred[i] == actual[i])
    return scores


def compute_analysis(actual, predictions):
    actual_rank = {team: i + 1 for i, team in enumerate(actual)}
    result = {}
    for name, pred in predictions.items():
        pred_rank = {team: i + 1 for i, team in enumerate(pred)}
        errors = [
            (abs(actual_rank[team] - pred_rank[team]), team, actual_rank[team], pred_rank[team])
            for team in actual_rank
            if team in pred_rank
        ]
        avg = sum(e[0] for e in errors) / len(errors)
        worst = max(errors, key=lambda x: x[0])
        result[name] = {'avg': avg, 'worst_team': worst[1], 'worst_err': worst[0],
                        'worst_actual': worst[2], 'worst_pred': worst[3]}
    return result


def render_analysis_html(analysis, winner):
    sorted_names = sorted(analysis, key=lambda n: analysis[n]['avg'])
    rows = ''
    for i, name in enumerate(sorted_names):
        a = analysis[name]
        is_best = i == 0
        row_style = 'background:rgba(124,58,237,0.08);' if is_best else ''
        name_style = 'color:#a78bfa;font-weight:700;' if is_best else 'color:rgba(255,255,255,0.85);font-weight:600;'
        badge = ' <span style="font-size:10px;background:rgba(124,58,237,0.3);color:#c4b5fd;padding:1px 6px;border-radius:4px;vertical-align:middle">최소</span>' if is_best else ''
        direction = '▲' if a['worst_pred'] > a['worst_actual'] else '▼'
        dir_color = '#f87171' if direction == '▲' else '#60a5fa'
        rows += f"""
        <tr style="{row_style}">
          <td style="text-align:left;padding-left:16px;{name_style}">{name}{badge}</td>
          <td style="font-weight:700;color:#e2e8f0;">{a['avg']:.1f}칸</td>
          <td style="text-align:left;padding-left:12px;">
            <div style="color:rgba(255,255,255,0.9);font-weight:700;margin-bottom:3px;">{a['worst_team']}</div>
            <div style="font-size:11px;color:rgba(255,255,255,0.4);">
              예측 {a['worst_pred']}위
              <span style="color:{dir_color};margin:0 3px">{direction}</span>
              실제 {a['worst_actual']}위
              <span style="background:rgba(239,68,68,0.15);color:#fca5a5;
                           padding:1px 6px;border-radius:4px;margin-left:4px">±{a['worst_err']}칸</span>
            </div>
          </td>
        </tr>"""

    return f"""
    <style>
      .an-wrap {{ border-radius:16px;border:1px solid rgba(255,255,255,0.07);overflow:hidden; }}
      .an-table {{ border-collapse:collapse;width:100%;font-size:13px;
                   font-family:'Inter','Noto Sans KR',sans-serif; }}
      .an-table th {{ background:#2d0046;color:rgba(255,255,255,0.5);padding:11px 12px;
                      font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
                      border-bottom:1px solid rgba(124,58,237,0.35); }}
      .an-table th:first-child {{ text-align:left;padding-left:16px; }}
      .an-table th:last-child  {{ text-align:left;padding-left:12px; }}
      .an-table td {{ padding:13px 12px;border-bottom:1px solid rgba(255,255,255,0.04);
                      color:rgba(255,255,255,0.6);text-align:center;white-space:nowrap; }}
      .an-table td:last-child {{ white-space:normal;word-break:keep-all;line-height:1.6; }}
      .an-table tr:last-child td {{ border-bottom:none; }}
      .an-table tr:hover td {{ background:rgba(255,255,255,0.02) !important; }}
    </style>
    <div class="an-wrap">
      <table class="an-table">
        <thead>
          <tr>
            <th>예측자</th>
            <th>평균 오차</th>
            <th>최대 실수</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


def render_html_table(actual, points, predictions, scores):
    names = list(predictions.keys())
    header_cells = '<th>순위</th><th>실제 순위</th>' + ''.join(f'<th>{n}</th>' for n in names)

    rows_html = ''
    for i in range(20):
        rank = i + 1
        act = actual[i]

        if rank <= 5:
            rank_cls = 'rank-ucl'
        elif rank <= 7:
            rank_cls = 'rank-euro'
        elif rank >= 18:
            rank_cls = 'rank-rel'
        else:
            rank_cls = ''

        pts = points.get(act, '')
        row = f'<td class="rank-num {rank_cls}">{rank}</td>'
        row += f'<td class="team-name">{act}<span class="pts-badge">{pts}pts</span></td>'
        for name in names:
            pred = predictions[name][i]
            cell_cls = 'hit' if pred == act else 'miss'
            row += f'<td class="{cell_cls}">{pred}</td>'
        rows_html += f'<tr>{row}</tr>'

    return f"""
    <style>
      .pl-wrap {{
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.07);
        background: rgba(255,255,255,0.02);
      }}
      .pl-table {{
        border-collapse: collapse;
        width: 100%;
        min-width: 320px;
        font-size: 12px;
        font-family: 'Inter', 'Noto Sans KR', sans-serif;
      }}
      .pl-table th {{
        background: linear-gradient(135deg, #2d0046 0%, #4c1d95 100%);
        color: rgba(255,255,255,0.85);
        padding: 12px 10px;
        text-align: center;
        font-weight: 600;
        font-size: 11px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        white-space: nowrap;
        border-bottom: 1px solid rgba(124,58,237,0.4);
      }}
      .pl-table td {{
        padding: 9px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        white-space: nowrap;
        color: rgba(255,255,255,0.75);
        text-align: center;
      }}
      .pl-table tr:last-child td {{ border-bottom: none; }}
      .pl-table tr:hover td {{ background: rgba(255,255,255,0.03) !important; }}

      /* Sticky: 순위 컬럼 */
      .pl-table th:nth-child(1),
      .pl-table td:nth-child(1) {{
        position: sticky;
        left: 0;
        z-index: 2;
        width: 40px;
        min-width: 40px;
      }}
      /* Sticky: 실제순위 컬럼 */
      .pl-table th:nth-child(2),
      .pl-table td:nth-child(2) {{
        position: sticky;
        left: 40px;
        z-index: 2;
        border-right: 1px solid rgba(255,255,255,0.08);
        min-width: 72px;
      }}
      /* Sticky 헤더는 z-index 한 단계 더 높게 */
      .pl-table th:nth-child(1),
      .pl-table th:nth-child(2) {{
        z-index: 3;
        background: #2d0046;
      }}
      /* Sticky body 셀 배경 (투명이면 뒤 내용이 비쳐 보임) */
      .pl-table td:nth-child(1),
      .pl-table td:nth-child(2) {{
        background: #0d0b1a;
      }}
      .pl-table tr:hover td:nth-child(1),
      .pl-table tr:hover td:nth-child(2) {{
        background: #13102a !important;
      }}

      .rank-num {{
        font-weight: 700;
        font-size: 11px;
        color: rgba(255,255,255,0.3) !important;
      }}
      .rank-ucl  {{ color: #60a5fa !important; }}
      .rank-euro {{ color: #fbbf24 !important; }}
      .rank-rel  {{ color: #f87171 !important; }}
      .team-name {{
        font-weight: 600;
        text-align: left !important;
        padding-left: 14px !important;
        color: rgba(255,255,255,0.92) !important;
      }}
      .pts-badge {{
        display: block;
        font-size: 10px;
        font-weight: 500;
        color: rgba(255,255,255,0.3);
        margin-top: 1px;
      }}
      .hit {{
        background: rgba(16,185,129,0.12) !important;
        color: #34d399 !important;
        font-weight: 700;
      }}
      .miss {{
        color: rgba(255,255,255,0.28) !important;
      }}
    </style>
    <div class="pl-wrap">
      <table class="pl-table">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """


# ── Page config ───────────────────────────────────────────────
st.set_page_config(page_title='PL 예측 결과', page_icon='⚽', layout='centered')

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', 'Noto Sans KR', sans-serif;
  }

  .stApp {
    background: radial-gradient(ellipse at 20% 0%, #1e0a3c 0%, #0b0b1a 55%, #0a1628 100%);
  }

  #MainMenu, footer, header { visibility: hidden; }

  /* Streamlit 기본 블록 패딩 제거 */
  .block-container { padding-top: 1rem !important; }
  .stMarkdown, .element-container { margin-bottom: 0 !important; }
  .stMarkdown p { margin: 0 !important; }

  .stButton > button {
    background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 22px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.45) !important;
    transition: all 0.2s ease !important;
  }
  .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(124,58,237,0.6) !important;
  }

  hr { border-color: rgba(255,255,255,0.07) !important; margin: 20px 0 !important; }

  .stSpinner > div { border-top-color: #7c3aed !important; }
  .stAlert { border-radius: 12px !important; }

  /* Score grid: 항상 한 줄 */
  .score-grid {
    display: flex;
    flex-wrap: nowrap;
    gap: 8px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
  }
  .score-grid > div {
    flex: 1 1 0;
    min-width: 0;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.35) !important;
    font-weight: 600;
    font-size: 13px;
    border-radius: 8px 8px 0 0;
    padding: 8px 18px;
  }
  .stTabs [aria-selected="true"] {
    background: rgba(124,58,237,0.12) !important;
    color: #a78bfa !important;
    border-bottom: 2px solid #7c3aed !important;
  }
  .stTabs [data-baseweb="tab-panel"] { padding-top: 20px; }

  /* Mobile tweaks */
  @media (max-width: 480px) {
    .pl-header-title { font-size: 22px !important; }
    .pl-header-wrap  { padding: 20px 0 16px !important; }
    .stButton > button { width: 100% !important; }
  }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:8px 0 20px">
  <div style="font-size:10px;font-weight:700;letter-spacing:5px;color:#7c3aed;text-transform:uppercase;margin-bottom:6px">
    2025–26 Season
  </div>
  <div style="font-size:15px;font-weight:600;letter-spacing:6px;color:rgba(255,255,255,0.5);text-transform:uppercase;margin-bottom:8px">
    Premier League
  </div>
  <div class="pl-header-title" style="font-size:32px;font-weight:900;color:white;letter-spacing:-0.5px;line-height:1.2">
    순위 예측 대결
  </div>
  <div style="width:40px;height:3px;background:linear-gradient(90deg,#7c3aed,#a855f7);margin:12px auto 0;border-radius:99px"></div>
</div>
""", unsafe_allow_html=True)

col_l, col_c, col_r = st.columns([1, 1, 1])
with col_c:
    if st.button('🔄 현재 순위 불러오기', use_container_width=True):
        st.cache_data.clear()

with st.spinner('순위 불러오는 중...'):
    try:
        actual_data = fetch_actual()
        actual = [t for t, _ in actual_data]
        points = {t: p for t, p in actual_data}
    except Exception as e:
        st.error(f'순위를 불러오지 못했습니다: {e}')
        st.stop()

scores = compare(actual, PREDICTIONS)
winner = max(scores, key=scores.get)
sorted_scores = sorted(scores.items(), key=lambda x: -x[1])


# ── Score cards ───────────────────────────────────────────────
cards_html = ''
for i, (name, score) in enumerate(sorted_scores):
    if i == 0:
        bg     = 'linear-gradient(135deg, rgba(251,191,36,0.18), rgba(245,158,11,0.08))'
        border = '1px solid rgba(251,191,36,0.35)'
        score_color = '#fbbf24'
        icon   = '🏆<br>'
    else:
        bg     = 'rgba(255,255,255,0.04)'
        border = '1px solid rgba(255,255,255,0.07)'
        score_color = '#a78bfa'
        icon   = ''

    cards_html += f"""
    <div style="
      flex:1;min-width:72px;
      text-align:center;
      padding:18px 8px 14px;
      background:{bg};
      border:{border};
      border-radius:16px;
      backdrop-filter:blur(12px);
    ">
      <div style="font-size:18px;line-height:1.2;margin-bottom:4px">{icon}</div>
      <div style="font-size:10px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;
                  color:rgba(255,255,255,0.4);margin-bottom:8px">{name}</div>
      <div style="font-size:30px;font-weight:900;color:{score_color};line-height:1">{score}</div>
      <div style="font-size:10px;color:rgba(255,255,255,0.3);margin-top:5px;font-weight:500">적중</div>
    </div>"""

st.markdown(f"""
<div style="margin:8px 0 28px">
  <div style="font-size:10px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;
              color:rgba(255,255,255,0.25);margin-bottom:12px;text-align:center">SCOREBOARD</div>
  <div class="score-grid">{cards_html}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

analysis = compute_analysis(actual, PREDICTIONS)

tab1, tab2 = st.tabs(['📊 순위 비교', '🔍 상세 분석'])

with tab1:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:16px;margin:0 0 14px;justify-content:flex-end;flex-wrap:wrap">
      <div style="display:flex;gap:12px;font-size:11px;color:rgba(255,255,255,0.35);font-weight:500">
        <span><span style="color:#60a5fa">●</span> UCL</span>
        <span><span style="color:#fbbf24">●</span> 유로파</span>
        <span><span style="color:#f87171">●</span> 강등권</span>
      </div>
      <div style="display:flex;gap:8px;font-size:11px">
        <span style="background:rgba(16,185,129,0.15);color:#34d399;
                     padding:3px 10px;border-radius:6px;font-weight:700">✓ 적중</span>
        <span style="background:rgba(255,255,255,0.05);color:rgba(255,255,255,0.3);
                     padding:3px 10px;border-radius:6px;font-weight:500">✗ 오답</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(render_html_table(actual, points, PREDICTIONS, scores), unsafe_allow_html=True)

with tab2:
    st.markdown(render_analysis_html(analysis, winner), unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-top:16px;padding:14px 16px;background:rgba(255,255,255,0.03);
                border-radius:12px;border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:11px;color:rgba(255,255,255,0.35);line-height:1.8;">
        <span style="color:rgba(255,255,255,0.5);font-weight:600;">평균 오차</span>
        &nbsp;— 20개 팀 각각의 |예측 순위 − 실제 순위| 평균. 낮을수록 전반적으로 근접하게 맞힌 것.<br>
        <span style="color:rgba(255,255,255,0.5);font-weight:600;">최대 실수</span>
        &nbsp;— 한 팀에서 예측이 가장 크게 빗나간 경우.
      </div>
    </div>
    """, unsafe_allow_html=True)
