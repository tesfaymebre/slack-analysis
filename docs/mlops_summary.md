# MLOps Components Summary

This project uses the following MLOps components during Task 2.

## 1. Feature Store
A feature store centralizes reusable ML features so training and serving use the same definitions. In this challenge, PostgreSQL (Task 3) will act as the feature store for user stats, channel metrics, sentiment scores, and topic features produced in Tasks 1 and 2.

## 2. Model Versioning (MLflow)
MLflow tracks experiments, parameters, metrics, and model artifacts. In Task 2 we log:
- message classification models
- topic modelling outputs
- daily sentiment summaries

This makes experiments reproducible and lets us compare runs over time.

## 3. Model Monitoring
Model monitoring watches production performance for drift, latency, and quality degradation. For this Slack analysis project, monitoring would track:
- classifier label distribution changes
- sentiment trend shifts
- topic drift across channels

## 4. Continuous Integration (CI)
GitHub Actions run flake8, unit tests, and docstring checks on every push/PR. This is **Continuous Integration** — validating code quality before merge.

## 5. Continuous Delivery / Deployment (CD)
Task 5 adds Docker packaging and deployment automation. CD extends CI by automatically building and publishing deployable artifacts after tests pass.

## 6. Dockerization
Docker packages the app and dependencies into a portable image. This ensures the dashboard and ML pipeline run consistently across laptops, CI runners, and cloud servers.

## 7. Data and Model Pipelines
The analysis pipeline follows CRISP-DM:
1. Load raw Slack JSON
2. Parse into structured DataFrames
3. Engineer features for EDA and ML
4. Train and evaluate models
5. Log artifacts with MLflow
6. Expose results in dashboards and databases

## How they fit together

```text
Raw Slack JSON -> src/loader.py -> Features -> ML models -> MLflow
                                      |                        |
                                      v                        v
                               PostgreSQL (Task 3)        Streamlit (Task 4)
```

CI validates code on every change. MLflow versions models. PostgreSQL stores features. Streamlit and Docker deliver insights to users.
