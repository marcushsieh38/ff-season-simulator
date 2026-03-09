import streamlit as st
import numpy as np
import pandas as pd
import requests
import gc

st.set_page_config(
    page_title="Sleeper Season Sim",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface2: #1a1a24;
    --border: #2a2a3a;
    --accent: #00ff87;
    --accent2: #ff6b35;
    --accent3: #4f9cf9;
    --text: #e8e8f0;
    --muted: #6b6b80;
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif;
}

.main .block-container {
    padding: 2rem 3rem;
    max-width: 1400px;
}

h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.05em; }

.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(3rem, 8vw, 7rem);
    line-height: 0.9;
    letter-spacing: 0.02em;
    background: linear-gradient(135deg, #00ff87 0%, #4f9cf9 50%, #ff6b35 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
}

.hero-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    color: var(--muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 3rem;
}

.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent3));
}

.stat-card:hover { border-color: var(--accent); }

.stat-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.5rem;
    color: var(--accent);
    line-height: 1;
}

.stat-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.25rem;
}

.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    letter-spacing: 0.08em;
    color: var(--text);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
}

.info-box {
    background: rgba(79,156,249,0.06);
    border: 1px solid rgba(79,156,249,0.2);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    font-size: 0.85rem;
    color: #a0b4c8;
    margin-bottom: 1.5rem;
}

.warn-box {
    background: rgba(255,107,53,0.06);
    border: 1px solid rgba(255,107,53,0.2);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    font-size: 0.85rem;
    color: #c8a090;
    margin-bottom: 1.5rem;
}

div[data-testid="stTextInput"] input {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1rem !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,255,135,0.1) !important;
}

div[data-testid="stTextInput"] label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

.stButton > button {
    background: linear-gradient(135deg, #00ff87, #00d4a0) !important;
    color: #0a0a0f !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.1em !important;
    padding: 0.6rem 2rem !important;
    transition: all 0.2s !important;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(0,255,135,0.25) !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

.stProgress > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent3)) !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}

.stExpander {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    background: var(--surface) !important;
}

footer { display: none !important; }
#MainMenu { display: none !important; }
header { display: none !important; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_all_players():
    try:
        response = requests.get("https://api.sleeper.app/v1/players/nfl", timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_league_info(league_id):
    try:
        response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}", timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_league_rosters(league_id):
    try:
        response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters", timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_league_users(league_id):
    try:
        response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users", timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_week_matchups(league_id, week):
    try:
        response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}", timeout=15)
        response.raise_for_status()
        data = response.json()
        return data if data else []
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def build_historical_player_stats(prior_league_id):
    player_weekly_scores = {}

    for week in range(1, 18):
        matchups = fetch_week_matchups(prior_league_id, week)
        if not matchups:
            continue

        for matchup in matchups:
            players_points = matchup.get("players_points", {})
            for player_id, points in players_points.items():
                if points is not None and points > 0:
                    if player_id not in player_weekly_scores:
                        player_weekly_scores[player_id] = []
                    player_weekly_scores[player_id].append(float(points))

    player_stats = {}
    for player_id, scores in player_weekly_scores.items():
        if len(scores) >= 3:
            arr = np.array(scores)
            player_stats[player_id] = {
                "mean": float(np.mean(arr)),
                "variance": float(np.var(arr, ddof=1)) if len(arr) > 1 else 5.0,
                "n_weeks": len(arr),
                "scores": scores
            }

    return player_stats


def compute_lognormal_params_vectorized(means_2d, variances_1d):
    variances_2d = np.maximum(variances_1d[np.newaxis, :], 0.01)
    means_2d = np.maximum(means_2d, 0.1)
    mu = np.log(means_2d ** 2 / np.sqrt(variances_2d + means_2d ** 2))
    sigma = np.sqrt(np.log(1 + variances_2d / means_2d ** 2))
    sigma = np.maximum(sigma, 0.05)
    return mu, sigma


def generate_schedule(num_teams, num_weeks=14):
    teams = list(range(num_teams))
    schedule = []

    if num_teams % 2 != 0:
        teams.append(-1)

    n = len(teams)
    fixed = teams[0]
    rotating = teams[1:]

    for week in range(num_weeks):
        rotated = rotating[week % len(rotating):] + rotating[:week % len(rotating)]
        all_week_teams = [fixed] + rotated
        matchups = []
        for i in range(n // 2):
            t1 = all_week_teams[i]
            t2 = all_week_teams[n - 1 - i]
            if t1 != -1 and t2 != -1:
                matchups.append((t1, t2))
        schedule.append(matchups)

    return schedule


def compute_positional_priors(all_players_data, player_stats):
    skill_positions = {"QB", "RB", "WR", "TE", "K"}
    positional_data = {pos: [] for pos in skill_positions}

    for player_id, stats_info in player_stats.items():
        position = all_players_data.get(player_id, {}).get("position", "")
        if position in skill_positions:
            positional_data[position].append(stats_info["mean"])

    positional_priors = {}
    for pos, means in positional_data.items():
        if means:
            top_50 = sorted(means, reverse=True)[:50]
            pos_mean = float(np.mean(top_50))
            pos_var = float(np.var(top_50)) if len(top_50) > 1 else 5.0
            positional_priors[pos] = {"mean": pos_mean, "variance": max(pos_var, 1.0)}
        else:
            positional_priors[pos] = {"mean": 8.0, "variance": 10.0}

    return positional_priors


def compute_qb_receiver_correlations(roster_player_ids, all_players_data, player_stats):
    qb_ids = [pid for pid in roster_player_ids
               if all_players_data.get(pid, {}).get("position") == "QB"
               and pid in player_stats]
    receiver_ids = [pid for pid in roster_player_ids
                    if all_players_data.get(pid, {}).get("position") in ("WR", "TE")
                    and pid in player_stats]

    correlations = {}
    for qb_id in qb_ids:
        qb_scores = player_stats[qb_id]["scores"]
        if len(qb_scores) < 5:
            continue
        for rec_id in receiver_ids:
            rec_scores = player_stats[rec_id]["scores"]
            min_len = min(len(qb_scores), len(rec_scores))
            if min_len < 5:
                continue
            qb_arr = np.array(qb_scores[:min_len])
            rec_arr = np.array(rec_scores[:min_len])
            if np.std(qb_arr) > 0 and np.std(rec_arr) > 0:
                correlations[(qb_id, rec_id)] = float(np.corrcoef(qb_arr, rec_arr)[0, 1])

    return correlations


def resolve_starter_indices(roster, valid_players, all_players_data):
    declared_starters = roster.get("starters") or []
    declared_starters = [pid for pid in declared_starters if pid and pid != "0"]

    if declared_starters:
        starter_set = set(declared_starters)
        indices = [i for i, pid in enumerate(valid_players) if pid in starter_set]
        if indices:
            return indices

    positional_starter_counts = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1}
    pos_groups = {}
    for i, pid in enumerate(valid_players):
        pos = all_players_data.get(pid, {}).get("position", "")
        if pos in positional_starter_counts:
            pos_groups.setdefault(pos, []).append(i)

    starter_indices = []
    for pos, count in positional_starter_counts.items():
        if pos in pos_groups:
            starter_indices.extend(pos_groups[pos][:count])

    return starter_indices if starter_indices else list(range(len(valid_players)))


def run_monte_carlo_simulation(
    rosters_data,
    users_data,
    all_players_data,
    player_stats,
    positional_priors,
    schedule,
    num_simulations=10000,
    num_weeks=14
):
    num_teams = len(rosters_data)
    user_map = {u["user_id"]: u.get("display_name", u["user_id"]) for u in users_data}
    team_names = [user_map.get(r.get("owner_id", ""), f"Team {r['roster_id']}") for r in rosters_data]

    skill_positions = {"QB", "RB", "WR", "TE", "K"}
    team_players = []
    team_starter_indices = []
    team_initial_means = []
    team_static_variances = []
    team_correlations = []

    for roster in rosters_data:
        player_ids = roster.get("players") or []
        valid_players = [pid for pid in player_ids
                         if all_players_data.get(pid, {}).get("position") in skill_positions]
        team_players.append(valid_players)
        team_starter_indices.append(resolve_starter_indices(roster, valid_players, all_players_data))

        means = []
        variances = []
        for pid in valid_players:
            if pid in player_stats:
                m = player_stats[pid]["mean"]
                v = player_stats[pid]["variance"]
            else:
                pos = all_players_data.get(pid, {}).get("position", "WR")
                prior = positional_priors.get(pos, {"mean": 8.0, "variance": 10.0})
                m = prior["mean"]
                v = prior["variance"]
            means.append(m)
            variances.append(v)

        team_initial_means.append(np.array(means, dtype=np.float32) if means else np.array([1.0], dtype=np.float32))
        team_static_variances.append(np.array(variances, dtype=np.float32) if variances else np.array([1.0], dtype=np.float32))
        team_correlations.append(
            compute_qb_receiver_correlations(valid_players, all_players_data, player_stats)
        )

    team_dynamic_means = [
        np.tile(base_means, (num_simulations, 1)).astype(np.float32)
        for base_means in team_initial_means
    ]

    wins_matrix = np.zeros((num_simulations, num_teams), dtype=np.float32)
    points_matrix = np.zeros((num_simulations, num_teams), dtype=np.float32)

    bayesian_prior_weight = 3.0
    bayesian_observation_weight = 1.0
    bayesian_total_weight = bayesian_prior_weight + bayesian_observation_weight

    for week_idx in range(num_weeks):
        week_team_scores = np.zeros((num_simulations, num_teams), dtype=np.float32)

        for team_idx in range(num_teams):
            valid_players = team_players[team_idx]
            if not valid_players:
                continue

            current_means = team_dynamic_means[team_idx]
            static_variances = team_static_variances[team_idx]

            mu_matrix, sigma_matrix = compute_lognormal_params_vectorized(current_means, static_variances)

            raw_scores = np.exp(
                np.random.randn(num_simulations, len(valid_players)).astype(np.float32) * sigma_matrix + mu_matrix
            ).astype(np.float32)

            updated_means = (
                bayesian_prior_weight * current_means + bayesian_observation_weight * raw_scores
            ) / bayesian_total_weight
            team_dynamic_means[team_idx] = updated_means

            qb_indices = [i for i, pid in enumerate(valid_players)
                          if all_players_data.get(pid, {}).get("position") == "QB"]

            if qb_indices:
                qb_col_idx = qb_indices[0]
                qb_scores_col = raw_scores[:, qb_col_idx]
                qb_p80_threshold = np.percentile(qb_scores_col, 80)
                high_qb_mask = qb_scores_col > qb_p80_threshold
                qb_pid = valid_players[qb_col_idx]

                for rec_col_idx, rec_pid in enumerate(valid_players):
                    rec_pos = all_players_data.get(rec_pid, {}).get("position", "")
                    if rec_pos not in ("WR", "TE"):
                        continue
                    corr = team_correlations[team_idx].get((qb_pid, rec_pid), 0.0)
                    if abs(corr) > 0.1:
                        raw_scores[high_qb_mask, rec_col_idx] *= (1.0 + corr * 0.15)

            starter_indices = team_starter_indices[team_idx]
            if starter_indices:
                team_weekly_scores = np.sum(raw_scores[:, starter_indices], axis=1)
            else:
                team_weekly_scores = np.sum(raw_scores, axis=1)
            week_team_scores[:, team_idx] = team_weekly_scores.astype(np.float32)

            del raw_scores, mu_matrix, sigma_matrix, updated_means
            gc.collect()

        points_matrix += week_team_scores

        for t1_idx, t2_idx in (schedule[week_idx] if week_idx < len(schedule) else []):
            if t1_idx < num_teams and t2_idx < num_teams:
                t1_scores = week_team_scores[:, t1_idx]
                t2_scores = week_team_scores[:, t2_idx]
                wins_matrix[:, t1_idx] += (t1_scores > t2_scores).astype(np.float32)
                wins_matrix[:, t2_idx] += (t2_scores > t1_scores).astype(np.float32)

        del week_team_scores
        gc.collect()

    num_playoff_teams = min(4, num_teams // 2)
    sorted_wins = np.sort(wins_matrix, axis=1)
    playoff_cutoff_per_sim = sorted_wins[:, -num_playoff_teams]
    playoff_matrix = wins_matrix >= playoff_cutoff_per_sim[:, np.newaxis]
    playoff_probs = np.mean(playoff_matrix, axis=0)

    mean_wins = np.mean(wins_matrix, axis=0)
    std_wins = np.std(wins_matrix, axis=0)
    mean_points = np.mean(points_matrix, axis=0)

    results = {
        "team_names": team_names,
        "playoff_probs": playoff_probs.tolist(),
        "mean_wins": mean_wins.tolist(),
        "std_wins": std_wins.tolist(),
        "mean_points": mean_points.tolist(),
        "wins_distribution": wins_matrix,
        "points_distribution": points_matrix,
        "num_simulations": num_simulations
    }

    del sorted_wins, playoff_matrix
    gc.collect()

    return results


def compute_luck_index(rosters_data, results):
    luck_indices = []
    for i, roster in enumerate(rosters_data):
        actual_wins = roster.get("settings", {}).get("wins", 0)
        expected_wins = results["mean_wins"][i]
        luck_indices.append({
            "team": results["team_names"][i],
            "actual_wins": actual_wins,
            "expected_wins": round(expected_wins, 1),
            "luck_index": round(actual_wins - expected_wins, 2)
        })
    return sorted(luck_indices, key=lambda x: x["luck_index"], reverse=True)


st.markdown('<div class="hero-title">SLEEPER<br>SEASON SIM</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">⬡ Bayesian Monte Carlo Engine &nbsp;·&nbsp; 10,000 Iterations &nbsp;·&nbsp; Log-Normal Distributions</div>', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1], gap="large")
with col_l:
    current_league_id = st.text_input("Current League ID", placeholder="e.g. 1234567890")
with col_r:
    prior_league_id = st.text_input("Prior Year League ID", placeholder="e.g. 0987654321")

num_sims = st.select_slider(
    "Simulation Iterations",
    options=[1000, 2500, 5000, 10000],
    value=5000
)

st.markdown('<div class="info-box">💡 <strong>How it works:</strong> Historical scoring data is pulled from your prior season to fit per-player Log-Normal distributions. A Bayesian conjugate update adjusts each player\'s expectation week-over-week within every simulation path. Per-simulation optimal lineup selection and vectorized playoff counting produce the final projections.</div>', unsafe_allow_html=True)

run_simulation = st.button("⚡ RUN SIMULATION", use_container_width=True)

if run_simulation:
    if not current_league_id or not prior_league_id:
        st.markdown('<div class="warn-box">⚠️ Please enter both League IDs to run the simulation.</div>', unsafe_allow_html=True)
        st.stop()

    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.markdown('<div class="hero-sub">→ FETCHING LEAGUE DATA...</div>', unsafe_allow_html=True)
    progress_bar.progress(5)

    league_info = fetch_league_info(current_league_id)
    if not league_info:
        st.error("❌ Could not fetch current league. Check your League ID.")
        st.stop()

    rosters_data = fetch_league_rosters(current_league_id)
    users_data = fetch_league_users(current_league_id)
    if not rosters_data or not users_data:
        st.error("❌ Could not fetch roster or user data.")
        st.stop()

    progress_bar.progress(15)
    status_text.markdown('<div class="hero-sub">→ LOADING NFL PLAYER DATABASE...</div>', unsafe_allow_html=True)

    all_players_data = fetch_all_players()
    if not all_players_data:
        st.error("❌ Could not fetch player database from Sleeper.")
        st.stop()

    progress_bar.progress(30)
    status_text.markdown('<div class="hero-sub">→ BUILDING HISTORICAL PRIORS FROM PRIOR SEASON...</div>', unsafe_allow_html=True)

    player_stats = build_historical_player_stats(prior_league_id)
    if not player_stats:
        st.warning("⚠️ No historical data found for prior league. Using positional defaults.")

    progress_bar.progress(50)
    status_text.markdown('<div class="hero-sub">→ COMPUTING POSITIONAL PRIORS & QB CORRELATIONS...</div>', unsafe_allow_html=True)

    positional_priors = compute_positional_priors(all_players_data, player_stats)
    num_teams = len(rosters_data)

    schedule_check = fetch_week_matchups(current_league_id, 1)
    if schedule_check:
        roster_ids = [r["roster_id"] for r in rosters_data]
        matchup_map = {}
        for m in schedule_check:
            mid = m.get("matchup_id")
            rid = m.get("roster_id")
            if mid and rid:
                matchup_map.setdefault(mid, []).append(
                    roster_ids.index(rid) if rid in roster_ids else 0
                )
        week1_schedule = [(pair[0], pair[1]) for pair in matchup_map.values() if len(pair) == 2]
        schedule = [week1_schedule] * 14
        schedule_source = "official"
    else:
        schedule = generate_schedule(num_teams, 14)
        schedule_source = "generated"

    progress_bar.progress(60)
    status_text.markdown(f'<div class="hero-sub">→ RUNNING {num_sims:,} MONTE CARLO ITERATIONS...</div>', unsafe_allow_html=True)

    np.random.seed(42)
    results = run_monte_carlo_simulation(
        rosters_data=rosters_data,
        users_data=users_data,
        all_players_data=all_players_data,
        player_stats=player_stats,
        positional_priors=positional_priors,
        schedule=schedule,
        num_simulations=num_sims,
        num_weeks=14
    )

    progress_bar.progress(95)
    status_text.markdown('<div class="hero-sub">→ COMPUTING LUCK INDEX & FINALIZING...</div>', unsafe_allow_html=True)

    luck_data = compute_luck_index(rosters_data, results)

    progress_bar.progress(100)
    status_text.empty()
    progress_bar.empty()

    league_name = league_info.get("name", "Your League")
    st.markdown(f'<div class="section-header">📊 {league_name.upper()} — SIMULATION RESULTS</div>', unsafe_allow_html=True)

    schedule_badge = "🟢 Official Schedule" if schedule_source == "official" else "🟡 Generated Round-Robin Schedule"
    st.markdown(f'<div class="info-box">{schedule_badge} &nbsp;·&nbsp; {num_sims:,} simulations completed &nbsp;·&nbsp; {len(player_stats):,} players with historical data</div>', unsafe_allow_html=True)

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{num_teams}</div><div class="stat-label">Teams</div></div>', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{num_sims:,}</div><div class="stat-label">Simulations</div></div>', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{len(player_stats):,}</div><div class="stat-label">Historical Players</div></div>', unsafe_allow_html=True)
    with m_col4:
        avg_pts = round(float(np.mean(results["mean_points"])), 1)
        st.markdown(f'<div class="stat-card"><div class="stat-value">{avg_pts}</div><div class="stat-label">Avg Proj. Points</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🏆 Playoff Odds", "📈 Win Distribution", "🍀 Luck Index"])

    with tab1:
        st.markdown('<div class="section-header">PLAYOFF PROBABILITY RANKINGS</div>', unsafe_allow_html=True)

        playoff_df = pd.DataFrame({
            "Team": results["team_names"],
            "Playoff %": [round(p * 100, 1) for p in results["playoff_probs"]],
            "Projected Wins": [round(w, 1) for w in results["mean_wins"]],
            "Win Std Dev": [round(s, 2) for s in results["std_wins"]],
            "Proj. Points": [round(p, 1) for p in results["mean_points"]]
        }).sort_values("Playoff %", ascending=False).reset_index(drop=True)
        playoff_df.index = playoff_df.index + 1

        st.dataframe(
            playoff_df,
            use_container_width=True,
            column_config={
                "Playoff %": st.column_config.ProgressColumn("Playoff %", format="%.1f%%", min_value=0, max_value=100),
                "Projected Wins": st.column_config.NumberColumn("Proj. Wins", format="%.1f"),
                "Win Std Dev": st.column_config.NumberColumn("Win Std Dev", format="%.2f"),
                "Proj. Points": st.column_config.NumberColumn("Proj. Points", format="%.1f"),
            },
            height=min(500, 70 + 35 * num_teams)
        )

    with tab2:
        st.markdown('<div class="section-header">WIN DISTRIBUTION — SELECT YOUR TEAM</div>', unsafe_allow_html=True)

        selected_team_name = st.selectbox("Select Team", options=results["team_names"], label_visibility="collapsed")
        team_idx = results["team_names"].index(selected_team_name)
        team_wins = results["wins_distribution"][:, team_idx]

        bins = np.arange(0, int(team_wins.max()) + 2) - 0.5
        hist_counts, bin_edges = np.histogram(team_wins, bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        hist_df = pd.DataFrame({
            "Wins": bin_centers.astype(int),
            "Simulations": hist_counts,
            "Frequency (%)": (hist_counts / num_sims * 100).round(1)
        })

        mean_w = results["mean_wins"][team_idx]
        playoff_p = results["playoff_probs"][team_idx]
        p10 = int(np.percentile(team_wins, 10))
        p90 = int(np.percentile(team_wins, 90))

        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            st.markdown(f'<div class="stat-card"><div class="stat-value">{mean_w:.1f}</div><div class="stat-label">Expected Wins</div></div>', unsafe_allow_html=True)
        with hc2:
            st.markdown(f'<div class="stat-card"><div class="stat-value">{playoff_p*100:.0f}%</div><div class="stat-label">Playoff Probability</div></div>', unsafe_allow_html=True)
        with hc3:
            st.markdown(f'<div class="stat-card"><div class="stat-value">{p10}–{p90}</div><div class="stat-label">P10–P90 Win Range</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.bar_chart(hist_df.set_index("Wins")["Simulations"], use_container_width=True)

        with st.expander("📋 Full Distribution Table"):
            st.dataframe(hist_df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown('<div class="section-header">LUCK INDEX — ACTUAL VS EXPECTED WINS</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">The Luck Index measures how many more (or fewer) wins a team has vs their simulation-expected record. Positive = lucky schedule; negative = unlucky.</div>', unsafe_allow_html=True)

        luck_df = pd.DataFrame(luck_data)
        if "team" in luck_df.columns:
            luck_df.columns = ["Team", "Actual Wins", "Expected Wins", "Luck Index"]
            st.dataframe(
                luck_df,
                use_container_width=True,
                column_config={
                    "Luck Index": st.column_config.NumberColumn("Luck Index", format="%.2f", help="Positive = Lucky, Negative = Unlucky"),
                    "Expected Wins": st.column_config.NumberColumn(format="%.1f"),
                },
                hide_index=True,
                height=min(500, 70 + 35 * num_teams)
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<div style='font-family: DM Mono, monospace; font-size: 0.7rem; color: #3a3a50; text-align: center; letter-spacing: 0.1em;'>
    SLEEPER SEASON SIM &nbsp;·&nbsp; BAYESIAN MONTE CARLO ENGINE &nbsp;·&nbsp; BUILT WITH NUMPY VECTORIZATION
    </div>""", unsafe_allow_html=True)

else:
    st.markdown("""
    <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 2rem;'>
        <div class='stat-card'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>📐</div>
            <div style='font-family: Bebas Neue, sans-serif; font-size: 1.1rem; letter-spacing: 0.08em; color: #e8e8f0; margin-bottom: 0.25rem;'>LOG-NORMAL MODELING</div>
            <div style='font-size: 0.8rem; color: #6b6b80; line-height: 1.5;'>Each player's weekly output is modeled as a Log-Normal distribution, fit to their historical scoring data using conjugate priors.</div>
        </div>
        <div class='stat-card'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🔗</div>
            <div style='font-family: Bebas Neue, sans-serif; font-size: 1.1rem; letter-spacing: 0.08em; color: #e8e8f0; margin-bottom: 0.25rem;'>QB-RECEIVER CORRELATION</div>
            <div style='font-size: 0.8rem; color: #6b6b80; line-height: 1.5;'>Historically-derived correlations between QBs and their pass-catchers are used to adjust projections when a QB hits elite outcomes.</div>
        </div>
        <div class='stat-card'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>⚡</div>
            <div style='font-family: Bebas Neue, sans-serif; font-size: 1.1rem; letter-spacing: 0.08em; color: #e8e8f0; margin-bottom: 0.25rem;'>FULLY VECTORIZED</div>
            <div style='font-size: 0.8rem; color: #6b6b80; line-height: 1.5;'>Bayesian prior updates, per-simulation lineup selection, and playoff counting all run via NumPy broadcasting — zero Python loops over simulations.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
