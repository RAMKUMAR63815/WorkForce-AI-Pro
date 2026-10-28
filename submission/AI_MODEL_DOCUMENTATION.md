# WorkForce AI Pro — AI Model Documentation

## 1. Overview

WorkForce AI Pro is an HR Attrition Prediction and Workforce Intelligence Platform designed to help HR teams analyze workforce information and identify employees who may be at risk of leaving an organization.

The AI module supports dataset management, model training, prediction, attrition analytics, and risk monitoring.

**Important:** The exact machine-learning algorithm, training metrics, feature list, and prediction thresholds must be documented from the implemented code and actual training results. They should not be assumed.

## 2. Objectives

The AI module aims to:

- Analyze workforce and employee-related data.
- Train an attrition prediction model using an available dataset.
- Generate predictions using the implemented prediction API.
- Support HR decision-making with analytics.
- Monitor employee attrition risk over time.
- Support alerts and follow-up interventions where implemented.

Predictions are intended to support HR decisions, not replace human judgment.

## 3. AI Workflow

The intended workflow is:

1. **Dataset submission:** An authorized user submits or registers a dataset.
2. **Dataset validation:** The backend processes the dataset and reports validation errors where supported.
3. **Model training:** The training endpoint uses the selected dataset.
4. **Prediction:** The prediction endpoint processes an input request.
5. **Risk monitoring:** Prediction results may be recorded for later analysis.
6. **Alert evaluation:** The alert service evaluates employees according to the configured business rules.
7. **Dashboard reporting:** HR users review available analytics and monitoring results.
8. **Intervention:** Authorized HR personnel review risk information and determine appropriate follow-up actions.

The exact sequence of database writes and automatic recalculation depends on the implemented backend.

## 4. Dataset Management

The dataset API supports the following routes:

| Endpoint                                | Purpose                            |
| --------------------------------------- | ---------------------------------- |
| `GET /api/datasets/`                    | Retrieve dataset records           |
| `POST /api/datasets/`                   | Submit or register a dataset       |
| `GET /api/datasets/{dataset_id}`        | Retrieve dataset details           |
| `GET /api/datasets/{dataset_id}/errors` | Retrieve dataset validation errors |

Refer to the live OpenAPI specification for exact request formats, accepted file types, and validation requirements.

### Dataset quality considerations

Before training a model, verify:

- Required columns are present.
- Data types match the expected schema.
- Missing values are handled appropriately.
- Duplicate records are reviewed.
- The target label is available for supervised training.
- Sensitive employee information is handled securely.
- Training and evaluation data are separated appropriately.

These are recommended validation practices; the checks actually enforced by the application must be verified in the code.

## 5. Model Training

**Endpoint:** `POST /api/attrition/train/{dataset_id}`

This endpoint initiates model training using the selected dataset.

The training implementation should define:

- Input features.
- Attrition target column.
- Data preprocessing.
- Missing-value handling.
- Categorical feature encoding.
- Training and test split strategy.
- Model selection and hyperparameters.
- Model persistence and versioning.
- Evaluation metrics and error handling.

The actual algorithm and configuration must be taken from the project's training code.

### Model evaluation

For a classification model, useful evaluation measures may include:

| Metric           | Meaning                                                               |
| ---------------- | --------------------------------------------------------------------- |
| Accuracy         | Fraction of predictions that are correct                              |
| Precision        | Fraction of predicted attrition cases that are actual attrition cases |
| Recall           | Fraction of actual attrition cases detected by the model              |
| F1-score         | Harmonic mean of precision and recall                                 |
| ROC-AUC          | Measures ranking performance across classification thresholds         |
| Confusion matrix | Shows true and false positive and negative predictions                |

Do not report metric values until they have been calculated from an actual evaluation run. Accuracy alone may be misleading when attrition cases are relatively uncommon.

## 6. Attrition Prediction

**Endpoint:** `POST /api/attrition/predict`

The prediction endpoint accepts input defined by the application's request schema and returns the response defined by the prediction implementation.

The prediction pipeline may include:

1. Request validation.
2. Feature preparation.
3. Application of the trained model and any fitted preprocessing.
4. Prediction generation.
5. Formatting of the API response.
6. Recording the result, if supported by the implementation.

The request fields, response structure, probability calculation, and error cases should be verified through Swagger UI and the relevant source code.

### Interpreting predictions

If the model returns a probability, it should be interpreted as a model estimate, not a guarantee that an employee will leave.

Any risk categories such as low, medium, or high must follow documented thresholds from the actual implementation. Do not invent thresholds or treat an uncalibrated probability as a reliable real-world probability.

## 7. Model Information and History

| Endpoint                     | Purpose                                                               |
| ---------------------------- | --------------------------------------------------------------------- |
| `GET /api/attrition/models`  | Retrieve available model information                                  |
| `GET /api/attrition/history` | Retrieve prediction or model history, according to the implementation |

History and model metadata can help with traceability. Where supported, record the model version, training dataset, training timestamp, evaluation metrics, and prediction timestamp.

## 8. Attrition Analytics

**Endpoint:** `GET /api/attrition-analytics/summary`

The analytics endpoint supplies attrition-related summary information according to the current implementation.

Useful workforce analytics may include:

- Employee headcount.
- Historical attrition counts.
- Attrition rates over a defined period.
- Distribution of predicted risk levels.
- Department-level workforce trends.
- Changes in risk over time.

These are possible analytics, not a claim that every metric is currently returned by the endpoint. Verify the response schema before documenting individual fields.

## 9. Risk Monitoring

The risk-monitoring API includes:

| Endpoint                                                   | Purpose                                     |
| ---------------------------------------------------------- | ------------------------------------------- |
| `GET /api/risk-monitoring/summary`                         | Retrieve a monitoring summary               |
| `GET /api/risk-monitoring/logs`                            | Retrieve monitoring logs                    |
| `GET /api/risk-monitoring/employees/{employee_id}/history` | Retrieve risk history for an employee       |
| `GET /api/employee-risk-alert-dashboard/summary`           | Retrieve employee risk-alert dashboard data |

Monitoring supports reviewing historical information and understanding how recorded risk information changes over time.

The precise recalculation schedule, event triggers, logging rules, and data retention behavior must be confirmed from the implementation.

## 10. Attrition Alerts

**Endpoint:** `POST /api/attrition-alerts/evaluate`

The alert evaluation process checks employee records against the application's configured rules.

The endpoint may support a `cooldown_hours` query parameter, subject to the live route definition.

An alert workflow may involve:

1. Identifying records eligible for evaluation.
2. Applying configured risk criteria.
3. Checking for existing alerts or cooldown restrictions.
4. Creating alerts when conditions are satisfied.
5. Recording evaluation results.

The actual alert conditions and cooldown behavior must be verified in the service code. A prediction does not necessarily cause an immediate alert unless the application explicitly implements that behavior.

## 11. HR Intervention and Responsible Use

Attrition predictions should be used as decision-support information.

Recommended practices:

- Let authorized HR staff review predictions before taking action.
- Do not automatically penalize, dismiss, or disadvantage employees based only on model output.
- Restrict access to employee-level predictions.
- Avoid using unnecessary personal or sensitive attributes.
- Evaluate performance across relevant employee groups where legally and ethically appropriate.
- Investigate false positives and false negatives.
- Keep an audit trail of consequential decisions where appropriate.
- Provide suitable human review and correction procedures.

## 12. Security and Privacy

The AI module operates within the platform's authentication and authorization system.

Recommended safeguards include:

- JWT authentication for protected APIs.
- Role-based authorization for dataset, training, prediction, and monitoring operations.
- Validation of uploaded files and request payloads.
- Secure handling of employee identifiers and workforce data.
- Protection of model files and training artifacts.
- Environment-based secret management.
- Restricted access to logs and prediction history.
- Appropriate retention and deletion policies.

Confirm the actual permission requirements for each AI endpoint before deployment.

## 13. Testing and Verification

Use Swagger UI:

`http://localhost:8003/docs`

Suggested verification sequence:

1. Confirm backend and database health.
2. Authenticate as an authorized test user.
3. Submit a valid dataset.
4. Verify dataset details and validation errors.
5. Train a model with a valid dataset.
6. Review the training response and evaluation results.
7. Submit a valid prediction request.
8. Check model information and history.
9. Verify analytics and risk-monitoring responses.
10. Evaluate alert behavior using test records.
11. Test invalid inputs and unauthorized access.
12. Record actual results in `TEST_RESULTS.md`.

Use test data where possible. Do not expose real employee information in screenshots or reports.

## 14. Limitations

Model quality depends on dataset quality, feature relevance, class distribution, training procedures, and changes in workforce behavior.

Potential limitations include:

- Incomplete or outdated employee records.
- Historical patterns that do not represent future conditions.
- False-positive and false-negative predictions.
- Bias inherited from historical data.
- Changes in organizational policy or labor-market conditions.
- Limited model explainability.
- Lack of sufficient data for reliable evaluation.

Document the limitations observed in the actual model and its evaluation results.

## 15. Model Documentation Checklist

Before final project submission, complete the following using evidence from the implementation:

- [x] Actual algorithm name.
- [x] Dataset name and source.
- [x] Target column.
- [x] Features used by the model.
- [x] Data preprocessing steps.
- [x] Training and test split.
- [x] Model version and persistence method.
- [x] Actual evaluation metrics.
- [x] Actual prediction request and response examples.
- [x] Risk classification rules, if implemented.
- [x] Alert conditions and cooldown behavior.
- [x] Access permissions for AI endpoints.
- [x] Known limitations and responsible-use safeguards.

## 16. Summary

The AI component of WorkForce AI Pro provides API capabilities for dataset management, attrition model training, prediction, analytics, and risk monitoring.

The final technical report must reflect the implemented code and measured results. Model details, metric values, and performance claims should be added only after they have been verified.

**Project:** WorkForce AI Pro
**Backend:** FastAPI
**Database:** MySQL
**ML libraries:** Verify against the project's dependency files
**API specification:** OpenAPI
