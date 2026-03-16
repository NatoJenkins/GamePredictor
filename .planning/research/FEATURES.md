# Feature Landscape

**Domain:** NFL Game Outcome Prediction System
**Researched:** 2026-03-15
**Confidence:** MEDIUM (based on training knowledge of NFL analytics ecosystem, nfl-data-py, and ML experiment patterns; no live web verification available)

## Table Stakes

Features users expect. Missing = product feels incomplete.

### ML Engineered Features (Game-Level from Play-by-Play)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Rolling offensive yards per game (pass + rush) | Most basic team strength signal; every public model uses this | Low | Use 3-game and season-to-date windows. Must use only prior games (no leakage). |
| Rolling points scored / allowed per game | Direct outcome proxy; foundational feature | Low | Same rolling window treatment. Differential (scored - allowed) is often more predictive than raw values. |
| Turnover differential (rolling) | Turnovers are among the strongest single-game predictors | Low | INTs + fumbles lost vs forced. Rolling average smooths variance. |
| Third-down conversion rate (off + def) | Proxy for sustained drive ability and defensive stops | Low | Available directly in play-by-play aggregation. |
| Home/away indicator | Home-field advantage is ~2.5 points historically | Low | Binary feature. One of the most reliably predictive simple features. |
| Rest days / bye week indicator | Short rest (Thursday games) degrades performance measurably | Low | Compute days since last game from schedule data. |
| Win/loss streak (current) | Captures momentum, team form | Low | Count consecutive wins/losses entering the game. |
| Season win percentage to date | Overall team quality measure | Low | Wins / games played, computed only from prior games. |
| EPA per play (offensive and defensive, rolling) | Expected Points Added is the gold standard advanced metric in nfl-data-py | Medium | nfl-data-py provides per-play EPA. Aggregate to game-level, then roll. This is THE feature that separates toy models from real ones. |
| Pass rate over expected (PROE) | Captures offensive play-calling tendency adjusted for situation | Medium | Derived from play-by-play pass/rush decisions vs expected. Requires situation-aware baseline. |
| Opponent-adjusted metrics | Raw stats mislead when schedule strength varies | High | Adjust rolling EPA/yards by opponent defensive rank. Requires computing opponent quality first. |

### Prediction Output Features

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Binary win/loss prediction per game | The core output -- "who wins?" | Low | Direct classifier output. |
| Confidence score (predicted probability) | Users need to know HOW confident the model is, not just the pick | Low | XGBoost predict_proba output. Display as percentage. |
| Historical accuracy tracking | Users cannot trust a model without seeing its track record | Medium | Store all past predictions vs actual outcomes. Show season-level and rolling accuracy. |
| Model accuracy vs naive baseline | "57% accurate" means nothing without "coin flip is 50%, home team always wins is 57%" | Low | Always display model accuracy alongside at least one baseline. |

### Dashboard Features

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| This week's picks with confidence | The primary user-facing view -- "what does the model say this week?" | Medium | Requires weekly data refresh pipeline feeding the UI. |
| Confidence-sorted game list | Users want to see highest-confidence picks first | Low | Simple sort on prediction probability. |
| Season accuracy summary | "How is the model doing this year?" | Low | Win/loss on predictions, displayed as percentage with record (e.g., 142-98). |
| Historical predictions log | Scrollable/filterable list of all past predictions and outcomes | Medium | Paginated table with filters by week, team, correctness. |

### Experiment Tracking Features

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Per-experiment metrics logging (accuracy, log loss, AUC) | Cannot iterate without tracking what was tried and how it performed | Low | Log to experiments.jsonl per the project spec. |
| Experiment comparison (side-by-side) | Need to compare runs to decide keep/revert | Medium | MLflow UI handles this natively. experiments.jsonl needs a viewer or script. |
| Feature list per experiment | Must know which features each run used to understand what drove improvement | Low | Log feature names alongside metrics. |
| Keep/revert decision log | Audit trail of which models were promoted and why | Low | Boolean field in experiments.jsonl plus optional notes. |
| Validation accuracy as primary metric | The project lives or dies on 2023 val accuracy -- it must be front and center | Low | Always display prominently; never let training accuracy confuse the picture. |

## Differentiators

Features that set product apart. Not expected, but valued.

### ML Engineered Features (Advanced)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| CPOE (Completion Percentage Over Expected) | Isolates QB accuracy from scheme/situation; available in nfl-data-py | Medium | Strong signal for passing game quality beyond raw completion %. |
| Success rate (% of plays with positive EPA) | Captures consistency better than averages; a team with steady positive plays is more reliable than one with boom/bust | Medium | Binary per-play metric aggregated to game level, then rolled. |
| Red zone efficiency (off + def) | Scoring when close matters more than moving the ball between the 20s | Medium | Filter plays inside opponent 20, compute TD rate. |
| Weighted rolling averages (recency bias) | Recent games matter more than week 1 performance; exponential decay weighting | Medium | Apply exponential or linear decay to rolling window. Tunable decay parameter. |
| Pace of play (plays per game, time of possession) | Captures game style -- fast offenses create more variance | Low | Direct aggregation from play-by-play. |
| Penalty rate differential | Undisciplined teams lose winnable games; often overlooked feature | Low | Penalties and penalty yards per game, rolling. |
| Strength of schedule (computed) | Adjusts expectations based on who the team has faced | High | Compute from opponents' win rates or EPA ranks. Recursive dependency makes this tricky. |
| Quarterback consistency (EPA std dev) | Low variance QBs win more reliably; captures "game manager" vs "gunslinger" | Medium | Standard deviation of per-play EPA for the QB, rolled across games. |

### Prediction Output Features (Advanced)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Calibrated probabilities (Platt scaling or isotonic regression) | Raw XGBoost probabilities are often not well-calibrated; "70% confidence" should mean 70% win rate historically | Medium | Post-hoc calibration on validation set. Display calibration curve in dashboard. |
| Feature importance per prediction (SHAP values) | "Why did the model pick Team A?" -- explainability builds trust | High | SHAP is computationally expensive but XGBoost has fast TreeSHAP. Show top 3-5 contributing features per game. |
| Confidence tiers (high/medium/low) | Not all picks are equal; users want to know which to trust most | Low | Bucket predictions by probability distance from 0.5. Easy to implement, high UX value. |
| Calibration plot (predicted vs actual win rate) | Visual proof the model's probabilities are meaningful | Medium | Group predictions into probability bins, plot actual win rate vs predicted. |

### Dashboard Features (Advanced)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Team-level deep dive page | Click a team to see its rolling stats, prediction history, feature trends | High | Requires per-team data views and charts. Great for engagement but significant frontend work. |
| Weekly recap with correct/incorrect highlighting | After games complete, show which picks were right/wrong with visual indicators | Medium | Requires result ingestion after game day. Green/red styling on predictions. |
| Model performance over time chart | Line chart of rolling accuracy by week -- shows if model is improving or degrading | Medium | Time series of cumulative or rolling accuracy. Reveals model drift. |
| Feature importance global view | Bar chart of most important features across all predictions | Medium | XGBoost feature_importances_ displayed in dashboard. Helps users understand the model. |

### Experiment Tracking Features (Advanced)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Automated experiment loop (autoresearch pattern) | Agent-driven experimentation accelerates iteration; the agent reads program.md, picks experiments, runs them, logs results | High | Core to the project spec. Requires careful design of the loop, guardrails, and revert logic. |
| Hyperparameter logging and comparison | Track not just features but learning rate, max depth, etc. per run | Low | Log full XGBoost params dict to experiments.jsonl and MLflow. |
| Experiment tagging/categorization | Group experiments by type (feature engineering, hyperparameter tuning, architecture change) | Low | Add a "category" field to experiment logs. |
| Reproducibility (random seed + data hash) | Every experiment must be reproducible -- log the seed and a hash of the training data | Low | Essential for debugging. Log random_state and a hash of feature matrix shape + sample values. |
| Program.md experiment backlog | A living document of experiment ideas for the autoresearch agent to consume | Low | Markdown file listing hypotheses to test. Agent reads and picks next. |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Live in-game win probability | Entirely different problem (real-time data, play-level model, websocket streaming); massive scope creep | Stay pre-game only. In-game models are a separate project. |
| Vegas odds / spread integration | Adds data source complexity, legal/licensing questions, and conflates the model's signal with market signal | Use model probability as the sole confidence signal. Compare to Vegas as an external benchmark only if desired later. |
| Player-level injury tracking | Requires unreliable data sources (injury reports are gamed), player-level modeling is far more complex, and data quality is poor | Use team-level aggregates. If a star player is out, it shows up in team EPA eventually. |
| User accounts and authentication | Over-engineering for v1; adds auth complexity, session management, password handling | Open read access or single-user. Add auth only if/when multi-user demand exists. |
| Betting recommendations / "pick of the day" | Legal liability, gambling addiction concerns, and the model is not proven profitable against the spread | Show predictions and confidence only. Never frame output as betting advice. |
| Complex multi-model ensembles in v1 | Premature optimization; get one model right first | Start with XGBoost. Only ensemble after understanding single-model behavior deeply. |
| Real-time score scraping | Fragile, rate-limited, and not needed for pre-game predictions | Use nfl-data-py's weekly data refresh which updates after games complete. |
| Over-engineered feature store | Feature stores (Feast, etc.) add infrastructure for scale you do not have | Compute features in pandas, store in PostgreSQL. A feature store is warranted at 100+ features and multiple consumers. |
| Mobile app | Significant additional development surface; web dashboard works on mobile browsers | Build a responsive web dashboard. If mobile demand appears, consider PWA before native. |
| Chat/AI explanation interface | "Ask the model why" via LLM is flashy but unreliable and expensive | Use SHAP values for explainability. Static feature importance is more trustworthy than generated explanations. |

## Feature Dependencies

```
Data Ingestion (nfl-data-py) --> Play-by-Play Storage (PostgreSQL)
  |
  v
Game-Level Feature Engineering --> Rolling/Aggregate Features
  |                                    |
  |                                    v
  |                              Opponent-Adjusted Features
  |                                    |
  v                                    v
Feature Matrix (no leakage) ---------> Model Training (XGBoost)
  |                                    |
  |                                    v
  |                              Experiment Logging (experiments.jsonl + MLflow)
  |                                    |
  |                                    v
  |                              Keep/Revert Decision
  |                                    |
  v                                    v
Prediction Generation ----------> Calibrated Probabilities
  |                                    |
  v                                    v
FastAPI Endpoints ------------> React Dashboard
  |                                    |
  v                                    |
Weekly Data Refresh Pipeline           |
  |                                    |
  v                                    v
Automated Retrain ----------------> Updated Predictions
```

Key dependency chains:
- EPA features require play-by-play data (not just game summaries)
- Opponent-adjusted features require all teams' base features to be computed first
- Calibrated probabilities require a trained model and a calibration dataset
- SHAP explanations require a trained model and the feature matrix for each game
- The autoresearch loop requires experiment logging to be working first
- Dashboard accuracy tracking requires stored predictions AND game results

## MVP Recommendation

Prioritize (Phase 1 - Get a Working Model):
1. **Data ingestion + basic rolling features** (yards, points, turnovers, EPA per play, home/away, rest days)
2. **Leakage-safe feature engineering pipeline** -- this is the hardest part to get right and the easiest to get wrong
3. **XGBoost training with temporal split** and logging to experiments.jsonl
4. **Binary prediction + raw probability output**
5. **Basic accuracy tracking** (model vs coin flip vs home-team-always-wins baselines)

Prioritize (Phase 2 - Dashboard + Experiment Loop):
6. **FastAPI endpoints** for current picks and historical accuracy
7. **React dashboard** with this-week's-picks view and season accuracy
8. **MLflow integration** for visual experiment comparison
9. **Autoresearch experiment loop** (agent-driven iteration on models/train.py)

Prioritize (Phase 3 - Polish + Advanced Features):
10. **Probability calibration** (Platt scaling)
11. **SHAP-based explanations** per prediction
12. **Advanced engineered features** (CPOE, success rate, weighted rolling averages, opponent adjustments)
13. **Weekly recap view** with correct/incorrect highlighting
14. **Model performance over time chart**

Defer indefinitely:
- **Player-level features**: team aggregates are sufficient and far simpler
- **Live predictions**: entirely different architecture
- **Vegas integration**: different problem domain
- **Multi-model ensembles**: premature until single model is well-understood

## Engineered Feature Priority (What Actually Predicts NFL Wins)

Based on established NFL analytics literature and the features available in nfl-data-py:

### Tier 1 -- Build First (Highest Predictive Value)
| Feature | Why It Matters |
|---------|---------------|
| EPA per play (off + def, rolling) | THE best single feature family for NFL prediction. Accounts for situation, field position, and down/distance. Available per-play in nfl-data-py. |
| Point differential (rolling) | Direct outcome signal. Highly correlated with future wins. Simple but strong. |
| Turnover differential (rolling) | Turnovers swing games. Net turnovers per game is a top-5 predictor in most published models. |
| Home/away | Consistent ~2.5 point advantage. Free, simple, always available. |

### Tier 2 -- Build Second (Strong Signal, Moderate Complexity)
| Feature | Why It Matters |
|---------|---------------|
| Third-down conversion rate (off + def) | Sustaining drives vs forcing punts. Strong proxy for execution quality. |
| Success rate (% positive EPA plays) | Captures consistency. A team with 50% success rate is more reliable than one averaging same EPA with 30% success rate and big plays. |
| Rest days / bye indicator | Thursday games after Sunday = measurable performance drop. Bye weeks = slight boost. |
| Sack rate (off + def) | Pass protection quality and pass rush quality. Derived from play-by-play sack flags. |
| Rushing yards before contact (off) | Proxy for offensive line quality, which is hard to measure directly. |

### Tier 3 -- Build for Marginal Gains (Diminishing Returns)
| Feature | Why It Matters |
|---------|---------------|
| CPOE | Good QB signal but partially captured by passing EPA already. |
| Red zone efficiency | Matters but small sample sizes per game make rolling averages noisy. |
| Pace / plays per game | Stylistic signal. Fast teams create variance. |
| Opponent-adjusted metrics | Theoretically ideal but computationally complex and recursive. |
| Penalty differential | Real but weak signal. Often more noise than signal. |

### Data Leakage Prevention -- Features to NEVER Compute Wrong
| Leakage Risk | What Goes Wrong | Prevention |
|--------------|----------------|------------|
| Using current-game stats as features | Model sees the outcome in the inputs; 95%+ accuracy that means nothing | Features must be computed from games STRICTLY before the game being predicted |
| Including future games in rolling averages | Leaks future performance into past predictions | Sort by game date, use `.shift(1)` or equivalent before rolling |
| Season-level aggregates including current game | Subtle leakage -- season averages include the game you're predicting | Always exclude current game from any aggregate |
| Test data in training | Temporal split violation | Hard partition: train <= 2022, val = 2023, test = 2024. Never shuffle. |
| Feature scaling fit on full dataset | Scaler sees test distribution | Fit scaler on training data only, transform val/test |

## Sources

- Domain knowledge from NFL analytics community (nflfastR/nfl-data-py ecosystem)
- Established literature on EPA-based prediction models
- XGBoost documentation for feature importance and SHAP integration
- MLflow documentation for experiment tracking patterns
- Note: Web search was unavailable during research; findings are based on training knowledge (MEDIUM confidence)
