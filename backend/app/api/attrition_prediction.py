
import json
import uuid
from pathlib import Path
from app.models.employee import Employee
import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from app.api.risk_monitoring import record_risk
from sqlalchemy import select

from app.api.rbac import DbSession, HRUser
from app.models.dataset import AttritionDataset
from app.models.attrition_prediction import (
    AttritionModel,
    AttritionPrediction,
)
from app.schemas.attrition_prediction import (
    AttritionPredictRequest,
    AttritionPredictionResponse,
)

router = APIRouter(prefix="/attrition", tags=["AI Attrition Prediction"])

DATASET_DIR = Path(__file__).resolve().parents[1] / "uploads" / "datasets"
MODEL_DIR = Path(__file__).resolve().parents[1] / "uploads" / "models"

TARGET_NAMES = {"attrition"}
IDENTIFIER_NAMES = {
    "employeenumber",
    "employeeid",
    "employee_id",
    "id",
}


def normalize_column(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def get_dataset_file(dataset: AttritionDataset) -> Path:
    path = DATASET_DIR / dataset.stored_filename
    if not path.is_file():
        raise HTTPException(404, "Dataset file is missing from storage.")
    return path


@router.post("/train/{dataset_id}")
def train_attrition_model(
    dataset_id: int,
    db: DbSession,
    current_user: HRUser,
):
    dataset = db.get(AttritionDataset, dataset_id)
    if dataset is None:
        raise HTTPException(404, "Dataset not found.")

    if dataset.valid_rows < 10:
        raise HTTPException(
            400, "At least 10 valid rows are required for training."
        )

    file_path = get_dataset_file(dataset)

    try:
        frame = pd.read_csv(file_path)
    except Exception:
        raise HTTPException(400, "Unable to read the dataset CSV.")

    invalid_report = json.loads(dataset.validation_report or "[]")
    invalid_row_numbers = {
        item["row_number"]
        for item in invalid_report
        if "row_number" in item
    }

    # CSV row numbers include the header at row 1.
    frame = frame.loc[
        [index + 2 not in invalid_row_numbers for index in frame.index]
    ].copy()

    target_columns = [
        column for column in frame.columns
        if normalize_column(str(column)) in TARGET_NAMES
    ]
    if len(target_columns) != 1:
        raise HTTPException(
            400, "Dataset must contain exactly one Attrition column."
        )

    target_column = target_columns[0]

    # Normalize the target to binary values.
    target_values = (
        frame[target_column].astype(str).str.strip().str.lower()
    )
    mapping = {
        "yes": 1, "1": 1, "true": 1,
        "no": 0, "0": 0, "false": 0,
    }
    y = target_values.map(mapping)

    valid_target = y.notna()
    frame = frame.loc[valid_target].copy()
    y = y.loc[valid_target].astype(int)

    if y.nunique() < 2:
        raise HTTPException(
            400,
            "Training data must include both attrition and non-attrition examples.",
        )

    drop_columns = [
        column for column in frame.columns
        if column == target_column
        or normalize_column(str(column)) in IDENTIFIER_NAMES
    ]
    X = frame.drop(columns=drop_columns)

    # Remove completely empty columns.
    X = X.dropna(axis=1, how="all")
    if X.empty or X.shape[1] == 0:
        raise HTTPException(400, "Dataset has no usable feature columns.")

    feature_columns = list(X.columns)

    numeric_columns = list(
        X.select_dtypes(include=["number"]).columns
    )
    categorical_columns = [
        column for column in X.columns
        if column not in numeric_columns
    ]

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    transformers = []
    if numeric_columns:
        transformers.append(
            ("numeric", numeric_pipeline, numeric_columns)
        )
    if categorical_columns:
        transformers.append(
            ("categorical", categorical_pipeline, categorical_columns)
        )

    preprocessing = ColumnTransformer(transformers=transformers)
    classifier = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
    )

    pipeline = Pipeline([
        ("preprocessing", preprocessing),
        ("classifier", classifier),
    ])

    accuracy = None
    class_counts = y.value_counts()

    # Report a holdout metric only when both classes have enough examples.
    if len(y) >= 20 and class_counts.min() >= 5:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        pipeline.fit(X_train, y_train)
        accuracy = float(
            accuracy_score(y_test, pipeline.predict(X_test))
        )

    # Train final model on all valid examples.
    pipeline.fit(X, y)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    latest_version = db.scalar(
        select(AttritionModel.version)
        .where(AttritionModel.dataset_id == dataset_id)
        .order_by(AttritionModel.version.desc())
        .limit(1)
    ) or 0

    artifact_filename = f"{uuid.uuid4().hex}.joblib"
    artifact_path = MODEL_DIR / artifact_filename

    joblib.dump(pipeline, artifact_path)

    model_record = AttritionModel(
        dataset_id=dataset_id,
        version=latest_version + 1,
        artifact_filename=artifact_filename,
        feature_columns=json.dumps(feature_columns),
        target_column=target_column,
        trained_by=current_user.id,
        training_rows=len(X),
        accuracy=accuracy,
    )

    try:
        db.add(model_record)
        db.commit()
        db.refresh(model_record)
    except Exception:
        db.rollback()
        artifact_path.unlink(missing_ok=True)
        raise

    return {
        "message": "Attrition model trained successfully.",
        "model_id": model_record.id,
        "dataset_id": dataset_id,
        "model_version": model_record.version,
        "training_rows": len(X),
        "feature_columns": feature_columns,
        "holdout_accuracy": accuracy,
        "accuracy_note": (
            "Measured on a held-out split."
            if accuracy is not None
            else "Not reported: dataset too small for a reliable holdout metric."
        ),
    }


@router.post(
    "/predict",
    response_model=AttritionPredictionResponse,
)
def predict_attrition(
    payload: AttritionPredictRequest,
    db: DbSession,
    current_user: HRUser,
):
    dataset = db.get(AttritionDataset, payload.dataset_id)
    if dataset is None:
        raise HTTPException(404, "Dataset not found.")

    model_record = db.scalar(
        select(AttritionModel)
        .where(AttritionModel.dataset_id == payload.dataset_id)
        .order_by(AttritionModel.version.desc())
        .limit(1)
    )

    if model_record is None:
        raise HTTPException(
            400, "Train a model for this dataset before predicting."
        )

    if payload.employee_id is not None:
        employee = db.get(__import__(
            "app.models.employee", fromlist=["Employee"]
        ).Employee, payload.employee_id)
        if employee is None:
            raise HTTPException(404, "Employee not found.")

    model_path = MODEL_DIR / model_record.artifact_filename
    if not model_path.is_file():
        raise HTTPException(404, "Trained model file is missing.")

    feature_columns = json.loads(model_record.feature_columns)
    missing = [name for name in feature_columns if name not in payload.features]
    if missing:
        raise HTTPException(
            422,
            detail={
                "message": "Prediction input is missing required features.",
                "missing_features": missing,
            },
        )

    row = {name: payload.features[name] for name in feature_columns}
    frame = pd.DataFrame([row])

    try:
        pipeline = joblib.load(model_path)
        probabilities = pipeline.predict_proba(frame)[0]
        classes = list(pipeline.named_steps["classifier"].classes_)
        positive_index = classes.index(1)
    except Exception:
        raise HTTPException(
            400,
            "Prediction failed. Check that input values match the training data.",
        )

    risk = float(probabilities[positive_index])
    predicted_label = "Yes" if risk >= 0.5 else "No"
    confidence = float(max(probabilities))

    prediction = AttritionPrediction(
        model_id=model_record.id,
        dataset_id=payload.dataset_id,
        employee_id=payload.employee_id,
        predicted_label=predicted_label,
        risk_percentage=round(risk * 100, 2),
        confidence_score=round(confidence * 100, 2),
        input_features=json.dumps(row, default=str),
    )

    db.add(prediction)
    db.flush()
    record_risk(db, prediction)
    db.commit()
    db.refresh(prediction)

    return prediction

@router.get("/models")
def list_trained_models(
    db: DbSession,
    current_user: HRUser,
):
    models = db.scalars(
        select(AttritionModel).order_by(
            AttritionModel.created_at.desc()
        )
    ).all()

    return [
        {
            "id": model.id,
            "dataset_id": model.dataset_id,
            "version": model.version,
            "training_rows": model.training_rows,
            "holdout_accuracy": model.accuracy,
            "created_at": model.created_at,
        }
        for model in models
    ]


@router.get("/history")
def get_prediction_history(
    db: DbSession,
    current_user: HRUser,
):
    predictions = db.scalars(
        select(AttritionPrediction)
        .order_by(AttritionPrediction.created_at.desc())
        .limit(500)
    ).all()

    return predictions
