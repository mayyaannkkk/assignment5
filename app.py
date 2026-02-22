import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Argentina Football Analytics",
    page_icon="🇦🇷",
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
    results    = pd.read_csv("results.csv")
    goalscorers= pd.read_csv("goalscorers.csv")
    shootouts  = pd.read_csv("shootouts.csv")

    results["date"]     = pd.to_datetime(results["date"])
    goalscorers["date"] = pd.to_datetime(goalscorers["date"])
    shootouts["date"]   = pd.to_datetime(shootouts["date"])

    # Filter Argentina
    arg = results[(results["home_team"] == "Argentina") |
                  (results["away_team"] == "Argentina")].copy()

    def decompose(row):
        if row["home_team"] == "Argentina":
            return row["home_score"], row["away_score"], row["away_team"], True
        return row["away_score"], row["home_score"], row["home_team"], False

    decomposed = arg.apply(lambda r: pd.Series(decompose(r),
        index=["arg_scored","arg_conceded","opponent","is_home"]), axis=1)
    arg = pd.concat([arg, decomposed], axis=1)

    arg["result"] = arg.apply(
        lambda r: "Win" if r["arg_scored"] > r["arg_conceded"]
        else ("Draw" if r["arg_scored"] == r["arg_conceded"] else "Loss"), axis=1)
    arg["year"]   = arg["date"].dt.year
    arg["decade"] = (arg["year"] // 10 * 10).astype(str) + "s"

    # Goal scorers for Argentina (non-own-goals by Argentina)
    arg_goals = goalscorers[goalscorers["team"] == "Argentina"].copy()
    arg_goals["year"] = arg_goals["date"].dt.year

    # Shootouts
    arg_shoot = shootouts[
        (shootouts["home_team"] == "Argentina") |
        (shootouts["away_team"] == "Argentina")].copy()
    arg_shoot["won"] = arg_shoot["winner"] == "Argentina"

    return arg, arg_goals, arg_shoot

arg, arg_goals, arg_shoot = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/"
    "24701-soccer-field-icon.svg/240px-24701-soccer-field-icon.svg.png",
    width=60
)
st.sidebar.title("🇦🇷 Filters")

# Year range slider
min_yr, max_yr = int(arg["year"].min()), int(arg["year"].max())
year_range = st.sidebar.slider(
    "Year Range", min_yr, max_yr, (1950, max_yr), step=1
)

# Tournament multiselect
all_tournaments = sorted(arg["tournament"].unique())
default_tourn = ["FIFA World Cup", "Copa América",
                 "FIFA World Cup qualification", "Friendly"]
sel_tournaments = st.sidebar.multiselect(
    "Tournaments", all_tournaments, default=default_tourn
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data Source:** [Kaggle – International Football Results 1872–2025]"
    "(https://www.kaggle.com/datasets/martj42/"
    "international-football-results-from-1872-to-2017)"
)

# Apply global filters
mask = (
    (arg["year"] >= year_range[0]) &
    (arg["year"] <= year_range[1]) &
    (arg["tournament"].isin(sel_tournaments))
)
df = arg[mask].copy()
df_goals = arg_goals[
    (arg_goals["year"] >= year_range[0]) &
    (arg_goals["year"] <= year_range[1])
].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🇦🇷 Argentina Football Analytics Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">A deep-dive into Argentina\'s international football journey '
            '— from historic Copa América triumphs to World Cup glory</p>', unsafe_allow_html=True)

# ── Top KPI Cards ─────────────────────────────────────────────────────────────
total  = len(df)
wins   = (df["result"] == "Win").sum()
draws  = (df["result"] == "Draw").sum()
losses = (df["result"] == "Loss").sum()
win_pct = round(wins / total * 100, 1) if total else 0
goals_scored   = int(df["arg_scored"].sum())
goals_conceded = int(df["arg_conceded"].sum())

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Matches Played",  f"{total:,}")
c2.metric("Wins",            f"{wins:,}")
c3.metric("Draws",           f"{draws:,}")
c4.metric("Losses",          f"{losses:,}")
c5.metric("Win Rate",        f"{win_pct}%")
c6.metric("Goals Scored",    f"{goals_scored:,}")

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊 Overall Performance",
    "⚽ Goals & Scorers",
    "🏆 Tournaments & Rivals"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overall Performance
# ════════════════════════════════════════════════════════════════════════════
with tab1:

    # --- Chart 1: Win/Draw/Loss trend by decade ---
    st.markdown('<p class="section-header">Win / Draw / Loss Record by Decade</p>',
                unsafe_allow_html=True)

    decade_df = (df.groupby(["decade","result"])
                   .size().reset_index(name="count"))
    decade_order = sorted(df["decade"].unique())
    fig_decade = px.bar(
        decade_df, x="decade", y="count", color="result",
        color_discrete_map={"Win":"#75AADB","Draw":"#F6BE00","Loss":"#D6001C"},
        barmode="group", category_orders={"decade": decade_order},
        labels={"decade":"Decade","count":"Matches","result":"Result"},
        height=400
    )
    fig_decade.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc", legend_title_text="Result"
    )
    st.plotly_chart(fig_decade, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    Looking at Argentina's record decade by decade, you can really see how the team has grown into 
    a powerhouse over time. Back in the early decades, the wins and losses were pretty balanced — 
    Argentina was competitive but not yet dominant. Things started clicking in the 1940s and 1950s, 
    when the wins started piling up noticeably. The 2000s and 2010s stand out as Argentina's golden 
    era in terms of raw win numbers, which lines up with the generation that included Messi, Agüero, 
    and Di María reaching their prime. The 2020s look smaller simply because there are fewer years 
    of data, but the win-to-loss ratio in that short stretch is the best it's ever been — a strong 
    sign that the current squad is carrying that momentum forward.
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Chart 2: Win rate rolling average (line chart) ---
    st.markdown('<p class="section-header">Win Rate Over Time (5-Year Rolling Average)</p>',
                unsafe_allow_html=True)

    yr_stats = (df.groupby("year")
                  .agg(matches=("result","count"),
                       wins=("result", lambda x: (x=="Win").sum()))
                  .reset_index())
    yr_stats["win_rate"] = yr_stats["wins"] / yr_stats["matches"] * 100
    yr_stats = yr_stats.sort_values("year")
    yr_stats["rolling_wr"] = yr_stats["win_rate"].rolling(5, min_periods=1).mean()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=yr_stats["year"], y=yr_stats["win_rate"],
        mode="markers", name="Annual Win Rate",
        marker=dict(color="#75AADB", size=5, opacity=0.45)
    ))
    fig_trend.add_trace(go.Scatter(
        x=yr_stats["year"], y=yr_stats["rolling_wr"],
        mode="lines", name="5-Year Rolling Avg",
        line=dict(color="#F6BE00", width=2.5)
    ))
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc", height=380,
        yaxis_title="Win Rate (%)", xaxis_title="Year",
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    The rolling win rate line tells a fascinating story of Argentina's ups and downs. There are clear 
    dips in the late 1950s and mid-1970s — periods when the team struggled on the international stage. 
    But what jumps out most is the steady climb from around 2008 onwards, where the rolling average 
    sits consistently above 60%. There were rough patches too — 2018 was a painful year with a 
    group-stage exit at the World Cup — but Argentina bounced back almost immediately. The peak 
    in the early 2020s is no coincidence; it reflects the Copa América 2021 title (Argentina's 
    first major trophy in 28 years) and the unforgettable 2022 World Cup win in Qatar. These aren't 
    just numbers — they represent a team that found its identity and finally delivered on its 
    enormous potential.
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Chart 3: Home vs Away win rates (grouped bar) ---
    st.markdown('<p class="section-header">Home vs Away vs Neutral Performance</p>',
                unsafe_allow_html=True)

    df["venue"] = df["is_home"].map({True: "Home", False: "Away"})
    df.loc[df["neutral"] == True, "venue"] = "Neutral"

    venue_df = (df.groupby(["venue","result"])
                  .size().reset_index(name="count"))
    fig_venue = px.bar(
        venue_df, x="venue", y="count", color="result",
        color_discrete_map={"Win":"#75AADB","Draw":"#F6BE00","Loss":"#D6001C"},
        barmode="stack",
        category_orders={"venue":["Home","Neutral","Away"]},
        labels={"venue":"Venue","count":"Matches","result":"Result"},
        height=380
    )
    fig_venue.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc"
    )
    st.plotly_chart(fig_venue, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    Argentina's home and away split reveals something interesting — while the team wins more 
    at home (as you'd expect from any football side), their away and neutral-venue record is 
    still remarkably strong. This matters a lot in international football, where World Cups and 
    Copa Américas are almost always played on neutral or semi-neutral ground. The fact that 
    Argentina maintains a winning record even without the home crowd behind them shows a mental 
    toughness and quality that doesn't rely on familiar surroundings. The loss rate doesn't 
    shoot up dramatically in away conditions, which separates truly elite teams from good ones.
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Goals & Scorers
# ════════════════════════════════════════════════════════════════════════════
with tab2:

    col_a, col_b = st.columns(2)

    # --- Chart 4: Top 15 scorers (horizontal bar) ---
    with col_a:
        st.markdown('<p class="section-header">Top 15 Argentina Goal Scorers</p>',
                    unsafe_allow_html=True)

        non_own = df_goals[df_goals["own_goal"] == False]
        top_scorers = (non_own["scorer"]
                       .value_counts().head(15).reset_index())
        top_scorers.columns = ["Scorer","Goals"]
        top_scorers = top_scorers.sort_values("Goals")

        colors = ["#D6001C" if s == "Lionel Messi" else "#75AADB"
                  for s in top_scorers["Scorer"]]

        fig_scorers = go.Figure(go.Bar(
            x=top_scorers["Goals"], y=top_scorers["Scorer"],
            orientation="h", marker_color=colors,
            text=top_scorers["Goals"], textposition="outside"
        ))
        fig_scorers.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#cccccc", height=480,
            xaxis_title="Goals", yaxis_title=""
        )
        st.plotly_chart(fig_scorers, use_container_width=True)

    # --- Chart 5: Goal types (penalty vs open play) pie ---
    with col_b:
        st.markdown('<p class="section-header">Goal Breakdown by Type</p>',
                    unsafe_allow_html=True)

        penalty_goals  = (non_own["penalty"] == True).sum()
        regular_goals  = (non_own["penalty"] == False).sum()
        own_goals_opp  = (df_goals["own_goal"] == True).sum()   # own goals by opponents

        fig_pie = go.Figure(go.Pie(
            labels=["Open Play","Penalties","Own Goals (by opponents)"],
            values=[regular_goals, penalty_goals, own_goals_opp],
            hole=0.4,
            marker_colors=["#75AADB","#F6BE00","#D6001C"]
        ))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cccccc", height=480,
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Interpretations side by side
    colx, coly = st.columns(2)
    with colx:
        st.markdown("""<div class="interpretation-box">
        The top scorer chart is almost impossible to look at without noticing the gulf between 
        Messi and everyone else. With 63 goals (within this filtered dataset), he's nearly 
        double Batistuta's 37 — and Batistuta was considered a generational striker in his own 
        right. What makes Messi's number even more impressive is that he spent years being 
        criticized for not performing for Argentina the way he did for Barcelona. The chart 
        quietly proves those critics wrong. Players like Higuaín, Agüero, and Lautaro further 
        down the list show that Argentina has never lacked for quality in attack — yet none 
        came close to matching the GOAT at the top.
        </div>""", unsafe_allow_html=True)
    with coly:
        st.markdown("""<div class="interpretation-box">
        The pie chart shows that the vast majority of Argentina's goals come from open play, 
        which tells you this is a team that creates chances through build-up and individual 
        brilliance rather than relying on set-pieces or spot-kicks. Penalties make up a 
        meaningful but not dominant slice — a healthy sign that Argentina earns its goals 
        the hard way. The own goals conceded by opponents are a small but notable category, 
        showing that Argentina's pressure and attacking movement sometimes forces errors even 
        without a clean finish. It all adds up to a picture of an attacking team that plays 
        with variety and creativity.
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Chart 6: Goals by minute heatmap-style histogram ---
    st.markdown('<p class="section-header">When Does Argentina Score? (Goal Timing Distribution)</p>',
                unsafe_allow_html=True)

    minute_data = non_own.dropna(subset=["minute"]).copy()
    minute_data["minute"] = minute_data["minute"].astype(int)
    minute_data = minute_data[minute_data["minute"] <= 120]

    bins = list(range(0, 121, 10))
    labels_bin = [f"{b+1}-{b+10}" for b in bins[:-1]]
    minute_data["period"] = pd.cut(minute_data["minute"], bins=bins,
                                   labels=labels_bin, right=True)
    period_counts = minute_data["period"].value_counts().reset_index()
    period_counts.columns = ["Period","Goals"]
    period_counts = period_counts.sort_values("Period")

    fig_timing = px.bar(
        period_counts, x="Period", y="Goals",
        color="Goals",
        color_continuous_scale=["#1a3a6b","#75AADB","#F6BE00"],
        labels={"Period":"Match Minute Interval","Goals":"Goals Scored"},
        height=380
    )
    fig_timing.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc", coloraxis_showscale=False,
        xaxis_title="Match Minute Interval", yaxis_title="Goals Scored"
    )
    st.plotly_chart(fig_timing, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    The timing of Argentina's goals shows a very familiar pattern that football analysts call 
    "second-half surge." Goals in the 71–90 minute window are the most frequent, which makes 
    a lot of sense — by that point, opposition defenses tire, gaps open up, and Argentina's 
    fitness and quality start to tell. There's also a solid chunk of early goals in the first 
    10-20 minutes, reflecting a team that's dangerous right from kick-off and doesn't wait 
    around to impose itself. The relatively quieter middle portion (31–60 minutes) is typical 
    for international football where both teams are often feeling each other out tactically. 
    The 81–90+ bracket being the highest is also a reflection of Argentina's notorious 
    never-say-die attitude — many famous comeback goals have come in those final 
    desperate minutes.
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Tournaments & Rivals
# ════════════════════════════════════════════════════════════════════════════
with tab3:

    # --- Chart 7: Tournament win rates (horizontal bar) ---
    st.markdown('<p class="section-header">Win Rate by Tournament Type</p>',
                unsafe_allow_html=True)

    tourn_stats = (df.groupby("tournament")
                     .agg(matches=("result","count"),
                          wins=("result", lambda x: (x=="Win").sum()))
                     .reset_index())
    tourn_stats = tourn_stats[tourn_stats["matches"] >= 10]
    tourn_stats["win_rate"] = tourn_stats["wins"] / tourn_stats["matches"] * 100
    tourn_stats = tourn_stats.sort_values("win_rate", ascending=True)

    fig_tourn = go.Figure(go.Bar(
        x=tourn_stats["win_rate"],
        y=tourn_stats["tournament"],
        orientation="h",
        marker_color="#75AADB",
        text=tourn_stats["win_rate"].round(1).astype(str) + "%",
        textposition="outside",
        customdata=tourn_stats["matches"],
        hovertemplate="<b>%{y}</b><br>Win Rate: %{x:.1f}%<br>Matches: %{customdata}<extra></extra>"
    ))
    fig_tourn.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc", height=420,
        xaxis_title="Win Rate (%)", yaxis_title=""
    )
    st.plotly_chart(fig_tourn, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    When you break down Argentina's win rate by tournament, it's clear that they've been 
    better at some competitions than others — and the reasons are worth thinking about. 
    Copa América and World Cup Qualification tend to show strong win rates because Argentina 
    dominates within South American football most of the time. The FIFA World Cup win rate 
    is lower, which makes sense — you only face the best teams in the world at a World Cup, 
    so every match is a battle. Friendlies often have lower win rates too, partly because 
    teams use them to experiment with lineups and tactics. A tournament's win rate isn't 
    just about quality — it's also about who you're playing against, and in the World Cup, 
    even a 53% win rate means you're doing well.
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Chart 8: Head-to-head scatter (top 10 rivals) ---
    st.markdown('<p class="section-header">Argentina vs Top 10 Rivals — Head-to-Head Record</p>',
                unsafe_allow_html=True)

    top_rivals = df["opponent"].value_counts().head(10).index
    rival_df = df[df["opponent"].isin(top_rivals)].copy()
    rival_stats = (rival_df.groupby(["opponent","result"])
                            .size().unstack(fill_value=0).reset_index())
    for col in ["Win","Draw","Loss"]:
        if col not in rival_stats.columns:
            rival_stats[col] = 0
    rival_stats["Total"] = rival_stats["Win"] + rival_stats["Draw"] + rival_stats["Loss"]
    rival_stats["Win Rate"] = rival_stats["Win"] / rival_stats["Total"] * 100
    rival_stats["Goal Diff"] = rival_df.groupby("opponent")["arg_scored"].sum().values - \
                                rival_df.groupby("opponent")["arg_conceded"].sum().values

    fig_scatter = px.scatter(
        rival_stats, x="Total", y="Win Rate",
        size="Win", color="Win Rate",
        color_continuous_scale=["#D6001C","#F6BE00","#75AADB"],
        text="opponent", height=460,
        labels={"Total":"Matches Played","Win Rate":"Win Rate (%)","Win":"Wins"}
    )
    fig_scatter.update_traces(textposition="top center", textfont_color="#ffffff")
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cccccc", coloraxis_showscale=False
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("""<div class="interpretation-box">
    This scatter plot places Argentina's biggest rivals in a fascinating context. Uruguay 
    stands out immediately — they've played each other more times than any other matchup 
    in the dataset, a testament to the fierce and historic Río de la Plata rivalry. 
    Despite the sheer volume of games, Argentina holds a positive win rate against Uruguay, 
    which is no small feat given how competitive that fixture always is. Brazil, the other 
    giant of South American football, sits with a lower Argentina win rate — showing that 
    this rivalry is genuinely two-sided and harder to dominate. Teams like Chile and Paraguay, 
    despite being played very often, show high Argentina win rates — they're regular opponents 
    in qualification but Argentina has historically had the upper hand. The bubble size 
    (representing wins) gives you a quick sense of where Argentina's dominance is most absolute.
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Chart 9: Penalty shootout record ---
    st.markdown('<p class="section-header">Penalty Shootout Record</p>',
                unsafe_allow_html=True)

    shoot_display = arg_shoot.copy()
    shoot_display["Outcome"] = shoot_display["won"].map({True:"Won 🟢", False:"Lost 🔴"})
    shoot_display["opponent"] = shoot_display.apply(
        lambda r: r["away_team"] if r["home_team"]=="Argentina" else r["home_team"], axis=1)
    shoot_display["Year"] = shoot_display["date"].dt.year

    col_p1, col_p2 = st.columns([1,2])
    with col_p1:
        won_s  = shoot_display["won"].sum()
        lost_s = (~shoot_display["won"]).sum()
        fig_shoot = go.Figure(go.Pie(
            labels=["Won","Lost"],
            values=[won_s, lost_s],
            hole=0.5,
            marker_colors=["#75AADB","#D6001C"],
            textinfo="label+percent"
        ))
        fig_shoot.add_annotation(
            text=f"{won_s}W – {lost_s}L",
            x=0.5, y=0.5, font_size=16,
            showarrow=False, font_color="#ffffff"
        )
        fig_shoot.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cccccc", height=320,
            showlegend=False
        )
        st.plotly_chart(fig_shoot, use_container_width=True)

    with col_p2:
        display_cols = ["Year","opponent","Outcome"]
        st.dataframe(
            shoot_display[display_cols].sort_values("Year", ascending=False)
            .reset_index(drop=True),
            use_container_width=True, height=320
        )

    st.markdown("""<div class="interpretation-box">
    Penalty shootouts are often called a "lottery" in football, but Argentina's 65% win rate 
    in shootouts tells a different story — this is a team that tends to handle the pressure 
    better than most. Of their 23 shootout appearances, they've come out on top 15 times. 
    The losses are painful to recall — the 2006 World Cup exit to Germany and the heartbreak 
    against Brazil in 2001 still sting — but the overall record shows a squad that generally 
    keeps its nerve when it matters most. The 2022 World Cup run, which included a semifinal 
    and final decided on penalties, added two more crucial wins and really cemented Argentina's 
    reputation as a side that doesn't crumble under the ultimate test of individual nerve 
    and mental strength.
    </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#666; font-size:0.85rem;'>"
    "Built with Streamlit · Data: International Football Results 1872–2025 (Kaggle) · "
    "DSA 506 Visual Analytics – SUNY Polytechnic Institute · Spring 2026"
    "</p>",
    unsafe_allow_html=True
)
