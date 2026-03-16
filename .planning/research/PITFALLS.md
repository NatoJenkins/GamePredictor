# Domain Pitfalls

**Domain:** NFL game outcome prediction (win/loss classifier with confidence scores)
**Researched:** 2026-03-15
**Confidence:** MEDIUM (training-data-based expertise; web verification was unavailable)

---

## Critical Pitfalls

Mistakes that cause rewrites, false confidence in model quality, or production failures.

---

### Pitfall 1: Future Data Leakage in Rolling Features

**What goes wrong:** Rolling averages, cumulative stats, or season aggregates are computed using the full season (or the game being predicted) rather than strictly prior games. Example: a "season yards per game" feature for Week 8 that includes Week 8's own yards. The model sees the outcome embedded in the features, inflating validation accuracy to 70%+ -- but real predictions crater to ~50%.

**Why it happens:** Pandas `groupby().rolling()` and `expanding()` default to including the current row. A simple `df.groupby('team').expanding().mean()` includes the current game. Many tutorials compute season-level aggregates first, then join, accidentally including future games. The bug is silent -- no errors, just impossibly good metrics.

**Consequences:** Model appears to beat every benchmark easily during development. Deployed model performs at or below coin flip. Entire feature engineering pipeline must be rewritten. Potentially months of wasted experiment iterations.

**Prevention:**
- Shift all rolling/expanding computations by 1: `groupby('team').expanding().mean().shift(1)` -- the `.shift(1)` is mandatory.
- Write explicit leakage tests: for each game, assert that no feature value could change if that game's outcome changed. Concretely: zero out that game's stats, recompute features, verify identical values.
- Use a `build_features(games_up_to_date)` function that physically filters the dataframe to exclude future games before computing anything.
- For opponent-based features (opponent's defensive stats), the same shift rule applies -- you can only use the opponent's stats from games before this matchup.

**Detection:** Suspiciously high accuracy (>65% on NFL games is a red flag). Features that correlate >0.5 with the target. Validation accuracy much higher than any published NFL prediction model.

**Phase relevance:** Feature Engineering phase. Must be enforced from the very first feature and tested continuously.

---

### Pitfall 2: Validation Season Contamination via Feature Leakage

**What goes wrong:** The temporal split (train 2005-2022, validate 2023, test 2024) is correctly applied to the model training step, but features for 2023 games are computed using 2023 data from other games in the validation set. Example: Team A's rolling average going into Week 10 of 2023 uses Weeks 1-9 of 2023 -- those weeks are also in the validation set. This is NOT leakage if done correctly (you would do the same in production). The real pitfall is the reverse: computing 2023 features that accidentally use 2022 training data aggregates that were computed with knowledge of where the train/val boundary falls.

**Why it happens:** Confusion about what "temporal split" means for feature computation vs. model training. Features should be computed sequentially regardless of the split -- the split only governs which rows the model trains on vs. evaluates on.

**Consequences:** Subtle bias in validation metrics. Over-engineering the split logic wastes time. Under-engineering it leaks.

**Prevention:**
- Compute ALL features in one sequential pass over the entire 2005-2024 dataset, using only prior-game data at each step (see Pitfall 1).
- THEN split into train/val/test by season for model fitting.
- The features themselves are computed identically to how they would be in production -- using all available prior data.
- Never compute features separately per split.

**Detection:** Check that feature computation code has no awareness of the train/val/test boundary. Features should be a pure function of prior games.

**Phase relevance:** Feature Engineering and Model Training phases.

---

### Pitfall 3: nfl-data-py Data Quality Issues

**What goes wrong:** nfl-data-py pulls from nflfastR's public data repository. Several known issues:
1. **Missing or incomplete games:** Some games (especially older seasons, international games, or games with data feed issues) have incomplete play-by-play. A game might have 40 plays recorded instead of 120+.
2. **Column schema changes across seasons:** Columns get added, renamed, or deprecated across years. A column present in 2020+ data may be NaN for all pre-2020 games. The `epa` (expected points added) column has different calculation methodologies across eras.
3. **Bye weeks and schedule gaps:** The data has no explicit bye week rows -- you must infer bye weeks from gaps in the schedule. Rolling features across bye weeks need careful handling (a team's "last 3 games" might span 4 calendar weeks).
4. **Team abbreviation inconsistencies:** Relocations and rebrandings cause issues. The Raiders appear as OAK (pre-2020) and LV (2020+). Washington appears as WAS, WSH, or WAS with different team names. The Chargers moved from SD to LAC.
5. **Playoff vs. regular season confusion:** Play-by-play includes postseason games. If you compute rolling stats without filtering, a team's Week 1 features include their playoff performance, which creates a biased feature (only good teams have playoff data).
6. **The `result` column trap:** nfl-data-py schedule data has a `result` column that contains the home team's score differential. Using this directly as a feature leaks the outcome. It must only be used as the target variable.

**Why it happens:** nfl-data-py is a convenience wrapper, not a curated dataset. The underlying data evolves each season. Schema documentation is sparse.

**Consequences:** Silent NaN propagation in features. Models trained on inconsistent features across eras. Team identity bugs that corrupt rolling calculations. Playoff contamination inflates some teams' feature values.

**Prevention:**
- Load one season first and inspect ALL columns. Document which columns you use and verify they exist across your entire date range (2005-2024).
- Build a data validation step that checks: game count per season (should be 256 for 16-game era, 272 for 17-game era starting 2021), minimum play count per game (flag games with <50 plays), team abbreviation mapping table.
- Create a team name normalization mapping: `{"OAK": "LV", "SD": "LAC", "STL": "LA", "WSH": "WAS"}` and apply it universally.
- Filter to regular season only for feature computation. Handle playoff features separately if needed.
- Never use `result`, `home_score`, or `away_score` as features -- only as the target or for computing the target.

**Detection:** Run `df.isna().sum()` on every feature column, grouped by season. Large NaN spikes in certain seasons indicate schema changes. Check `df.groupby('season').game_id.nunique()` to catch missing games.

**Phase relevance:** Data Ingestion phase. Build validation checks before any feature engineering begins.

---

### Pitfall 4: Overfitting to the 2023 Validation Season

**What goes wrong:** The experiment loop iterates many times, each time tweaking hyperparameters or features to maximize 2023 validation accuracy. After 50+ iterations, the model is effectively overfit to the specific outcomes of the 2023 season. It has learned the quirks of that particular season (e.g., the specific upsets, the specific team trajectories) rather than general NFL prediction patterns. The 2024 holdout test reveals the true (much lower) accuracy.

**Why it happens:** This is the fundamental problem with the keep/revert experiment loop. Each iteration that "keeps" a change is implicitly fitting to 2023. With enough iterations, you can reach 60%+ on 2023 while actually degrading generalization. The 2023 season is only ~272 games -- a small validation set where noise dominates.

**Consequences:** False confidence in model quality. The 2024 holdout reveals the model is no better than baseline. All experiment iterations were wasted because they optimized for noise.

**Prevention:**
- **Cap experiment iterations:** Set a hard limit (20-30 experiments). After that, accept the best model or restructure the approach.
- **Track multiple validation metrics:** Not just 2023 accuracy. Also track 2021 accuracy and 2022 accuracy (computed on those seasons but not used for keep/revert decisions). If 2023 accuracy improves but 2021/2022 degrade, you are overfitting.
- **Use calibration, not just accuracy:** Log Brier score, log loss, and calibration plots alongside accuracy. A model with 56% accuracy and well-calibrated probabilities is better than 58% accuracy with garbage confidence scores.
- **Early stopping on improvement rate:** If the last 5 experiments all showed <0.5% improvement, stop iterating.
- **Never peek at 2024 holdout until final evaluation.** Not even once. Log it automatically at the end but do not use it for any decision.

**Detection:** Validation accuracy climbing steadily while additional accuracy metrics (on other seasons) plateau or decline. Confidence calibration degrading (model says 80% confident on games it wins only 55% of the time).

**Phase relevance:** Model Training phase (experiment loop). This is the highest-risk phase of the entire project.

---

### Pitfall 5: Experiment Loop Infinite Loops and Regression Spirals

**What goes wrong:** The autoresearch-style experiment loop (read program.md, pick experiment, modify train.py, run, log, keep/revert) can degenerate in several ways:
1. **Infinite loop:** Agent keeps trying similar experiments that all fail to improve, never converging. Each iteration takes 5-10 minutes, burning hours.
2. **Regression spiral:** A "keep" decision introduces a subtle bug (e.g., accidentally dropping a feature column), subsequent experiments build on the broken base, accuracy degrades, and the agent tries increasingly desperate changes to recover.
3. **Conflicting reverts:** Agent reverts a change but the experiments.jsonl log still shows the experiment. Later the agent re-tries the same failed experiment.
4. **train.py drift:** After many iterations, train.py becomes an unmaintainable mess of commented-out code, dead branches, and accumulated hacks.

**Why it happens:** The experiment loop is essentially an optimization algorithm with a human-like agent as the optimizer. Without proper termination conditions, deduplication, and code quality gates, it degrades like any uncontrolled search process.

**Consequences:** Hours of wasted compute. Corrupted model pipeline. Unreproducible results. train.py becomes unreadable.

**Prevention:**
- **Termination conditions in program.md:** "Stop after 20 experiments OR after 3 consecutive experiments with <0.3% improvement OR if accuracy exceeds 58%."
- **Experiment deduplication:** Before running, check experiments.jsonl for a semantically similar prior experiment. Skip if already tried.
- **Git commit before each experiment:** Every iteration starts with a clean commit. Revert means `git checkout -- models/train.py`, not manual undo.
- **Code quality gate:** After each keep, the code must still pass linting and type checks. No accumulation of dead code.
- **Structured experiment descriptions:** Each experiment logged with a typed description (e.g., "add feature: opponent_pass_rate_last_5") so deduplication is possible.

**Detection:** Experiments.jsonl growing past 30 entries. Multiple sequential reverts. Accuracy oscillating around the same value for 5+ experiments.

**Phase relevance:** Model Training phase. Define loop governance rules BEFORE starting the loop.

---

### Pitfall 6: FastAPI Model Serving Cold Start and Stale Model

**What goes wrong:**
1. **Cold start latency:** Loading an XGBoost model from disk on first request takes 1-5 seconds. If the model is loaded per-request (a common beginner pattern), every prediction is slow.
2. **Stale model in memory:** The model is loaded at FastAPI startup and cached in memory. When a new model is trained and approved, the running API still serves the old model. Without a reload mechanism, you must restart the entire service.
3. **Feature/model version mismatch:** The API serves model v5 but the feature engineering code has been updated for model v6 (new columns, renamed features, different normalization). Predictions silently use wrong feature transformations.

**Why it happens:** FastAPI is a web framework, not a model serving platform. Model lifecycle management is DIY.

**Consequences:** Slow predictions. Serving stale models without knowing. Silent prediction errors from feature mismatches.

**Prevention:**
- **Load model at startup in a lifespan event**, not per-request. Store in `app.state.model`.
- **Add a `/reload` endpoint** (POST, protected) that reloads the model from disk. Call this after a successful keep decision.
- **Version the model and feature pipeline together.** Save a `model_metadata.json` alongside the model artifact that records which feature columns are expected, in what order, and with what preprocessing. The API validates incoming features against this metadata before prediction.
- **Health check endpoint** that returns the currently loaded model version and last-reload timestamp.

**Detection:** Check response times on the `/predict` endpoint. Monitor which model version the API reports vs. which is latest on disk.

**Phase relevance:** API Serving phase. Design the reload/versioning pattern before building the API.

---

## Moderate Pitfalls

---

### Pitfall 7: Home/Away Feature Asymmetry

**What goes wrong:** Features are computed from the home team's perspective only. The model learns "home team yards per game" and "away team yards per game" but these are not symmetric transformations of the same underlying team stats. When a team switches from home to away, its features change meaning. Some builders create separate home and away rolling stats, doubling the feature space and halving the data each stat is computed from.

**Prevention:**
- Compute team-level rolling stats independent of home/away status. Then in the game-level feature row, assign them as "team_A_stat" and "team_B_stat" based on home/away.
- Include a simple `is_home` binary feature to let the model learn home-field advantage.
- Do not create separate rolling averages for "when home" vs. "when away" -- insufficient sample size per split.

**Phase relevance:** Feature Engineering phase.

---

### Pitfall 8: Early-Season Feature Instability

**What goes wrong:** Rolling features for Weeks 1-3 are computed from 0-2 prior games. A team's "yards per game over last 5 games" in Week 2 is based on 1 game -- extremely noisy. The model either gets confused by these unstable values or overfits to early-season noise.

**Prevention:**
- Use expanding windows with a minimum period: `expanding(min_periods=3).mean()`. For games with fewer than `min_periods` prior games, fill with the league-wide average for that stat.
- Include a `games_played_so_far` feature so the model can learn to weight early-season predictions with lower confidence.
- Consider using prior season's final stats as a "preseason prior" that decays as current-season data accumulates.

**Phase relevance:** Feature Engineering phase.

---

### Pitfall 9: MLflow Experiment Tracking Drift

**What goes wrong:**
1. **Experiment naming chaos:** Experiments are created ad hoc with names like "test", "test2", "final", "final_v2". After 30 runs, the MLflow UI is unusable.
2. **Missing parameters:** Some runs log hyperparameters, others do not. Comparison becomes impossible.
3. **Artifact storage bloat:** Every run saves the full model artifact. With 50+ experiments, disk fills up.
4. **Dual-logging inconsistency:** experiments.jsonl and MLflow drift apart -- one has runs the other does not, or fields differ.

**Prevention:**
- Define a fixed MLflow experiment name at project start (e.g., "nfl-game-predictor").
- Create a `log_experiment()` function that writes to BOTH experiments.jsonl AND MLflow atomically. Never log to one without the other.
- Mandatory parameter schema: every run logs `{features_used, n_estimators, max_depth, learning_rate, train_seasons, val_season, accuracy, brier_score, log_loss, timestamp}`.
- Only save model artifacts for "keep" decisions, not reverted experiments. Log metrics for all.
- Use MLflow run tags to mark "kept" vs. "reverted" runs.

**Phase relevance:** Infrastructure/Setup phase (before model training begins).

---

### Pitfall 10: Target Variable Construction Errors

**What goes wrong:** The win/loss target is constructed incorrectly. Common bugs:
- Ties are silently dropped or assigned to one class, biasing the dataset.
- The target is computed from the home team's perspective but features are computed from both perspectives, creating 2 rows per game. If both rows predict the same game, the model sees correlated duplicate predictions.
- Overtime games have different dynamics but are treated identically.

**Prevention:**
- Decide on row structure upfront: one row per game (predicting home team win) or two rows per game (each team's perspective, but then you MUST NOT have both rows from the same game in the same train/val split -- they are not independent).
- One row per game (home team perspective) is simpler and avoids the duplication trap. Recommended for v1.
- Handle ties explicitly: assign as 0.5, drop them (rare in NFL, ~1 per season), or assign to away team (tie = home team failed). Document the choice.

**Phase relevance:** Feature Engineering phase (target definition).

---

### Pitfall 11: Ignoring the 53% Baseline Context

**What goes wrong:** The 53% benchmark sounds easy to beat -- it is not. NFL games are close to 50/50 events with home-field advantage providing ~2-3% edge. Vegas lines, powered by massive data operations, achieve roughly 53% against the spread and ~65% on moneyline favorites. A simple "always pick the home team" model gets ~57%. A "pick the team with the better record" heuristic gets ~60%. If your ML model cannot beat these trivial baselines, it is not learning anything useful.

**Prevention:**
- Implement and log trivial baselines alongside every experiment: always-home, better-record, higher-ELO.
- The 53% target should be a minimum threshold, not a goal. Compare against the trivial baselines to prove the model adds value beyond simple heuristics.
- If the model achieves 56% but always-pick-home achieves 57%, the model is worse than useless despite "beating" 53%.

**Phase relevance:** Model Training phase. Baselines must be established in the first experiment.

---

## Minor Pitfalls

---

### Pitfall 12: Docker Compose Configuration for ML Workloads

**What goes wrong:** PostgreSQL, FastAPI, MLflow, and potentially a training container all in Docker Compose. Common issues: PostgreSQL data not persisted (forgot volume mount), MLflow artifacts stored inside the container (lost on rebuild), training container runs out of memory because no limits set, network configuration prevents FastAPI from reaching PostgreSQL.

**Prevention:**
- Named volumes for PostgreSQL data AND MLflow artifact store from day one.
- Set memory limits for the training container.
- Use Docker Compose health checks so the API does not start before PostgreSQL is ready.
- Use a `.env` file for database credentials -- never hardcode in docker-compose.yml.

**Phase relevance:** Deployment phase.

---

### Pitfall 13: Weekly Data Refresh Race Condition

**What goes wrong:** The weekly pipeline (fetch new data, compute features, optionally retrain) runs while the API is serving predictions. If the pipeline updates the database mid-computation, the API might serve predictions based on partially-updated features.

**Prevention:**
- Use a staging table pattern: load new data into staging tables, compute features there, then atomically swap.
- Or simpler: schedule the refresh during low-traffic hours and briefly take the API offline (acceptable for a personal/portfolio project).
- Never retrain and serve from the same model file simultaneously.

**Phase relevance:** Pipeline/Deployment phase.

---

### Pitfall 14: Confusing Accuracy Metrics Across Different Contexts

**What goes wrong:** Reporting "62% accuracy" without specifying whether that is training accuracy, validation accuracy, test accuracy, accuracy on favorites only, accuracy on close games, or accuracy on a specific week range. Stakeholders (or your future self) cannot interpret the number.

**Prevention:**
- Always log metrics with explicit context: `{"metric": "accuracy", "split": "val_2023", "value": 0.563, "n_games": 272}`.
- Dashboard should show validation accuracy prominently and training accuracy with a clear "this is training accuracy, expect it to be higher" note.
- Break down accuracy by: overall, home favorites, away favorites, close-spread games, divisional games.

**Phase relevance:** Model Training and Dashboard phases.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Data Ingestion | nfl-data-py schema changes silently break feature code across seasons (Pitfall 3) | Validate schema per-season, build normalization mapping, check game counts |
| Feature Engineering | Future data leakage in rolling features (Pitfall 1) -- the #1 project killer | Mandatory `.shift(1)` on all rolling/expanding ops, write leakage unit tests |
| Feature Engineering | Home/away asymmetry and early-season instability (Pitfalls 7, 8) | Team-level stats independent of venue, minimum periods with league-average fill |
| Feature Engineering | Target variable construction errors (Pitfall 10) | One row per game (home perspective), explicit tie handling |
| Model Training | Overfitting to 2023 validation season (Pitfall 4) | Cap iterations, track multi-season accuracy, monitor calibration |
| Model Training | Experiment loop degeneration (Pitfall 5) | Termination conditions in program.md, git commit per iteration, deduplication |
| Model Training | Ignoring trivial baselines (Pitfall 11) | Always-home and better-record baselines logged from experiment #1 |
| Experiment Tracking | MLflow/jsonl dual-logging drift (Pitfall 9) | Single `log_experiment()` function, mandatory parameter schema |
| API Serving | Cold start, stale model, feature/model version mismatch (Pitfall 6) | Lifespan model loading, `/reload` endpoint, version metadata |
| Deployment | Docker volume persistence, refresh race conditions (Pitfalls 12, 13) | Named volumes, staging tables or maintenance windows |
| Dashboard | Confusing accuracy contexts (Pitfall 14) | Explicit metric labeling with split, sample size, and breakdown |

---

## Sources

- Training-data-based domain knowledge on sports ML prediction, nfl-data-py, XGBoost, MLflow, FastAPI. MEDIUM confidence overall.
- Web verification was unavailable during this research session. Findings should be validated against current nfl-data-py documentation and recent community discussions.
- Specific nfl-data-py column and team abbreviation details based on training data from nflfastR/nfl-data-py ecosystem as of mid-2024. Schema may have changed -- verify against `nfl.import_pbp_data([2024])` column listing.
