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
    return [team for _, team in standings[:20]]


def compare(actual, predictions):
    scores = {}
    for name, pred in predictions.items():
        scores[name] = sum(1 for i in range(20) if pred[i] == actual[i])
    return scores


def render_html_table(actual, predictions, scores):
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

        row = f'<td class="rank-num {rank_cls}">{rank}</td>'
        row += f'<td class="team-name">{act}</td>'
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

  /* Score grid: 한 줄 → 모바일에서 2열 자동 wrap */
  .score-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
    gap: 8px;
  }

  /* Mobile tweaks */
  @media (max-width: 480px) {
    .pl-header-title { font-size: 22px !important; }
    .pl-header-wrap  { padding: 20px 0 16px !important; }
    .score-grid { grid-template-columns: repeat(2, 1fr); }
    .stButton > button { width: 100% !important; }
  }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="pl-header-wrap" style="text-align:center;padding:36px 0 24px">
  <div style="font-size:11px;font-weight:700;letter-spacing:4px;color:#7c3aed;text-transform:uppercase;margin-bottom:10px">
    2025–26 SEASON
  </div>
  <h1 class="pl-header-title" style="font-size:30px;font-weight:900;color:white;margin:0;letter-spacing:-0.5px;line-height:1.15">
    ⚽ 프리미어리그<br>순위 예측 대결
  </h1>
  <div style="width:44px;height:3px;background:linear-gradient(90deg,#7c3aed,#a855f7);margin:16px auto 0;border-radius:99px"></div>
</div>
""", unsafe_allow_html=True)

if st.button('🔄 현재 순위 불러오기'):
    st.cache_data.clear()

with st.spinner('순위 불러오는 중...'):
    try:
        actual = fetch_actual()
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


# ── Legend ────────────────────────────────────────────────────
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


# ── Table ─────────────────────────────────────────────────────
st.markdown(render_html_table(actual, PREDICTIONS, scores), unsafe_allow_html=True)
