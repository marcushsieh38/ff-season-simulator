import streamlit as st
import numpy as np
import pandas as pd
import requests
import gc

st.set_page_config(page_title="Sleeper Season Sim", page_icon="🏈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
:root { --bg:#0a0a0f;--surface:#111118;--surface2:#1a1a24;--border:#2a2a3a;--accent:#00ff87;--accent3:#4f9cf9;--text:#e8e8f0;--muted:#6b6b80; }
html,body,.stApp{background-color:var(--bg)!important;color:var(--text)!important;font-family:'DM Sans',sans-serif;}
.main .block-container{padding:2rem 3rem;max-width:1400px;}
.hero-title{font-family:'Bebas Neue',sans-serif;font-size:clamp(3rem,8vw,7rem);line-height:0.9;background:linear-gradient(135deg,#00ff87 0%,#4f9cf9 50%,#ff6b35 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:0.5rem;}
.hero-sub{font-family:'DM Mono',monospace;font-size:0.85rem;color:var(--muted);letter-spacing:0.15em;text-transform:uppercase;margin-bottom:3rem;}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.5rem;position:relative;overflow:hidden;}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--accent),var(--accent3));}
.stat-value{font-family:'Bebas Neue',sans-serif;font-size:2.5rem;color:var(--accent);line-height:1;}
.stat-label{font-family:'DM Mono',monospace;font-size:0.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;margin-top:0.25rem;}
.section-header{font-family:'Bebas Neue',sans-serif;font-size:1.8rem;letter-spacing:0.08em;color:var(--text);border-bottom:1px solid var(--border);padding-bottom:0.5rem;margin-bottom:1.5rem;}
.info-box{background:rgba(79,156,249,0.06);border:1px solid rgba(79,156,249,0.2);border-radius:8px;padding:1rem 1.25rem;font-size:0.85rem;color:#a0b4c8;margin-bottom:1.5rem;}
.warn-box{background:rgba(255,107,53,0.06);border:1px solid rgba(255,107,53,0.2);border-radius:8px;padding:1rem 1.25rem;font-size:0.85rem;color:#c8a090;margin-bottom:1.5rem;}
div[data-testid="stTextInput"] input{background:var(--surface2)!important;border:1px solid var(--border)!important;border-radius:8px!important;color:var(--text)!important;font-family:'DM Mono',monospace!important;font-size:0.9rem!important;padding:0.6rem 1rem!important;}
div[data-testid="stTextInput"] input:focus{border-color:var(--accent)!important;box-shadow:0 0 0 2px rgba(0,255,135,0.1)!important;}
div[data-testid="stTextInput"] label{font-family:'DM Mono',monospace!important;font-size:0.75rem!important;color:var(--muted)!important;text-transform:uppercase!important;letter-spacing:0.1em!important;}
.stButton>button{background:linear-gradient(135deg,#00ff87,#00d4a0)!important;color:#0a0a0f!important;border:none!important;border-radius:8px!important;font-family:'Bebas Neue',sans-serif!important;font-size:1.1rem!important;letter-spacing:0.1em!important;padding:0.6rem 2rem!important;width:100%;}
div[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:12px!important;overflow:hidden!important;}
.stProgress>div>div{background:linear-gradient(90deg,var(--accent),var(--accent3))!important;}
.stSelectbox div[data-baseweb="select"]>div{background:var(--surface2)!important;border-color:var(--border)!important;color:var(--text)!important;}
.stExpander{border:1px solid var(--border)!important;border-radius:8px!important;background:var(--surface)!important;}
footer{display:none!important;}#MainMenu{display:none!important;}header{display:none!important;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_all_players():
    try:
        r = requests.get("https://api.sleeper.app/v1/players/nfl", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_league_info(league_id):
    try:
        r = requests.get(f"https://api.sleeper.app/v1/league/{league_id}", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_league_rosters(league_id):
    try:
        r = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_league_users(league_id):
    try:
        r = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_week_matchups(league_id, week):
    try:
        r = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}", timeout=15)
        r.raise_for_status()
        data = r.json()
        return data if data else []
    except Exception:
        return []


@st.cache_data(ttl=86400, show_spinner=False)
def load_season_data(league_id, num_regular_season_weeks):
    actual_schedule = []
    player_weekly_scores = {}
    roster_starters_by_week = {}
    roster_actual_wins = {}

    for week in range(1, num_regular_season_weeks + 1):
        matchups = fetch_week_matchups(league_id, week)
        if not matchups:
            actual_schedule.append([])
            continue

        week_pairs_map = {}
        week_scores_map = {}

        for entry in matchups:
            roster_id = entry.get("roster_id")
            matchup_id = entry.get("matchup_id")
            starters = [s for s in (entry.get("starters") or []) if s and s != "0"]
            players_points = entry.get("players_points") or {}
            points = float(entry.get("points", 0) or 0)

            roster_starters_by_week.setdefault(roster_id, {})[week] = starters
            week_scores_map[roster_id] = points
            roster_actual_wins.setdefault(roster_id, 0)

            starter_set = set(starters)
            for pid, pts in players_points.items():
                if pts is not None and float(pts) > 0 and pid in starter_set:
                    player_weekly_scores.setdefault(pid, []).append(float(pts))

            if matchup_id:
                week_pairs_map.setdefault(matchup_id, []).append(roster_id)

        week_pairs = [tuple(pair) for pair in week_pairs_map.values() if len(pair) == 2]
        actual_schedule.append(week_pairs)

        for pair in week_pairs:
            rid_a, rid_b = pair
            score_a = week_scores_map.get(rid_a, 0)
            score_b = week_scores_map.get(rid_b, 0)
            if score_a > score_b:
                roster_actual_wins[rid_a] = roster_actual_wins.get(rid_a, 0) + 1
            elif score_b > score_a:
                roster_actual_wins[rid_b] = roster_actual_wins.get(rid_b, 0) + 1

    player_stats = {}
    for pid, scores in player_weekly_scores.items():
        if len(scores) >= 2:
            arr = np.array(scores, dtype=np.float32)
            player_stats[pid] = {
                "mean": float(np.mean(arr)),
                "variance": float(np.var(arr, ddof=1)) if len(arr) > 1 else 5.0,
                "scores": scores,
            }

    return actual_schedule, roster_starters_by_week, player_stats, roster_actual_wins


def compute_lognormal_params_vectorized(means_2d, variances_1d):
    var2d = np.maximum(variances_1d[np.newaxis, :], 0.01)
    m2d = np.maximum(means_2d, 0.1)
    mu = np.log(m2d ** 2 / np.sqrt(var2d + m2d ** 2))
    sigma = np.sqrt(np.log(1 + var2d / m2d ** 2))
    return mu, np.maximum(sigma, 0.05)


def compute_positional_priors(all_players_data, player_stats):
    skill_positions = {"QB", "RB", "WR", "TE", "K"}
    positional_data = {pos: [] for pos in skill_positions}
    for pid, info in player_stats.items():
        pos = all_players_data.get(pid, {}).get("position", "")
        if pos in skill_positions:
            positional_data[pos].append(info["mean"])
    positional_priors = {}
    for pos, means in positional_data.items():
        if means:
            top_50 = sorted(means, reverse=True)[:50]
            positional_priors[pos] = {
                "mean": float(np.mean(top_50)),
                "variance": max(float(np.var(top_50)) if len(top_50) > 1 else 5.0, 1.0)
            }
        else:
            positional_priors[pos] = {"mean": 8.0, "variance": 10.0}
    return positional_priors


def compute_qb_receiver_correlations(starter_pids, all_players_data, player_stats):
    qb_ids = [p for p in starter_pids if all_players_data.get(p, {}).get("position") == "QB" and p in player_stats]
    rec_ids = [p for p in starter_pids if all_players_data.get(p, {}).get("position") in ("WR", "TE") and p in player_stats]
    correlations = {}
    for qb_id in qb_ids:
        qs = player_stats[qb_id]["scores"]
        if len(qs) < 4:
            continue
        for rec_id in rec_ids:
            rs = player_stats[rec_id]["scores"]
            n = min(len(qs), len(rs))
            if n < 4:
                continue
            qa, ra = np.array(qs[:n]), np.array(rs[:n])
            if np.std(qa) > 0 and np.std(ra) > 0:
                correlations[(qb_id, rec_id)] = float(np.corrcoef(qa, ra)[0, 1])
    return correlations


def run_resimulation(
    rosters_data, users_data, all_players_data, player_stats, positional_priors,
    roster_starters_by_week, actual_schedule, roster_actual_wins,
    num_regular_season_weeks, num_simulations,
):
    num_teams = len(rosters_data)
    user_map = {u["user_id"]: u.get("display_name", u["user_id"]) for u in users_data}
    team_names = [user_map.get(r.get("owner_id", ""), f"Team {r['roster_id']}") for r in rosters_data]
    roster_ids = [r["roster_id"] for r in rosters_data]
    roster_id_to_idx = {rid: i for i, rid in enumerate(roster_ids)}
    skill_positions = {"QB", "RB", "WR", "TE", "K"}

    team_all_starter_pids = []
    for roster in rosters_data:
        rid = roster["roster_id"]
        seen, ordered = set(), []
        for week in range(1, num_regular_season_weeks + 1):
            for pid in roster_starters_by_week.get(rid, {}).get(week, []):
                if pid not in seen and all_players_data.get(pid, {}).get("position") in skill_positions:
                    seen.add(pid)
                    ordered.append(pid)
        team_all_starter_pids.append(ordered)

    team_initial_means, team_static_variances, team_correlations = [], [], []
    for starter_pids in team_all_starter_pids:
        means, variances = [], []
        for pid in starter_pids:
            if pid in player_stats:
                means.append(player_stats[pid]["mean"])
                variances.append(player_stats[pid]["variance"])
            else:
                pos = all_players_data.get(pid, {}).get("position", "WR")
                prior = positional_priors.get(pos, {"mean": 8.0, "variance": 10.0})
                means.append(prior["mean"])
                variances.append(prior["variance"])
        team_initial_means.append(np.array(means, dtype=np.float32) if means else np.array([0.0], dtype=np.float32))
        team_static_variances.append(np.array(variances, dtype=np.float32) if variances else np.array([1.0], dtype=np.float32))
        team_correlations.append(compute_qb_receiver_correlations(starter_pids, all_players_data, player_stats))

    team_dynamic_means = [np.tile(base, (num_simulations, 1)).astype(np.float32) for base in team_initial_means]

    wins_matrix = np.zeros((num_simulations, num_teams), dtype=np.float32)
    points_matrix = np.zeros((num_simulations, num_teams), dtype=np.float32)
    bayesian_prior_w, bayesian_obs_w = 3.0, 1.0
    bayesian_total = bayesian_prior_w + bayesian_obs_w

    for week_idx in range(num_regular_season_weeks):
        week_number = week_idx + 1
        week_team_scores = np.zeros((num_simulations, num_teams), dtype=np.float32)

        for team_idx, roster in enumerate(rosters_data):
            rid = roster["roster_id"]
            week_starter_pids = [
                pid for pid in roster_starters_by_week.get(rid, {}).get(week_number, [])
                if all_players_data.get(pid, {}).get("position") in skill_positions
            ]
            all_pids = team_all_starter_pids[team_idx]
            pid_to_col = {pid: i for i, pid in enumerate(all_pids)}
            starter_cols = [pid_to_col[pid] for pid in week_starter_pids if pid in pid_to_col]

            if not all_pids or not starter_cols:
                continue

            current_means = team_dynamic_means[team_idx]
            mu_m, sigma_m = compute_lognormal_params_vectorized(current_means, team_static_variances[team_idx])
            raw_scores = np.exp(
                np.random.randn(num_simulations, len(all_pids)).astype(np.float32) * sigma_m + mu_m
            ).astype(np.float32)

            team_dynamic_means[team_idx] = (bayesian_prior_w * current_means + bayesian_obs_w * raw_scores) / bayesian_total

            qb_entries = [(i, pid) for i, pid in enumerate(all_pids) if all_players_data.get(pid, {}).get("position") == "QB"]
            if qb_entries:
                qb_col, qb_pid = qb_entries[0]
                high_qb_mask = raw_scores[:, qb_col] > np.percentile(raw_scores[:, qb_col], 80)
                for col_i, pid in enumerate(all_pids):
                    if all_players_data.get(pid, {}).get("position") not in ("WR", "TE"):
                        continue
                    corr = team_correlations[team_idx].get((qb_pid, pid), 0.0)
                    if abs(corr) > 0.1:
                        raw_scores[high_qb_mask, col_i] *= (1.0 + corr * 0.15)

            week_team_scores[:, team_idx] = np.sum(raw_scores[:, starter_cols], axis=1).astype(np.float32)
            del raw_scores, mu_m, sigma_m
            gc.collect()

        points_matrix += week_team_scores

        for rid1, rid2 in (actual_schedule[week_idx] if week_idx < len(actual_schedule) else []):
            t1, t2 = roster_id_to_idx.get(rid1), roster_id_to_idx.get(rid2)
            if t1 is not None and t2 is not None:
                wins_matrix[:, t1] += (week_team_scores[:, t1] > week_team_scores[:, t2]).astype(np.float32)
                wins_matrix[:, t2] += (week_team_scores[:, t2] > week_team_scores[:, t1]).astype(np.float32)

        del week_team_scores
        gc.collect()

    num_playoff_teams = min(4, num_teams // 2)
    sorted_wins = np.sort(wins_matrix, axis=1)
    playoff_probs = np.mean(wins_matrix >= sorted_wins[:, -num_playoff_teams][:, np.newaxis], axis=0)
    mean_wins = np.mean(wins_matrix, axis=0)
    std_wins = np.std(wins_matrix, axis=0)
    mean_points = np.mean(points_matrix, axis=0)

    actual_wins_by_idx = [roster_actual_wins.get(roster_ids[i], 0) for i in range(num_teams)]

    results = {
        "team_names": team_names,
        "roster_ids": roster_ids,
        "playoff_probs": playoff_probs.tolist(),
        "mean_wins": mean_wins.tolist(),
        "std_wins": std_wins.tolist(),
        "mean_points": mean_points.tolist(),
        "actual_wins_by_idx": actual_wins_by_idx,
        "wins_distribution": wins_matrix,
        "num_simulations": num_simulations,
    }

    del wins_matrix, points_matrix, sorted_wins
    gc.collect()
    return results


def build_summary_table(rosters_data, results):
    rows = []
    for i, roster in enumerate(rosters_data):
        s = roster.get("settings", {})
        fpts = s.get("fpts", 0) + s.get("fpts_decimal", 0) / 100
        rows.append({
            "Team": results["team_names"][i],
            "Actual Record": f"{results['actual_wins_by_idx'][i]}–{int(s.get('losses', 0))}",
            "Actual Points": round(fpts, 1),
            "Sim Wins (Avg)": round(results["mean_wins"][i], 1),
            "Sim Points (Avg)": round(results["mean_points"][i], 1),
            "Playoff %": round(results["playoff_probs"][i] * 100, 1),
            "Win Std Dev": round(results["std_wins"][i], 2),
            "_sort": results["actual_wins_by_idx"][i],
        })
    df = pd.DataFrame(rows).sort_values("_sort", ascending=False).drop(columns=["_sort"]).reset_index(drop=True)
    df.index = df.index + 1
    return df


def build_luck_table(rosters_data, results):
    rows = []
    for i, roster in enumerate(rosters_data):
        s = roster.get("settings", {})
        fpts = s.get("fpts", 0) + s.get("fpts_decimal", 0) / 100
        actual_wins = results["actual_wins_by_idx"][i]
        rows.append({
            "Team": results["team_names"][i],
            "Actual Wins": int(actual_wins),
            "Sim Expected Wins": round(results["mean_wins"][i], 1),
            "Luck Index": round(actual_wins - results["mean_wins"][i], 2),
            "Actual Points": round(fpts, 1),
            "Sim Points (Avg)": round(results["mean_points"][i], 1),
        })
    return pd.DataFrame(rows).sort_values("Luck Index", ascending=False).reset_index(drop=True)


st.markdown('<div class="hero-title">SLEEPER<br>SEASON SIM</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Bayesian Monte Carlo Resimulation &nbsp;·&nbsp; Completed Season Analysis &nbsp;·&nbsp; Luck Index</div>', unsafe_allow_html=True)

league_id_input = st.text_input("Completed Season League ID", placeholder="Paste your Sleeper league ID here")
num_sims = st.select_slider("Simulation Iterations", options=[1000, 2500, 5000, 10000], value=5000)
st.markdown('<div class="info-box">Enter the League ID of a <strong>finished season</strong>. The sim replays every week using the real starters each team set and the actual matchup schedule, then compares what did happen to what should have happened across thousands of alternate universes.</div>', unsafe_allow_html=True)

run_simulation = st.button("RESIMULATE SEASON", use_container_width=True)

if run_simulation:
    if not league_id_input.strip():
        st.markdown('<div class="warn-box">Please enter a League ID to continue.</div>', unsafe_allow_html=True)
        st.stop()

    league_id = league_id_input.strip()
    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.markdown('<div class="hero-sub">FETCHING LEAGUE INFO...</div>', unsafe_allow_html=True)
    progress_bar.progress(5)
    league_info = fetch_league_info(league_id)
    if not league_info:
        st.error("Could not find that league. Double-check your League ID.")
        st.stop()

    settings = league_info.get("settings", {})
    num_regular_season_weeks = int(settings.get("playoff_week_start", 15)) - 1
    num_regular_season_weeks = max(1, min(num_regular_season_weeks, 17))

    rosters_data = fetch_league_rosters(league_id)
    users_data = fetch_league_users(league_id)
    if not rosters_data or not users_data:
        st.error("Could not fetch roster or user data.")
        st.stop()

    progress_bar.progress(12)
    status_text.markdown('<div class="hero-sub">LOADING NFL PLAYER DATABASE...</div>', unsafe_allow_html=True)
    all_players_data = fetch_all_players()
    if not all_players_data:
        st.error("Could not fetch the Sleeper player database.")
        st.stop()

    progress_bar.progress(22)
    status_text.markdown(f'<div class="hero-sub">LOADING {num_regular_season_weeks} WEEKS OF MATCHUP DATA...</div>', unsafe_allow_html=True)
    actual_schedule, roster_starters_by_week, player_stats, roster_actual_wins = load_season_data(league_id, num_regular_season_weeks)

    if not player_stats:
        st.error("No scoring data found. Make sure this league has completed at least one week.")
        st.stop()

    progress_bar.progress(45)
    status_text.markdown('<div class="hero-sub">BUILDING PLAYER DISTRIBUTIONS & QB CORRELATIONS...</div>', unsafe_allow_html=True)
    positional_priors = compute_positional_priors(all_players_data, player_stats)
    num_teams = len(rosters_data)

    progress_bar.progress(55)
    status_text.markdown(f'<div class="hero-sub">RUNNING {num_sims:,} ALTERNATE UNIVERSES...</div>', unsafe_allow_html=True)
    np.random.seed(42)
    results = run_resimulation(
        rosters_data=rosters_data, users_data=users_data, all_players_data=all_players_data,
        player_stats=player_stats, positional_priors=positional_priors,
        roster_starters_by_week=roster_starters_by_week, actual_schedule=actual_schedule,
        roster_actual_wins=roster_actual_wins, num_regular_season_weeks=num_regular_season_weeks,
        num_simulations=num_sims,
    )

    progress_bar.progress(95)
    status_text.markdown('<div class="hero-sub">FINALIZING RESULTS...</div>', unsafe_allow_html=True)
    summary_table = build_summary_table(rosters_data, results)
    luck_table = build_luck_table(rosters_data, results)
    progress_bar.progress(100)
    status_text.empty()
    progress_bar.empty()

    league_name = league_info.get("name", "Your League")
    season_year = league_info.get("season", "")
    st.markdown(f'<div class="section-header">{league_name.upper()} {season_year} — RESIMULATION RESULTS</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box">🟢 {num_regular_season_weeks}-week regular season replayed with real lineups &nbsp;·&nbsp; {num_sims:,} simulations &nbsp;·&nbsp; {len(player_stats):,} starters modeled</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="stat-card"><div class="stat-value">{num_teams}</div><div class="stat-label">Teams</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat-card"><div class="stat-value">{num_regular_season_weeks}</div><div class="stat-label">Weeks Replayed</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-card"><div class="stat-value">{len(player_stats):,}</div><div class="stat-label">Players Modeled</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="stat-card"><div class="stat-value">{num_sims:,}</div><div class="stat-label">Simulations</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📋 Season Summary", "📈 Win Distribution", "🍀 Luck Index"])

    with tab1:
        st.markdown('<div class="section-header">ACTUAL VS SIMULATED SEASON</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">Every team\'s real finish compared to their simulation average. Playoff % shows how often each team made it given their actual weekly starters and real schedule.</div>', unsafe_allow_html=True)
        st.dataframe(
            summary_table, use_container_width=True,
            column_config={
                "Playoff %": st.column_config.ProgressColumn("Playoff %", format="%.1f%%", min_value=0, max_value=100),
                "Sim Wins (Avg)": st.column_config.NumberColumn(format="%.1f"),
                "Sim Points (Avg)": st.column_config.NumberColumn(format="%.1f"),
                "Actual Points": st.column_config.NumberColumn(format="%.1f"),
                "Win Std Dev": st.column_config.NumberColumn(format="%.2f"),
            },
            height=min(520, 70 + 38 * num_teams)
        )

    with tab2:
        st.markdown('<div class="section-header">WIN DISTRIBUTION</div>', unsafe_allow_html=True)
        selected_team = st.selectbox("Select team", options=results["team_names"], label_visibility="collapsed")
        team_idx = results["team_names"].index(selected_team)
        team_wins_dist = results["wins_distribution"][:, team_idx]
        actual_wins_this_team = results["actual_wins_by_idx"][team_idx]

        bins = np.arange(0, int(team_wins_dist.max()) + 2) - 0.5
        hist_counts, bin_edges = np.histogram(team_wins_dist, bins=bins)
        hist_df = pd.DataFrame({
            "Wins": ((bin_edges[:-1] + bin_edges[1:]) / 2).astype(int),
            "Simulations": hist_counts,
            "Frequency (%)": (hist_counts / num_sims * 100).round(1)
        })

        p10, p90 = int(np.percentile(team_wins_dist, 10)), int(np.percentile(team_wins_dist, 90))
        hc1, hc2, hc3, hc4 = st.columns(4)
        with hc1: st.markdown(f'<div class="stat-card"><div class="stat-value">{actual_wins_this_team}</div><div class="stat-label">Actual Wins</div></div>', unsafe_allow_html=True)
        with hc2: st.markdown(f'<div class="stat-card"><div class="stat-value">{results["mean_wins"][team_idx]:.1f}</div><div class="stat-label">Sim Expected Wins</div></div>', unsafe_allow_html=True)
        with hc3: st.markdown(f'<div class="stat-card"><div class="stat-value">{results["playoff_probs"][team_idx]*100:.0f}%</div><div class="stat-label">Playoff Probability</div></div>', unsafe_allow_html=True)
        with hc4: st.markdown(f'<div class="stat-card"><div class="stat-value">{p10}–{p90}</div><div class="stat-label">P10–P90 Range</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.bar_chart(hist_df.set_index("Wins")["Simulations"], use_container_width=True)

        pct_better = float(np.mean(team_wins_dist > actual_wins_this_team) * 100)
        pct_worse = float(np.mean(team_wins_dist < actual_wins_this_team) * 100)
        st.markdown(f'<div class="info-box">In {pct_better:.1f}% of simulations this team finished with <strong>more wins</strong> than they actually got. In {pct_worse:.1f}% they finished with fewer.</div>', unsafe_allow_html=True)

        with st.expander("Full Distribution Table"):
            st.dataframe(hist_df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown('<div class="section-header">LUCK INDEX</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box"><strong>Luck Index = Actual Wins minus Simulation Expected Wins.</strong> Positive means the team won more games than their starters deserved on average — favorable opponent timing or opponents underperforming. Negative means they were robbed by variance.</div>', unsafe_allow_html=True)
        st.dataframe(
            luck_table, use_container_width=True,
            column_config={
                "Luck Index": st.column_config.NumberColumn("Luck Index", format="%.2f", help="Positive = Lucky, Negative = Unlucky"),
                "Sim Expected Wins": st.column_config.NumberColumn(format="%.1f"),
                "Actual Points": st.column_config.NumberColumn(format="%.1f"),
                "Sim Points (Avg)": st.column_config.NumberColumn(format="%.1f"),
            },
            hide_index=True, height=min(520, 70 + 38 * num_teams)
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:DM Mono,monospace;font-size:0.7rem;color:#3a3a50;text-align:center;letter-spacing:0.1em;'>SLEEPER SEASON SIM &nbsp;·&nbsp; BAYESIAN MONTE CARLO RESIMULATION &nbsp;·&nbsp; NUMPY VECTORIZED</div>", unsafe_allow_html=True)

else:
    st.markdown("""
    <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:2rem;'>
        <div class='stat-card'>
            <div style='font-size:2rem;margin-bottom:0.5rem;'>📅</div>
            <div style='font-family:Bebas Neue,sans-serif;font-size:1.1rem;letter-spacing:0.08em;color:#e8e8f0;margin-bottom:0.25rem;'>REAL LINEUPS, REAL SCHEDULE</div>
            <div style='font-size:0.8rem;color:#6b6b80;line-height:1.5;'>Every week is replayed using the exact starters each manager set and the real matchup pairings — your WR3 who erupted stays on the bench where you left him.</div>
        </div>
        <div class='stat-card'>
            <div style='font-size:2rem;margin-bottom:0.5rem;'>🎲</div>
            <div style='font-family:Bebas Neue,sans-serif;font-size:1.1rem;letter-spacing:0.08em;color:#e8e8f0;margin-bottom:0.25rem;'>10,000 ALTERNATE UNIVERSES</div>
            <div style='font-size:0.8rem;color:#6b6b80;line-height:1.5;'>Log-Normal distributions fit to each starter's actual season scoring generate thousands of plausible outcomes from the same lineups and schedule.</div>
        </div>
        <div class='stat-card'>
            <div style='font-size:2rem;margin-bottom:0.5rem;'>🍀</div>
            <div style='font-family:Bebas Neue,sans-serif;font-size:1.1rem;letter-spacing:0.08em;color:#e8e8f0;margin-bottom:0.25rem;'>WHO ACTUALLY DESERVED IT</div>
            <div style='font-size:0.8rem;color:#6b6b80;line-height:1.5;'>The Luck Index separates scheduling variance from actual team strength — find out if your league winner got there on merit or good fortune.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
