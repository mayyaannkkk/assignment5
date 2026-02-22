import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Argentina Football Analytics",
    
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        color: #75AADB;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #aaaaaa;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .section-header {
        font-size: 1.35rem;
        font-weight: 700;
        color: #75AADB;
        border-bottom: 2px solid #75AADB;
        padding-bottom: 4px;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    .interpretation-box {
        background-color: #1e2530;
        border-left: 4px solid #75AADB;
        border-radius: 6px;
        padding: 1rem 1.2rem;
        margin-top: 0.8rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #d0d8e4;
    }
    .stMetric label { font-size: 0.85rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Load & preprocess data ────────────────────────────────────────────────────
@st.cache_data
def load_data():
    results     = pd.read_csv("results.csv")
    goalscorers = pd.read_csv("goalscorers.csv")
    shootouts   = pd.read_csv("shootouts.csv")

    results["date"]     = pd.to_datetime(results["date"])
    goalscorers["date"] = pd.to_datetime(goalscorers["date"])
    shootouts["date"]   = pd.to_datetime(shootouts["date"])

    arg = results[(results["home_team"] == "Argentina") |
                  (results["away_team"] == "Argentina")].copy()

    def decompose(row):
        if row["home_team"] == "Argentina":
            return row["home_score"], row["away_score"], row["away_team"], True
        return row["away_score"], row["home_score"], row["home_team"], False

    decomposed = arg.apply(
        lambda r: pd.Series(decompose(r),
                            index=["arg_scored","arg_conceded","opponent","is_home"]), axis=1)
    arg = pd.concat([arg, decomposed], axis=1)

    arg["result"] = arg.apply(
        lambda r: "Win"  if r["arg_scored"] > r["arg_conceded"]
        else ("Draw" if r["arg_scored"] == r["arg_conceded"] else "Loss"), axis=1)
    arg["year"]   = arg["date"].dt.year
    arg["decade"] = (arg["year"] // 10 * 10).astype(str) + "s"

    arg_goals = goalscorers[goalscorers["team"] == "Argentina"].copy()
    arg_goals["year"] = arg_goals["date"].dt.year

    arg_shoot = shootouts[
        (shootouts["home_team"] == "Argentina") |
        (shootouts["away_team"] == "Argentina")].copy()
    arg_shoot["won"] = arg_shoot["winner"] == "Argentina"

    return arg, arg_goals, arg_shoot

arg, arg_goals, arg_shoot = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div style="text-align:center; margin-bottom:12px; margin-top:4px;">
      <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Soccerball.svg/240px-Soccerball.svg.png"
           width="95" style="border-radius:50%; box-shadow: 0 0 14px #75AADB; background:#fff; padding:4px;">
    </div>
    <h2 style="text-align:center; color:#75AADB; margin-top:0; font-size:1.3rem;">🇦🇷 Filters</h2>
    """,
    unsafe_allow_html=True,
)

min_yr, max_yr = int(arg["year"].min()), int(arg["year"].max())
year_range = st.sidebar.slider("Year Range", min_yr, max_yr, (1950, max_yr), step=1)

all_tournaments = sorted(arg["tournament"].unique())
default_tourn   = ["FIFA World Cup","Copa América",
                   "FIFA World Cup qualification","Friendly"]
sel_tournaments = st.sidebar.multiselect(
    "Tournaments", all_tournaments, default=default_tourn)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data Source:** [Kaggle – International Football Results 1872–2025]"
    "(https://www.kaggle.com/datasets/martj42/"
    "international-football-results-from-1872-to-2017)"
)

# ── Apply filters ─────────────────────────────────────────────────────────────
mask = (
    (arg["year"] >= year_range[0]) &
    (arg["year"] <= year_range[1]) &
    (arg["tournament"].isin(sel_tournaments))
)
df       = arg[mask].copy()
df_goals = arg_goals[
    (arg_goals["year"] >= year_range[0]) &
    (arg_goals["year"] <= year_range[1])
].copy()

df["venue"] = df["is_home"].map({True: "Home", False: "Away"})
df.loc[df["neutral"] == True, "venue"] = "Neutral"

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title"> Argentina Football Analytics Dashboard</p>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">A deep-dive into Argentina\'s international football journey '
    '— from historic Copa América triumphs to World Cup glory</p>',
    unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total   = len(df)
wins    = (df["result"] == "Win").sum()
draws   = (df["result"] == "Draw").sum()
losses  = (df["result"] == "Loss").sum()
win_pct = round(wins / total * 100, 1) if total else 0
goals_scored   = int(df["arg_scored"].sum())
goals_conceded = int(df["arg_conceded"].sum())

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Matches Played", f"{total:,}")
c2.metric("Wins",           f"{wins:,}")
c3.metric("Draws",          f"{draws:,}")
c4.metric("Losses",         f"{losses:,}")
c5.metric("Win Rate",       f"{win_pct}%")
c6.metric("Goals Scored",   f"{goals_scored:,}")
st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    " Overall Performance",
    " Goals & Scorers",
    " Tournaments & Rivals",
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overall Performance
# ════════════════════════════════════════════════════════════════════════════


    st.markdown('<p class="section-header">World Cup Goal Difference — Edition by Edition (Waterfall)</p>',
                unsafe_allow_html=True)

    wc_all = arg[arg["tournament"] == "FIFA World Cup"].copy()
    wc_yr  = (wc_all.groupby("year")
                     .agg(scored=("arg_scored","sum"),
                          conceded=("arg_conceded","sum"))
                     .reset_index())
    wc_yr["gd"] = wc_yr["scored"] - wc_yr["conceded"]

    annotations_map = {
        1978: " Champions",
        1986: " Champions",
        2022: " Champions",
        1958: "Worst campaign",
        2018: "Group-stage exit",
    }

    fig_wf = go.Figure(go.Waterfall(
        x=wc_yr["year"].astype(str).tolist(),
        y=wc_yr["gd"].tolist(),
        measure=["relative"] * len(wc_yr),
        text=[f"{'+' if g>0 else ''}{g}" for g in wc_yr["gd"]],
        textposition="outside",
        connector={"line": {"color":"#555","dash":"dot"}},
        increasing={"marker": {"color":"#75AADB"}},
        decreasing={"marker": {"color":"#D6001C"}},
    ))

    for _, row in wc_yr.iterrows():
        if row["year"] in annotations_map:
            offset = 1.3 if row["gd"] >= 0 else -2.0
            fig_wf.add_annotation(
                x=str(row["year"]),
                y=row["gd"] + offset,
                text=annotations_map[row["year"]],
                showarrow=False,
                font=dict(size=10, color="#F6BE00"),
            )

    fig_wf.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc", height=420,
        yaxis_title="Goal Difference", xaxis_title="World Cup Year",
        showlegend=False,
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    The waterfall chart traces Argentina's goal difference in every World Cup they've 
    participated in and it reads like a storybook of highs, lows, and redemption. 
    The 1930 debut stands out as a stunning positive, with Argentina scoring freely and 
    reaching the final. Then came painful dips  1958 was a disaster with a -5 goal 
    difference, and 2018 was another rough patch when the team shipped more goals than 
    they scored. But the peaks tell the real story: 1978 on home soil, Maradona's 
    magical 1986 run , and the 2022 triumph in Qatar. It's worth noticing that 
    
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<p class="section-header">Home vs Away Goals by Decade (Population Pyramid)</p>',
                unsafe_allow_html=True)

    all_decades = sorted(arg["decade"].unique())
    home_goals  = arg[arg["is_home"] == True].groupby("decade")["arg_scored"].sum()
    away_goals  = arg[arg["is_home"] == False].groupby("decade")["arg_scored"].sum()

    home_vals = [int(home_goals.get(d, 0)) for d in all_decades]
    away_vals = [int(away_goals.get(d, 0)) for d in all_decades]
    max_val   = max(max(home_vals), max(away_vals)) + 20

    fig_pyr = go.Figure()
    fig_pyr.add_trace(go.Bar(
        y=all_decades, x=[-v for v in home_vals],
        orientation="h", name="Home Goals",
        marker_color="#75AADB",
        text=[str(v) for v in home_vals],
        textposition="inside", insidetextanchor="middle",
    ))
    fig_pyr.add_trace(go.Bar(
        y=all_decades, x=away_vals,
        orientation="h", name="Away Goals",
        marker_color="#D6001C",
        text=[str(v) for v in away_vals],
        textposition="inside", insidetextanchor="middle",
    ))

    tick_vals = list(range(-max_val, max_val+1, 40))
    tick_text = [str(abs(v)) for v in tick_vals]

    fig_pyr.update_layout(
        barmode="relative",
        xaxis=dict(tickvals=tick_vals, ticktext=tick_text,
                   title="Goals Scored", color="#cccccc", gridcolor="#333"),
        yaxis=dict(title="Decade", color="#cccccc"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc", height=430,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        bargap=0.15,
    )
    fig_pyr.add_vline(x=0, line_color="#666", line_width=1.5)
    st.plotly_chart(fig_pyr, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    The population pyramid flips the traditional format to show one of the most interesting 
    patterns in Argentina's history, how their home and away scoring has evolved across 
    more than a century. In the early decades (1910s to 1940s), the gap between home and 
    away goals was enormous. Argentina would run riot at home but struggled to find the net 
    on the road common for international football back when travel was exhausting and away 
    fixtures were genuinely alien environments. What's remarkable is how that gap has 
    narrowed over time. By the 2000s and 2010s, Argentina were scoring nearly as freely 
    away from home as on familiar turf. This reflects the globalization of football 
    better preparation, improved squad depth, and the rise of a generation of players 
    who perform at the same elite level regardless of the zip code.
    </div>""", unsafe_allow_html=True)

with tab1:


    st.markdown('<p class="section-header">Performance Radar Across Four Eras</p>',
                unsafe_allow_html=True)

    eras = {
        "Maradona Era (1979–1990)":  (1979, 1990),
        "Post-Maradona (1991–2004)": (1991, 2004),
        "Messi Early (2005–2014)":   (2005, 2014),
        "Messi Peak (2015–2025)":    (2015, 2025),
    }
    radar_cats  = ["Win Rate %", "Avg Goals Scored", "Avg Goals Conceded (inv)",
                   "Clean Sheet %", "Draw Avoidance %"]
    era_colors  = ["#75AADB","#F6BE00","#D6001C","#4CAF50"]

    fig_radar = go.Figure()
    for (era_name, (y1, y2)), color in zip(eras.items(), era_colors):
        sub = df[(df["year"] >= y1) & (df["year"] <= y2)]
        if len(sub) == 0:
            continue
        wr   = (sub["result"] == "Win").mean() * 100
        asc  = sub["arg_scored"].mean() * 20
        acc  = max((1 - sub["arg_conceded"].mean() / 4) * 100, 0)
        cs   = (sub["arg_conceded"] == 0).mean() * 100
        da   = (sub["result"] != "Draw").mean() * 100
        vals = [wr, asc, acc, cs, da] + [wr]   # close the polygon
        cats = radar_cats + [radar_cats[0]]

        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=cats,
            fill="toself", name=era_name,
            line_color=color, fillcolor=color, opacity=0.25,
        ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(color="#aaaaaa"), gridcolor="#333"),
            angularaxis=dict(tickfont=dict(color="#cccccc"), gridcolor="#444"),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)", font_color="#cccccc",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=460, margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    The radar chart gives you a bird's-eye view of how Argentina's identity as a team has 
    shifted across four distinct chapters of their history. The Maradona era, while legendary 
    in memory, shows a lower win rate Maradona carried a squad that wasn't always the 
    strongest on paper, making his individual heroics even more remarkable. As you move through 
    the Post-Maradona years and into the Messi era, the overall shape of the pentagon expands 
    noticeably, Argentina got better in almost every dimension simultaneously. The most striking 
    change in the Messi Peak era (2015–2025) is the dramatic improvement in goals conceded 
    , reflecting how much more organized and defensively solid Argentina 
    became under Scaloni's management. 
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Goals & Scorers
# ════════════════════════════════════════════════════════════════════════════
with tab2:

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<p class="section-header">Goals Per Match by Tournament (Box Plot)</p>',
                    unsafe_allow_html=True)

        box_data = df[df["tournament"].isin(
            ["FIFA World Cup","Copa América","FIFA World Cup qualification","Friendly"]
        )].copy()
        short_names = {
            "FIFA World Cup":               "World Cup",
            "Copa América":                 "Copa América",
            "FIFA World Cup qualification": "WC Qual.",
            "Friendly":                     "Friendly",
        }
        box_data["Short"] = box_data["tournament"].map(short_names)

        fig_box = px.box(
            box_data, x="Short", y="arg_scored",
            color="Short",
            color_discrete_sequence=["#75AADB","#F6BE00","#D6001C","#4CAF50"],
            points="outliers",
            labels={"arg_scored":"Goals Scored","Short":"Tournament"},
            height=430,
        )
        fig_box.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#cccccc", showlegend=False,
        )
        st.plotly_chart(fig_box, use_container_width=True)

    
    with col_b:
        st.markdown('<p class="section-header">Top 15 Argentina Goal Scorers (All-Time)</p>',
                    unsafe_allow_html=True)

        non_own     = arg_goals[arg_goals["own_goal"] == False]
        top_scorers = non_own["scorer"].value_counts().head(15).reset_index()
        top_scorers.columns = ["Scorer","Goals"]
        top_scorers = top_scorers.sort_values("Goals")

        colors_bar = ["#D6001C" if s == "Lionel Messi" else "#75AADB"
                      for s in top_scorers["Scorer"]]

        fig_bar = go.Figure(go.Bar(
            x=top_scorers["Goals"], y=top_scorers["Scorer"],
            orientation="h",
            marker_color=colors_bar,
            text=top_scorers["Goals"], textposition="outside",
        ))
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#cccccc", height=430,
            xaxis_title="Goals", yaxis_title="",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    colx, coly = st.columns(2)
    with colx:
        st.markdown("""<div class="interpretation-box">
        The box plot reveals something that pure averages would hide — the spread and 
        variability of Argentina's scoring. Copa America matches show the widest spread 
        and highest outliers, Argentina once scored 12 in a single game!, telling you 
        these were often mismatched fixtures against weaker South American opposition in 
        earlier eras. World Cup matches, by contrast, show a tighter distribution with 
        fewer blowouts every opponent at a World Cup is dangerous and you can't take 
        liberties. World Cup Qualification sits in the middle, with occasional heavy wins 
        pulling the outliers up.
        </div>""", unsafe_allow_html=True)
    with coly:
        st.markdown("""<div class="interpretation-box">
        The top scorer chart is almost impossible to look at without being struck by the 
        gulf between Messi and everyone else. With 63 goals, he's nearly double Batistuta's 
        37 and Batistuta himself was considered one of the most lethal strikers of his 
        generation. What makes Messi's record more impressive is that for years he was 
        unfairly criticized for not performing for Argentina the way he did for Barcelona. 
        This chart quietly settles that argument. 
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


    st.markdown('<p class="section-header">3D View — Scoring vs Conceding Across Years & Tournaments</p>',
                unsafe_allow_html=True)

    major_t = ["FIFA World Cup","Copa América","FIFA World Cup qualification","Friendly"]
    df_3d   = df[df["tournament"].isin(major_t)].copy()
    df_3d_g = (df_3d.groupby(["year","tournament"])
                    .agg(avg_scored=("arg_scored","mean"),
                         avg_conceded=("arg_conceded","mean"),
                         matches=("result","count"),
                         win_rate=("result", lambda x: (x=="Win").mean()*100))
                    .reset_index())
    df_3d_g = df_3d_g[df_3d_g["matches"] >= 2]

    color_map_3d = {
        "FIFA World Cup":               "#F6BE00",
        "Copa América":                 "#75AADB",
        "FIFA World Cup qualification": "#D6001C",
        "Friendly":                     "#4CAF50",
    }

    fig_3d = go.Figure()
    for tourn, color in color_map_3d.items():
        sub = df_3d_g[df_3d_g["tournament"] == tourn]
        if sub.empty:
            continue
        fig_3d.add_trace(go.Scatter3d(
            x=sub["year"],
            y=sub["avg_scored"],
            z=sub["avg_conceded"],
            mode="markers",
            name=tourn,
            marker=dict(
                size=sub["win_rate"] / 8 + 3,
                color=color, opacity=0.82,
                line=dict(width=0.5, color="#222"),
            ),
            text=sub.apply(
                lambda r: (f"{r['tournament']}<br>Year: {r['year']}<br>"
                           f"Avg Scored: {r['avg_scored']:.2f}<br>"
                           f"Avg Conceded: {r['avg_conceded']:.2f}<br>"
                           f"Win Rate: {r['win_rate']:.0f}%"), axis=1),
            hoverinfo="text",
        ))

    fig_3d.update_layout(
        scene=dict(
            xaxis=dict(title="Year", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="#333", color="#ccc"),
            yaxis=dict(title="Avg Goals Scored", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="#333", color="#ccc"),
            zaxis=dict(title="Avg Goals Conceded", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="#333", color="#ccc"),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)", font_color="#cccccc",
        height=520, legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig_3d, use_container_width=True)
    st.caption(" Tip: Click and drag to rotate the 3D chart. Bubble size reflects win rate.")

    st.markdown("""<div class="interpretation-box">
    This 3D scatter plots Argentina's attacking and defensive performance through time across 
    all four major tournament types and rotating it reveals patterns that a flat chart 
    would bury entirely. The ideal zone is high on the goals scored axis and low on the goals 
    conceded axis that's where Argentina's best seasons cluster. Copa América points blue
    tend to sit higher on the scoring axis, reflecting Argentina's dominance against fellow 
    South American nations. World Cup points yellow are more compressed and conservative 
    tighter scorelines because the opposition is at its absolute best
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Tournaments & Rivals
# ════════════════════════════════════════════════════════════════════════════
with tab3:

  
    st.markdown('<p class="section-header">Argentina vs Top 10 Rivals — Head-to-Head Record</p>',
                unsafe_allow_html=True)

    top_rivals  = df["opponent"].value_counts().head(10).index
    rival_df    = df[df["opponent"].isin(top_rivals)].copy()
    rival_stats = (rival_df.groupby(["opponent","result"])
                            .size().unstack(fill_value=0).reset_index())
    for col in ["Win","Draw","Loss"]:
        if col not in rival_stats.columns:
            rival_stats[col] = 0
    rival_stats["Total"]    = rival_stats["Win"] + rival_stats["Draw"] + rival_stats["Loss"]
    rival_stats["Win Rate"] = rival_stats["Win"] / rival_stats["Total"] * 100

    fig_scatter = px.scatter(
        rival_stats, x="Total", y="Win Rate",
        size="Win", color="Win Rate",
        color_continuous_scale=["#D6001C","#F6BE00","#75AADB"],
        text="opponent", height=460,
        labels={"Total":"Matches Played","Win Rate":"Win Rate (%)","Win":"Wins"},
    )
    fig_scatter.update_traces(textposition="top center", textfont_color="#ffffff")
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc", coloraxis_showscale=False,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    This scatter puts Argentina's ten most-played opponents in a single picture, and the 
    story it tells is one of almost total regional dominance  with one glaring exception. 
    Teams like Chile, Venezuela, Bolivia, and Ecuador sit with high win rates, meaning 
    Argentina has played them often and beaten them regularly. Uruguay is fascinating  
    the most-played opponent of all, and yet Argentina's win rate against them is lower 
    than almost any other South American rival. That's the Río de la Plata derby for you: 
    historically fierce, pride driven, and never comfortable. Brazil sits similarly, 
    confirming that the Argentina–Brazil fixture is genuinely two-sided. Bubble size 
    representing wins shows that Uruguay and Brazil, despite lower win rates, still have 
    the largest bubbles simply because Argentina has faced them so many times.
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

  
    st.markdown('<p class="section-header">Penalty Shootout Record</p>',
                unsafe_allow_html=True)

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        won_s  = int(arg_shoot["won"].sum())
        lost_s = int((~arg_shoot["won"]).sum())

        fig_shoot = go.Figure(go.Pie(
            labels=["Won","Lost"],
            values=[won_s, lost_s],
            hole=0.52,
            marker_colors=["#75AADB","#D6001C"],
            textinfo="label+percent",
        ))
        fig_shoot.add_annotation(
            text=f"{won_s}W – {lost_s}L",
            x=0.5, y=0.5,
            font_size=17, showarrow=False, font_color="#ffffff",
        )
        fig_shoot.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cccccc", height=320,
            showlegend=False,
        )
        st.plotly_chart(fig_shoot, use_container_width=True)

    with col_p2:
        shoot_display = arg_shoot.copy()
        shoot_display["Outcome"]  = shoot_display["won"].map({True:" Won","":""}).fillna(" Lost")
        shoot_display["won_bool"] = shoot_display["won"]
        shoot_display["Outcome"]  = shoot_display["won_bool"].apply(
            lambda x: " Won" if x else " Lost")
        shoot_display["Opponent"] = shoot_display.apply(
            lambda r: r["away_team"] if r["home_team"] == "Argentina" else r["home_team"],
            axis=1,
        )
        shoot_display["Year"] = shoot_display["date"].dt.year
        st.dataframe(
            shoot_display[["Year","Opponent","Outcome"]]
            .sort_values("Year", ascending=False)
            .reset_index(drop=True),
            use_container_width=True, height=320,
        )

    st.markdown("""<div class="interpretation-box">
    Penalty shootouts are often called a lottery, but Argentina's 65% success rate across 
    23 appearances tells a different story this is a team that tends to hold its nerve 
    when the pressure is at its absolute peak. The losses are painful chapters in national 
    memory the 2006 World Cup exit to Germany stings particularly, but the overall 
    record shows a mentality that doesn't buckle. The 2022 World Cup run, which included 
    shootout wins against Netherlands in the quarterfinal and France in an all-time classic 
    final, really cemented Argentina's reputation as a side that rises to the occasion. 
    Mental strength, goalkeeper quality, and the self belief to step up under the world's 
    gaze, Argentina consistently shows all three, and the numbers back it up.
    </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#666; font-size:0.85rem;'>"
    "Built with Streamlit · Data: International Football Results 1872–2025 (Kaggle) · "
    "DSA 506 Visual Analytics – SUNY Polytechnic Institute · Spring 2026"
    "</p>",
    unsafe_allow_html=True,
)
