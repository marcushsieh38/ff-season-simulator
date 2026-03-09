import streamlit as st
import numpy as np
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

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


def compute_intra_team_correlations(starter_pids, all_players_data, player_stats):
    """Compute QB->WR/TE (positive passing-game correlation) and QB->RB
    (negative cannibalization: heavy passing = fewer RB touches) correlations."""
    qb_ids = [p for p in starter_pids if all_players_data.get(p, {}).get("position") == "QB" and p in player_stats]
    skill_ids = [p for p in starter_pids if all_players_data.get(p, {}).get("position") in ("WR", "TE", "RB") and p in player_stats]
    correlations = {}
    for qb_id in qb_ids:
        qs = player_stats[qb_id]["scores"]
        if len(qs) < 4:
            continue
        for skill_id in skill_ids:
            rs = player_stats[skill_id]["scores"]
            n = min(len(qs), len(rs))
            if n < 4:
                continue
            qa, ra = np.array(qs[:n]), np.array(rs[:n])
            if np.std(qa) > 0 and np.std(ra) > 0:
                correlations[(qb_id, skill_id)] = float(np.corrcoef(qa, ra)[0, 1])
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
        team_correlations.append(compute_intra_team_correlations(starter_pids, all_players_data, player_stats))

    team_dynamic_means = [np.tile(base, (num_simulations, 1)).astype(np.float32) for base in team_initial_means]

    wins_matrix = np.zeros((num_simulations, num_teams), dtype=np.float32)
    points_matrix = np.zeros((num_simulations, num_teams), dtype=np.float32)
    # EMA decay: early weeks learn fast (prior dominates); later weeks trust
    # accumulated evidence more. alpha rises from ~0.20 to ~0.45 over the season.
    ema_min, ema_max = 0.20, 0.45

    for week_idx in range(num_regular_season_weeks):
        week_number = week_idx + 1
        t = week_idx / max(num_regular_season_weeks - 1, 1)  # 0 → 1 over season
        ema_alpha = ema_min + t * (ema_max - ema_min)
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

            # EMA update: blend prior mean toward observed score
            team_dynamic_means[team_idx] = (1.0 - ema_alpha) * current_means + ema_alpha * raw_scores

            qb_entries = [(i, pid) for i, pid in enumerate(all_pids) if all_players_data.get(pid, {}).get("position") == "QB"]
            if qb_entries:
                qb_col, qb_pid = qb_entries[0]
                high_qb_mask = raw_scores[:, qb_col] > np.percentile(raw_scores[:, qb_col], 80)
                for col_i, pid in enumerate(all_pids):
                    pos = all_players_data.get(pid, {}).get("position")
                    if pos not in ("WR", "TE", "RB"):
                        continue
                    corr = team_correlations[team_idx].get((qb_pid, pid), 0.0)
                    if abs(corr) > 0.1:
                        # WR/TE: positive corr boosts; RB: typically negative corr discounts
                        raw_scores[high_qb_mask, col_i] *= (1.0 + corr * 0.15)

            week_team_scores[:, team_idx] = np.sum(raw_scores[:, starter_cols], axis=1).astype(np.float32)

        points_matrix += week_team_scores

        for rid1, rid2 in (actual_schedule[week_idx] if week_idx < len(actual_schedule) else []):
            t1, t2 = roster_id_to_idx.get(rid1), roster_id_to_idx.get(rid2)
            if t1 is not None and t2 is not None:
                wins_matrix[:, t1] += (week_team_scores[:, t1] > week_team_scores[:, t2]).astype(np.float32)
                wins_matrix[:, t2] += (week_team_scores[:, t2] > week_team_scores[:, t1]).astype(np.float32)

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
    return results


def run_resimulation_batched(
    rosters_data, users_data, all_players_data, player_stats, positional_priors,
    roster_starters_by_week, actual_schedule, roster_actual_wins,
    num_regular_season_weeks, num_simulations, batch_size=250,
):
    """Identical math to run_resimulation but yields (completed_sims, partial_wins_matrix)
    after every batch so the caller can render a live chart."""
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
        team_correlations.append(compute_intra_team_correlations(starter_pids, all_players_data, player_stats))

    wins_matrix = np.zeros((num_simulations, num_teams), dtype=np.float32)
    points_matrix = np.zeros((num_simulations, num_teams), dtype=np.float32)
    # EMA decay: alpha rises from ema_min (week 1) to ema_max (final week)
    ema_min, ema_max = 0.20, 0.45

    # Process in batches; each batch runs ALL weeks for batch_size simulations
    batches = list(range(0, num_simulations, batch_size))
    for batch_start in batches:
        bs = min(batch_size, num_simulations - batch_start)
        batch_slice = slice(batch_start, batch_start + bs)

        team_dynamic_means = [np.tile(base, (bs, 1)).astype(np.float32) for base in team_initial_means]

        for week_idx in range(num_regular_season_weeks):
            week_number = week_idx + 1
            t = week_idx / max(num_regular_season_weeks - 1, 1)
            ema_alpha = ema_min + t * (ema_max - ema_min)
            week_team_scores = np.zeros((bs, num_teams), dtype=np.float32)

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
                    np.random.randn(bs, len(all_pids)).astype(np.float32) * sigma_m + mu_m
                ).astype(np.float32)

                # EMA update
                team_dynamic_means[team_idx] = (1.0 - ema_alpha) * current_means + ema_alpha * raw_scores

                qb_entries = [(i, pid) for i, pid in enumerate(all_pids) if all_players_data.get(pid, {}).get("position") == "QB"]
                if qb_entries:
                    qb_col, qb_pid = qb_entries[0]
                    high_qb_mask = raw_scores[:, qb_col] > np.percentile(raw_scores[:, qb_col], 80)
                    for col_i, pid in enumerate(all_pids):
                        pos = all_players_data.get(pid, {}).get("position")
                        if pos not in ("WR", "TE", "RB"):
                            continue
                        corr = team_correlations[team_idx].get((qb_pid, pid), 0.0)
                        if abs(corr) > 0.1:
                            raw_scores[high_qb_mask, col_i] *= (1.0 + corr * 0.15)

                week_team_scores[:, team_idx] = np.sum(raw_scores[:, starter_cols], axis=1).astype(np.float32)

            points_matrix[batch_slice] += week_team_scores
            for rid1, rid2 in (actual_schedule[week_idx] if week_idx < len(actual_schedule) else []):
                t1, t2 = roster_id_to_idx.get(rid1), roster_id_to_idx.get(rid2)
                if t1 is not None and t2 is not None:
                    wins_matrix[batch_slice, t1] += (week_team_scores[:, t1] > week_team_scores[:, t2]).astype(np.float32)
                    wins_matrix[batch_slice, t2] += (week_team_scores[:, t2] > week_team_scores[:, t1]).astype(np.float32)

        completed = batch_start + bs
        yield completed, wins_matrix[:completed].copy(), team_names, roster_ids

    # Final stats
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
    del sorted_wins, points_matrix
    yield completed, wins_matrix, team_names, roster_ids, results


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

# ── session-state keys ──────────────────────────────────────────────────────
for _k in ("sim_results", "sim_summary_table", "sim_luck_table",
           "sim_league_name", "sim_season_year", "sim_num_teams",
           "sim_num_weeks", "sim_num_players", "sim_num_sims"):
    if _k not in st.session_state:
        st.session_state[_k] = None

league_id_input = st.text_input("Completed Season League ID", placeholder="Paste your Sleeper league ID here")
num_sims = st.select_slider("Simulation Iterations", options=[1000, 2500, 5000, 10000], value=5000)
st.markdown('<div class="info-box">Enter the League ID of a <strong>finished season</strong>. The sim replays every week using the real starters each team set and the actual matchup schedule, then compares what did happen to what should have happened across thousands of alternate universes.</div>', unsafe_allow_html=True)

run_simulation = st.button("RESIMULATE SEASON", width="stretch")

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

    # ── live convergence line chart during simulation ─────────────────────────
    TEAM_COLORS = [
        "#00ff87","#4f9cf9","#ff6b35","#ffd700","#c084fc","#34d399",
        "#f87171","#60a5fa","#fb923c","#a78bfa","#4ade80","#f472b6",
    ]
    status_text.markdown('<div class="hero-sub">⚡ SIMULATING — WATCH PLAYOFF ODDS CONVERGE IN REAL TIME</div>', unsafe_allow_html=True)
    live_label = st.empty()
    live_chart  = st.empty()
    live_chips  = st.empty()

    # per-team history
    history_x = []          # shared x values: sims completed so far
    history_poff = []       # list-of-lists: running playoff % per team
    history_wins = []       # list-of-lists: running mean wins per team (for chips)
    _live_frame = 0

    actual_wins_live = None
    num_playoff_teams_live = None

    results = None
    gen = run_resimulation_batched(
        rosters_data=rosters_data, users_data=users_data, all_players_data=all_players_data,
        player_stats=player_stats, positional_priors=positional_priors,
        roster_starters_by_week=roster_starters_by_week, actual_schedule=actual_schedule,
        roster_actual_wins=roster_actual_wins, num_regular_season_weeks=num_regular_season_weeks,
        num_simulations=num_sims, batch_size=max(100, num_sims // 20),
    )

    for yielded in gen:
        if len(yielded) == 4:
            completed, partial_wins, team_names_live, roster_ids_live = yielded
            wins_so_far = partial_wins
        else:
            completed, _, team_names_live, roster_ids_live, results = yielded
            wins_so_far = results["wins_distribution"]

        n_t = len(team_names_live)
        is_final = results is not None

        # initialise once
        if actual_wins_live is None:
            actual_wins_live = [roster_actual_wins.get(roster_ids_live[i], 0) for i in range(n_t)]
            num_playoff_teams_live = min(4, n_t // 2)
            history_poff = [[] for _ in range(n_t)]
            history_wins = [[] for _ in range(n_t)]

        # running playoff probability
        running_means = wins_so_far[:completed].mean(axis=0)
        sorted_w = np.sort(wins_so_far[:completed], axis=1)
        cutoff = sorted_w[:, -num_playoff_teams_live]
        running_poff = np.mean(wins_so_far[:completed] >= cutoff[:, np.newaxis], axis=0) * 100

        # Wilson binomial SE for each team's playoff probability
        phat = running_poff / 100.0
        running_poff_std = np.sqrt(np.maximum(phat * (1.0 - phat) / completed, 0.0)) * 100.0

        history_x.append(completed)
        for i in range(n_t):
            history_poff[i].append(float(running_poff[i]))
            history_wins[i].append(float(running_means[i]))

        # ── build Plotly figure ───────────────────────────────────────────────
        fig_live = go.Figure()

        for i, tname in enumerate(team_names_live):
            col = TEAM_COLORS[i % len(TEAM_COLORS)]
            poff_vals = history_poff[i]
            std_val = float(running_poff_std[i])

            # shade ±1 std band (only once enough history)
            if len(history_x) >= 3:
                upper = [min(100.0, v + std_val) for v in poff_vals]
                lower = [max(0.0,   v - std_val) for v in poff_vals]
                r_c, g_c, b_c = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
                # upper bound (invisible line, fills downward)
                fig_live.add_trace(go.Scatter(
                    x=history_x, y=upper,
                    mode="lines", line=dict(width=0),
                    showlegend=False, hoverinfo="skip",
                    fillcolor=f"rgba({r_c},{g_c},{b_c},0.18)",
                ))
                # lower bound — fills up to upper
                fig_live.add_trace(go.Scatter(
                    x=history_x, y=lower,
                    mode="lines", line=dict(width=0),
                    fill="tonexty",
                    fillcolor=f"rgba({r_c},{g_c},{b_c},0.18)",
                    showlegend=False, hoverinfo="skip",
                ))

            # actual playoff finish marker line (50% threshold reference)
            # solid running playoff % line
            fig_live.add_trace(go.Scatter(
                x=history_x,
                y=poff_vals,
                mode="lines",
                name=tname,
                line=dict(color=col, width=2.5 if is_final else 2),
                hovertemplate=(
                    f"<b>{tname}</b><br>"
                    f"After %{{x:,}} sims: %{{y:.1f}}% playoff<br>"
                    f"Exp wins: {history_wins[i][-1]:.1f} · Actual: {actual_wins_live[i]}W"
                    "<extra></extra>"
                ),
            ))

        # 50% reference line
        fig_live.add_hline(y=50, line_width=1, line_dash="dot", line_color="#3a3a50",
                           annotation_text="50%", annotation_font=dict(color="#3a3a50", size=9))

        fig_live.update_layout(
            plot_bgcolor="#0a0a0f",
            paper_bgcolor="#111118",
            font=dict(family="DM Sans", color="#e8e8f0", size=11),
            xaxis=dict(
                title=dict(text="Simulations completed", font=dict(size=10, color="#6b6b80")),
                gridcolor="#1a1a24", tickfont=dict(family="DM Mono", size=10),
                range=[0, completed],
            ),
            yaxis=dict(
                title=dict(text="Playoff Probability (%)", font=dict(size=10, color="#6b6b80")),
                gridcolor="#1a1a24", tickfont=dict(family="DM Mono", size=10),
                range=[-2, 102],
            ),
            legend=dict(
                bgcolor="rgba(17,17,24,0.9)", bordercolor="#2a2a3a", borderwidth=1,
                font=dict(size=10), orientation="v",
                x=1.01, xanchor="left", y=1, yanchor="top",
            ),
            margin=dict(l=10, r=140, t=10, b=10),
            height=420,
            hovermode="x unified",
        )

        status_icon = "✅ CONVERGED" if is_final else "⚡ LIVE"
        live_label.markdown(
            f"<div style='font-family:DM Mono,monospace;font-size:0.7rem;color:#6b6b80;"
            f"letter-spacing:0.12em;text-transform:uppercase;padding:0.3rem 0;'>"
            f"{status_icon} &nbsp;·&nbsp; {completed:,} / {num_sims:,} universes simulated"
            f"&nbsp;·&nbsp; playoff probability convergence &nbsp;·&nbsp; shaded = uncertainty band</div>",
            unsafe_allow_html=True,
        )
        live_chart.plotly_chart(fig_live, width="stretch", key=f"live_{_live_frame}")
        _live_frame += 1

        # stat chips — show playoff % + expected wins
        chip_html = "<div style='display:flex;flex-wrap:wrap;gap:0.35rem;margin-top:0.4rem;'>"
        for i in range(n_t):
            col = TEAM_COLORS[i % len(TEAM_COLORS)]
            poff_val = float(running_poff[i])
            ew = float(running_means[i])
            aw = actual_wins_live[i]
            luck = ew - aw
            luck_str = f"+{luck:.1f}" if luck >= 0 else f"{luck:.1f}"
            luck_color = "#ff6b35" if luck < -0.05 else "#00ff87" if luck > 0.05 else "#6b6b80"
            chip_html += (
                f"<div style='background:#111118;border:1px solid #2a2a3a;border-top:2px solid {col};"
                f"border-radius:8px;padding:0.35rem 0.55rem;text-align:center;flex:1;min-width:80px;'>"
                f"<div style='font-family:Bebas Neue,sans-serif;font-size:1.25rem;color:{col};line-height:1;'>{poff_val:.0f}%</div>"
                f"<div style='font-family:DM Mono,monospace;font-size:0.58rem;color:#6b6b80;margin-top:0.1rem;"
                f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:88px;'>{team_names_live[i][:13]}</div>"
                f"<div style='font-family:DM Mono,monospace;font-size:0.55rem;color:#a0a0b8;'>"
                f"exp {ew:.1f}W</div>"
                f"<div style='font-family:DM Mono,monospace;font-size:0.55rem;color:{luck_color};'>"
                f"luck {luck_str}</div>"
                f"</div>"
            )
        chip_html += "</div>"
        live_chips.markdown(chip_html, unsafe_allow_html=True)

        pct = 55 + int((completed / num_sims) * 35)
        progress_bar.progress(min(pct, 90))

    # ── DO NOT clear live chart — let it persist as a summary ─────────────────
    # Update label to show final converged state
    live_label.markdown(
        f"<div style='font-family:DM Mono,monospace;font-size:0.7rem;color:#00ff87;"
        f"letter-spacing:0.12em;text-transform:uppercase;padding:0.3rem 0;'>"
        f"✅ CONVERGED &nbsp;·&nbsp; {num_sims:,} universes simulated &nbsp;·&nbsp; "
        f"playoff probability by team &nbsp;·&nbsp; shaded = uncertainty band</div>",
        unsafe_allow_html=True,
    )

    progress_bar.progress(95)
    status_text.markdown('<div class="hero-sub">FINALIZING RESULTS...</div>', unsafe_allow_html=True)
    summary_table = build_summary_table(rosters_data, results)
    luck_table = build_luck_table(rosters_data, results)
    progress_bar.progress(100)
    status_text.empty()
    progress_bar.empty()

    # ── persist everything to session state ──────────────────────────────────
    st.session_state.sim_results = results
    st.session_state.sim_summary_table = summary_table
    st.session_state.sim_luck_table = luck_table
    st.session_state.sim_league_name = league_info.get("name", "Your League")
    st.session_state.sim_season_year = league_info.get("season", "")
    st.session_state.sim_num_teams = num_teams
    st.session_state.sim_num_weeks = num_regular_season_weeks
    st.session_state.sim_num_players = len(player_stats)
    st.session_state.sim_num_sims = num_sims


# ── render results (from session state, survives tab/widget interactions) ────
if st.session_state.sim_results is not None:
    results        = st.session_state.sim_results
    summary_table  = st.session_state.sim_summary_table
    luck_table     = st.session_state.sim_luck_table
    league_name    = st.session_state.sim_league_name
    season_year    = st.session_state.sim_season_year
    num_teams      = st.session_state.sim_num_teams
    num_regular_season_weeks = st.session_state.sim_num_weeks
    num_players    = st.session_state.sim_num_players
    num_sims       = st.session_state.sim_num_sims

    st.markdown(f'<div class="section-header">{league_name.upper()} {season_year} — RESIMULATION RESULTS</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-box">🟢 {num_regular_season_weeks}-week regular season replayed with real lineups &nbsp;·&nbsp; {num_sims:,} simulations &nbsp;·&nbsp; {num_players:,} starters modeled</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="stat-card"><div class="stat-value">{num_teams}</div><div class="stat-label">Teams</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat-card"><div class="stat-value">{num_regular_season_weeks}</div><div class="stat-label">Weeks Replayed</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-card"><div class="stat-value">{num_players:,}</div><div class="stat-label">Players Modeled</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="stat-card"><div class="stat-value">{num_sims:,}</div><div class="stat-label">Simulations</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Season Summary", "📈 Win Distribution", "🍀 Luck Index", "🔬 Convergence"])

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
            height=36 * (num_teams + 1) + 3
        )

        # ── Bar chart: actual wins vs sim expected wins ──────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:1.2rem;">ACTUAL VS EXPECTED WINS</div>', unsafe_allow_html=True)
        team_names_sorted = [results["team_names"][i] for i in np.argsort(results["actual_wins_by_idx"])[::-1]]
        actual_sorted = sorted(results["actual_wins_by_idx"], reverse=True)
        mean_sorted = [results["mean_wins"][results["team_names"].index(t)] for t in team_names_sorted]
        std_sorted = [results["std_wins"][results["team_names"].index(t)] for t in team_names_sorted]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Sim Expected",
            x=team_names_sorted,
            y=mean_sorted,
            error_y=dict(type="data", array=std_sorted, visible=True, color="rgba(79,156,249,0.5)"),
            marker_color="rgba(79,156,249,0.6)",
            marker_line_color="rgba(79,156,249,1)",
            marker_line_width=1,
        ))
        fig_bar.add_trace(go.Scatter(
            name="Actual Wins",
            x=team_names_sorted,
            y=actual_sorted,
            mode="markers",
            marker=dict(color="#00ff87", size=12, symbol="diamond", line=dict(color="#0a0a0f", width=2)),
        ))
        fig_bar.update_layout(
            plot_bgcolor="#111118", paper_bgcolor="#111118",
            font=dict(family="DM Sans", color="#e8e8f0"),
            legend=dict(bgcolor="#1a1a24", bordercolor="#2a2a3a", borderwidth=1),
            xaxis=dict(gridcolor="#1a1a24", tickfont=dict(size=11)),
            yaxis=dict(gridcolor="#1a1a24", title="Wins"),
            margin=dict(l=10, r=10, t=20, b=10),
            height=340,
            bargap=0.3,
        )
        st.plotly_chart(fig_bar, width="stretch")

    with tab2:
        st.markdown('<div class="section-header">WIN DISTRIBUTION</div>', unsafe_allow_html=True)
        selected_team = st.selectbox("Select team", options=results["team_names"], key="win_dist_team")
        team_idx = results["team_names"].index(selected_team)
        team_wins_dist = results["wins_distribution"][:, team_idx]
        actual_wins_this_team = results["actual_wins_by_idx"][team_idx]

        bins = np.arange(0, int(team_wins_dist.max()) + 2) - 0.5
        hist_counts, bin_edges = np.histogram(team_wins_dist, bins=bins)
        win_vals = ((bin_edges[:-1] + bin_edges[1:]) / 2).astype(int)
        hist_df = pd.DataFrame({
            "Wins": win_vals,
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

        # ── Plotly histogram with actual-wins marker ─────────────────────────
        bar_colors = []
        for w in win_vals:
            if w == actual_wins_this_team:
                bar_colors.append("#00ff87")
            elif p10 <= w <= p90:
                bar_colors.append("rgba(79,156,249,0.75)")
            else:
                bar_colors.append("rgba(79,156,249,0.3)")

        fig_hist = go.Figure()
        fig_hist.add_trace(go.Bar(
            x=win_vals, y=hist_counts,
            marker_color=bar_colors,
            marker_line_color="rgba(0,0,0,0.3)", marker_line_width=1,
            customdata=hist_df["Frequency (%)"].values,
            hovertemplate="<b>%{x} wins</b><br>%{y:,} simulations (%{customdata:.1f}%)<extra></extra>",
        ))
        # actual wins vertical line
        fig_hist.add_vline(
            x=actual_wins_this_team, line_width=2, line_dash="dash", line_color="#00ff87",
            annotation_text=f"Actual: {actual_wins_this_team}W",
            annotation_font=dict(color="#00ff87", family="DM Mono", size=12),
            annotation_position="top",
        )
        # mean wins line
        mean_w = results["mean_wins"][team_idx]
        fig_hist.add_vline(
            x=mean_w, line_width=2, line_dash="dot", line_color="#4f9cf9",
            annotation_text=f"Avg: {mean_w:.1f}W",
            annotation_font=dict(color="#4f9cf9", family="DM Mono", size=12),
            annotation_position="top right",
        )
        fig_hist.update_layout(
            plot_bgcolor="#111118", paper_bgcolor="#111118",
            font=dict(family="DM Sans", color="#e8e8f0"),
            xaxis=dict(gridcolor="#1a1a24", title="Wins", dtick=1),
            yaxis=dict(gridcolor="#1a1a24", title="Simulations"),
            margin=dict(l=10, r=10, t=30, b=10),
            height=360,
            showlegend=False,
        )
        st.plotly_chart(fig_hist, width="stretch")

        pct_better = float(np.mean(team_wins_dist > actual_wins_this_team) * 100)
        pct_worse = float(np.mean(team_wins_dist < actual_wins_this_team) * 100)
        st.markdown(f'<div class="info-box">In {pct_better:.1f}% of simulations this team finished with <strong>more wins</strong> than they actually got. In {pct_worse:.1f}% they finished with fewer. <span style="color:#4f9cf9">■</span> shaded region = P10–P90 range.</div>', unsafe_allow_html=True)

        with st.expander("Full Distribution Table"):
            st.dataframe(hist_df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown('<div class="section-header">LUCK INDEX</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box"><strong>Luck Index = Actual Wins minus Simulation Expected Wins.</strong> Positive means the team won more games than their starters deserved on average — favorable opponent timing or opponents underperforming. Negative means they were robbed by variance.</div>', unsafe_allow_html=True)

        # ── Plotly horizontal bar — luck index ───────────────────────────────
        luck_df = luck_table.sort_values("Luck Index")
        colors_luck = ["#ff6b35" if v >= 0 else "#4f9cf9" for v in luck_df["Luck Index"]]
        fig_luck = go.Figure()
        fig_luck.add_trace(go.Bar(
            x=luck_df["Luck Index"], y=luck_df["Team"],
            orientation="h",
            marker_color=colors_luck,
            marker_line_width=0,
            customdata=np.stack([luck_df["Actual Wins"], luck_df["Sim Expected Wins"]], axis=-1),
            hovertemplate="<b>%{y}</b><br>Luck Index: %{x:+.2f}<br>Actual: %{customdata[0]}W · Expected: %{customdata[1]:.1f}W<extra></extra>",
        ))
        fig_luck.add_vline(x=0, line_width=1, line_color="#3a3a50")
        fig_luck.update_layout(
            plot_bgcolor="#111118", paper_bgcolor="#111118",
            font=dict(family="DM Sans", color="#e8e8f0"),
            xaxis=dict(gridcolor="#1a1a24", title="Luck Index (wins above/below expected)", zeroline=False),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=12)),
            margin=dict(l=10, r=10, t=20, b=10),
            height=max(300, 40 * num_teams),
            showlegend=False,
        )
        st.plotly_chart(fig_luck, width="stretch")

        st.dataframe(
            luck_table, use_container_width=True,
            column_config={
                "Luck Index": st.column_config.NumberColumn("Luck Index", format="%.2f", help="Positive = Lucky, Negative = Unlucky"),
                "Sim Expected Wins": st.column_config.NumberColumn(format="%.1f"),
                "Actual Points": st.column_config.NumberColumn(format="%.1f"),
                "Sim Points (Avg)": st.column_config.NumberColumn(format="%.1f"),
            },
            hide_index=True, height=36 * (num_teams + 1) + 3
        )

    with tab4:
        st.markdown('<div class="section-header">SIMULATION CONVERGENCE</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">Shows how each team\'s expected win total and playoff probability stabilises as more iterations are added. Flat lines = converged. Wiggle = more sims would help. Shaded bands show ±1 std of uncertainty around each running estimate.</div>', unsafe_allow_html=True)

        wins_dist = results["wins_distribution"]   # (num_sims, num_teams)
        checkpoints = np.unique(np.round(np.geomspace(50, num_sims, 40)).astype(int))
        checkpoints = checkpoints[checkpoints <= num_sims]

        # compute running mean + visible spread band at each checkpoint
        # std/sqrt(n) (SEM) is invisible at large n; use a fixed fraction of the
        # win-distribution std so the band reflects realistic outcome spread.
        running_means = np.zeros((len(checkpoints), num_teams), dtype=np.float32)
        running_stds  = np.zeros((len(checkpoints), num_teams), dtype=np.float32)
        for ci, cp in enumerate(checkpoints):
            sub = wins_dist[:cp]
            running_means[ci] = sub.mean(axis=0)
            # Show ±0.5 sigma of the win distribution — visible but not overwhelming
            running_stds[ci]  = sub.std(axis=0) * 0.5

        # league mean at each checkpoint for "above average" normalisation
        league_mean_by_cp = running_means.mean(axis=1, keepdims=True)  # (checkpoints, 1)

        # colour palette
        palette = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24

        conv_col1, conv_col2 = st.columns([2, 1])
        with conv_col1:
            conv_team = st.selectbox(
                "Highlight team",
                options=["All teams"] + results["team_names"],
                key="conv_team_select",
            )
        with conv_col2:
            show_above_avg = st.toggle("Show wins above league avg", value=False, key="above_avg_toggle")

        y_data = running_means - league_mean_by_cp if show_above_avg else running_means
        y_title = "Expected Wins Above League Avg" if show_above_avg else "Running Mean Expected Wins"

        fig_conv = go.Figure()
        if show_above_avg:
            fig_conv.add_hline(y=0, line_width=1, line_dash="dot", line_color="#3a3a50",
                               annotation_text="League avg", annotation_font=dict(color="#3a3a50", size=9))

        for ti, tname in enumerate(results["team_names"]):
            is_highlight = (conv_team == "All teams") or (conv_team == tname)
            col = palette[ti % len(palette)]
            yvals = y_data[:, ti].tolist()
            se = running_stds[:, ti].tolist()

            # hex → rgb for band fill
            r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
            band_alpha = 0.20 if is_highlight else 0.0

            upper = [yv + sv for yv, sv in zip(yvals, se)]
            lower = [yv - sv for yv, sv in zip(yvals, se)]

            if is_highlight:
                fig_conv.add_trace(go.Scatter(
                    x=checkpoints.tolist(), y=upper,
                    mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
                    fillcolor=f"rgba({r},{g},{b},{band_alpha})",
                ))
                fig_conv.add_trace(go.Scatter(
                    x=checkpoints.tolist(), y=lower,
                    mode="lines", line=dict(width=0), fill="tonexty",
                    fillcolor=f"rgba({r},{g},{b},{band_alpha})",
                    showlegend=False, hoverinfo="skip",
                ))

            fig_conv.add_trace(go.Scatter(
                x=checkpoints.tolist(), y=yvals,
                mode="lines",
                name=tname,
                line=dict(
                    color=col if is_highlight else "rgba(60,60,80,0.35)",
                    width=2.5 if is_highlight else 1,
                ),
                opacity=1.0 if is_highlight else 0.4,
                hovertemplate=f"<b>{tname}</b><br>After %{{x:,}} sims: %{{y:.2f}} wins<extra></extra>",
            ))

        fig_conv.update_layout(
            plot_bgcolor="#111118", paper_bgcolor="#111118",
            font=dict(family="DM Sans", color="#e8e8f0"),
            xaxis=dict(gridcolor="#1a1a24", title="Bootstrap Iterations", type="log"),
            yaxis=dict(gridcolor="#1a1a24", title=y_title),
            legend=dict(bgcolor="#1a1a24", bordercolor="#2a2a3a", borderwidth=1, font=dict(size=11)),
            margin=dict(l=10, r=10, t=20, b=10),
            height=420,
            hovermode="x unified",
        )
        st.plotly_chart(fig_conv, width="stretch")

        # ── Playoff probability convergence for selected/all teams ───────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:1.2rem;">PLAYOFF PROBABILITY CONVERGENCE</div>', unsafe_allow_html=True)
        num_playoff_teams = min(4, num_teams // 2)

        running_playoff      = np.zeros((len(checkpoints), num_teams), dtype=np.float32)
        running_playoff_se   = np.zeros((len(checkpoints), num_teams), dtype=np.float32)
        for ci, cp in enumerate(checkpoints):
            sub = wins_dist[:cp]
            sorted_sub = np.sort(sub, axis=1)
            cutoff = sorted_sub[:, -num_playoff_teams]
            pvals = np.mean(sub >= cutoff[:, np.newaxis], axis=0)
            running_playoff[ci] = pvals * 100
            # Wilson-style std error for a proportion
            running_playoff_se[ci] = np.sqrt(pvals * (1 - pvals) / cp) * 100 * 2.0

        fig_poff = go.Figure()
        fig_poff.add_hline(y=50, line_width=1, line_dash="dot", line_color="#3a3a50",
                           annotation_text="50%", annotation_font=dict(color="#3a3a50", size=9))

        for ti, tname in enumerate(results["team_names"]):
            is_highlight = (conv_team == "All teams") or (conv_team == tname)
            col = palette[ti % len(palette)]
            yvals = running_playoff[:, ti].tolist()
            se    = running_playoff_se[:, ti].tolist()
            r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
            band_alpha = 0.20 if is_highlight else 0.0

            upper = [min(100.0, yv + sv) for yv, sv in zip(yvals, se)]
            lower = [max(0.0,   yv - sv) for yv, sv in zip(yvals, se)]

            if is_highlight:
                fig_poff.add_trace(go.Scatter(
                    x=checkpoints.tolist(), y=upper,
                    mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
                    fillcolor=f"rgba({r},{g},{b},{band_alpha})",
                ))
                fig_poff.add_trace(go.Scatter(
                    x=checkpoints.tolist(), y=lower,
                    mode="lines", line=dict(width=0), fill="tonexty",
                    fillcolor=f"rgba({r},{g},{b},{band_alpha})",
                    showlegend=False, hoverinfo="skip",
                ))

            fig_poff.add_trace(go.Scatter(
                x=checkpoints.tolist(), y=yvals,
                mode="lines",
                name=tname,
                line=dict(
                    color=col if is_highlight else "rgba(60,60,80,0.35)",
                    width=2.5 if is_highlight else 1,
                ),
                opacity=1.0 if is_highlight else 0.4,
                showlegend=False,
                hovertemplate=f"<b>{tname}</b><br>After %{{x:,}} sims: %{{y:.1f}}% playoff<extra></extra>",
            ))

        fig_poff.update_layout(
            plot_bgcolor="#111118", paper_bgcolor="#111118",
            font=dict(family="DM Sans", color="#e8e8f0"),
            xaxis=dict(gridcolor="#1a1a24", title="Bootstrap Iterations", type="log"),
            yaxis=dict(gridcolor="#1a1a24", title="Playoff Probability (%)", range=[0, 102]),
            margin=dict(l=10, r=10, t=20, b=10),
            height=360,
            hovermode="x unified",
        )
        st.plotly_chart(fig_poff, width="stretch")

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
