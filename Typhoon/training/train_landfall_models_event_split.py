import os
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier
)

from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC


# ============================================================
# PATH SETTINGS
# ============================================================

SCRIPT_FOLDER = os.path.dirname(
    os.path.abspath(__file__)
)

INPUT_FILE = os.path.join(
    SCRIPT_FOLDER,
    "jma_day3_to_landfall_with_weather_prefecture.csv"
)

OUTPUT_FOLDER = os.path.join(
    SCRIPT_FOLDER,
    "trained_models"
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# TRAINING SETTINGS
# ============================================================

RANDOM_STATE = 42
TEST_SIZE = 0.20


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 70)
print("TYPHOON LANDFALL RISK CLASSIFICATION")
print("=" * 70)

print("\nInput:")
print(INPUT_FILE)

print("\nOutput folder:")
print(OUTPUT_FOLDER)


df = pd.read_csv(
    INPUT_FILE
)


print("\nTotal rows:", len(df))

print(
    "Total landfall events:",
    df["landfall_event_id"].nunique()
)

print("\nRisk distribution:")

print(
    df["risk"].value_counts()
)


# ============================================================
# TARGET
# ============================================================

y = df["risk"]


# ============================================================
# GROUP
#
# Keep every row belonging to the same landfall event
# together during the train/test split.
# ============================================================

groups = df[
    "landfall_event_id"
]


# ============================================================
# 80 / 20 EVENT-LEVEL SPLIT
# ============================================================

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE
)


train_idx, test_idx = next(

    splitter.split(
        df,
        y,
        groups=groups
    )

)


train_df = df.iloc[
    train_idx
].copy()


test_df = df.iloc[
    test_idx
].copy()


# ============================================================
# SPLIT INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("80/20 EVENT-LEVEL SPLIT")
print("=" * 70)


print(
    "Training rows:",
    len(train_df)
)

print(
    "Testing rows:",
    len(test_df)
)


print(
    "Training events:",
    train_df[
        "landfall_event_id"
    ].nunique()
)

print(
    "Testing events:",
    test_df[
        "landfall_event_id"
    ].nunique()
)


# ============================================================
# VERIFY NO EVENT LEAKAGE
# ============================================================

train_events = set(
    train_df[
        "landfall_event_id"
    ]
)

test_events = set(
    test_df[
        "landfall_event_id"
    ]
)


overlap = train_events.intersection(
    test_events
)


print(
    "Event overlap:",
    len(overlap)
)


assert len(overlap) == 0, (
    "DATA LEAKAGE DETECTED: "
    "same landfall event exists in training and testing."
)


print(
    "No event leakage detected."
)


# ============================================================
# TRAIN / TEST CLASS DISTRIBUTION
# ============================================================

print(
    "\nTraining risk distribution:"
)

print(
    train_df[
        "risk"
    ].value_counts()
)


print(
    "\nTesting risk distribution:"
)

print(
    test_df[
        "risk"
    ].value_counts()
)


# ============================================================
# SAVE TRAIN / TEST DATA
#
# ONLY saved inside trained_models/
# ============================================================

TRAIN_FILE = os.path.join(
    OUTPUT_FOLDER,
    "training_set.csv"
)


TEST_FILE = os.path.join(
    OUTPUT_FOLDER,
    "testing_set.csv"
)


train_df.to_csv(
    TRAIN_FILE,
    index=False,
    encoding="utf-8-sig"
)


test_df.to_csv(
    TEST_FILE,
    index=False,
    encoding="utf-8-sig"
)


print(
    "\nSaved training set:",
    TRAIN_FILE
)

print(
    "Saved testing set:",
    TEST_FILE
)


# ============================================================
# COLUMNS NOT USED FOR TRAINING
# ============================================================

DROP_COLUMNS = [

    # --------------------------------------------------------
    # TARGET
    # --------------------------------------------------------

    "risk",


    # --------------------------------------------------------
    # DIRECT LABEL LEAKAGE
    # --------------------------------------------------------

    "days_before_landfall",
    "relative_day",
    "is_landfall_day",
    "landfall",


    # --------------------------------------------------------
    # LANDFALL EVENT INFORMATION
    # --------------------------------------------------------

    "landfall_event_id",
    "landfall_datetime",
    "landfall_date",


    # --------------------------------------------------------
    # RAW DATE / TIME IDENTIFIERS
    # --------------------------------------------------------

    "datetime",
    "date",
    "datetime_yymmddhh",


    # --------------------------------------------------------
    # HOUR
    #
    # Removed because we are using DAILY data.
    # --------------------------------------------------------

    "hour",


    # --------------------------------------------------------
    # STORM IDENTIFIERS
    # --------------------------------------------------------

    "intl_id",
    "storm_number",
    "storm_name",
    "last_revision_date",


    # --------------------------------------------------------
    # RAW LOCATION
    #
    # UI uses prefecture instead.
    # --------------------------------------------------------

    "latitude",
    "longitude",

    "openmeteo_latitude",
    "openmeteo_longitude",


    # --------------------------------------------------------
    # DISTANCE
    #
    # UI will not require user to provide distance.
    # --------------------------------------------------------

    "distance_to_prefecture_km",


    # --------------------------------------------------------
    # DATASET CONSTRUCTION / DOWNLOAD INFORMATION
    # --------------------------------------------------------

    "complete_4day_sequence",
    "row_key",
    "weather_download_status",
    "weather_error",
    "openmeteo_timezone",
]


# ============================================================
# IMPORTANT
#
# nearest_prefecture is NOT dropped.
#
# It will therefore be used as a categorical feature.
# ============================================================


# ============================================================
# ONLY DROP COLUMNS THAT EXIST
# ============================================================

DROP_COLUMNS = [

    column

    for column in DROP_COLUMNS

    if column in df.columns
]


# ============================================================
# CREATE FEATURE LIST
# ============================================================

feature_columns = [

    column

    for column in df.columns

    if column not in DROP_COLUMNS
]


# ============================================================
# VERIFY FEATURE CONFIGURATION
# ============================================================

EXCLUDED_LOCATION_FEATURES = [

    "latitude",
    "longitude",
    "openmeteo_latitude",
    "openmeteo_longitude",
    "distance_to_prefecture_km",
    "hour"
]


for feature in EXCLUDED_LOCATION_FEATURES:

    assert feature not in feature_columns, (
        f"ERROR: {feature} should NOT be used."
    )


assert "nearest_prefecture" in feature_columns, (
    "ERROR: nearest_prefecture should be used."
)


# ============================================================
# DISPLAY EXACT FEATURES
# ============================================================

print("\n" + "=" * 70)
print("EXACT FEATURES USED FOR TRAINING")
print("=" * 70)


for number, feature in enumerate(
    feature_columns,
    start=1
):

    print(
        f"{number}. {feature}"
    )


print(
    "\nTotal features:",
    len(feature_columns)
)


print("\nConfirmed:")
print("nearest_prefecture        = INCLUDED")
print("hour                      = EXCLUDED")
print("latitude                  = EXCLUDED")
print("longitude                 = EXCLUDED")
print("openmeteo_latitude        = EXCLUDED")
print("openmeteo_longitude       = EXCLUDED")
print("distance_to_prefecture_km = EXCLUDED")


# ============================================================
# CREATE X / Y
# ============================================================

X_train = train_df[
    feature_columns
].copy()


X_test = test_df[
    feature_columns
].copy()


y_train = train_df[
    "risk"
].copy()


y_test = test_df[
    "risk"
].copy()


# ============================================================
# IDENTIFY NUMERIC FEATURES
# ============================================================

numeric_features = (

    X_train

    .select_dtypes(
        include=np.number
    )

    .columns

    .tolist()
)


# ============================================================
# IDENTIFY CATEGORICAL FEATURES
# ============================================================

categorical_features = [

    column

    for column in X_train.columns

    if column not in numeric_features
]


# ============================================================
# DISPLAY NUMERIC / CATEGORICAL
# ============================================================

print("\n" + "=" * 70)
print("NUMERIC FEATURES")
print("=" * 70)

for feature in numeric_features:

    print(
        feature
    )


print("\n" + "=" * 70)
print("CATEGORICAL FEATURES")
print("=" * 70)

for feature in categorical_features:

    print(
        feature
    )


# ============================================================
# NUMERIC PREPROCESSING
# ============================================================

numeric_transformer = Pipeline(

    steps=[

        (
            "imputer",

            SimpleImputer(
                strategy="median"
            )
        ),

        (
            "scaler",

            StandardScaler()
        )

    ]
)


# ============================================================
# CATEGORICAL PREPROCESSING
#
# nearest_prefecture will be one-hot encoded.
# ============================================================

categorical_transformer = Pipeline(

    steps=[

        (
            "imputer",

            SimpleImputer(
                strategy="most_frequent"
            )
        ),

        (
            "onehot",

            OneHotEncoder(
                handle_unknown="ignore"
            )
        )

    ]
)


# ============================================================
# COMBINE PREPROCESSING
# ============================================================

transformers = []


if numeric_features:

    transformers.append(

        (
            "numeric",
            numeric_transformer,
            numeric_features
        )

    )


if categorical_features:

    transformers.append(

        (
            "categorical",
            categorical_transformer,
            categorical_features
        )

    )


preprocessor = ColumnTransformer(
    transformers=transformers
)


# ============================================================
# MODELS
# ============================================================

models = {


    # --------------------------------------------------------
    # RANDOM FOREST
    # --------------------------------------------------------

    "Random Forest":

        RandomForestClassifier(

            n_estimators=300,

            random_state=RANDOM_STATE,

            class_weight="balanced",

            n_jobs=-1

        ),


    # --------------------------------------------------------
    # CART
    # --------------------------------------------------------

    "CART":

        DecisionTreeClassifier(

            random_state=RANDOM_STATE,

            class_weight="balanced"

        ),


    # --------------------------------------------------------
    # GRADIENT BOOSTING
    # --------------------------------------------------------

    "Gradient Boosting":

        GradientBoostingClassifier(

            random_state=RANDOM_STATE

        ),


    # --------------------------------------------------------
    # SVM
    # --------------------------------------------------------

    "SVM":

        SVC(

            kernel="rbf",

            class_weight="balanced",

            probability=True,

            random_state=RANDOM_STATE

        )
}


# ============================================================
# RESULTS
# ============================================================

results = []


# ============================================================
# TRAIN ALL MODELS
# ============================================================

for model_name, model in models.items():


    print("\n" + "=" * 70)

    print(
        "TRAINING:",
        model_name
    )

    print("=" * 70)


    # ========================================================
    # COMPLETE PIPELINE
    # ========================================================

    pipeline = Pipeline(

        steps=[

            (
                "preprocessor",
                preprocessor
            ),

            (
                "model",
                model
            )

        ]
    )


    # ========================================================
    # TRAIN
    # ========================================================

    pipeline.fit(
        X_train,
        y_train
    )


    # ========================================================
    # CREATE SAFE FILE NAME
    # ========================================================

    safe_name = (

        model_name

        .lower()

        .replace(
            " ",
            "_"
        )
    )


    # ========================================================
    # MODEL PATH
    #
    # ONLY inside trained_models/
    # ========================================================

    MODEL_FILE = os.path.join(

        OUTPUT_FOLDER,

        f"{safe_name}_model.joblib"

    )


    # ========================================================
    # SAVE TRAINED MODEL
    # ========================================================

    joblib.dump(
        pipeline,
        MODEL_FILE
    )


    print(
        "Saved model:",
        MODEL_FILE
    )


    # ========================================================
    # TEST MODEL
    # ========================================================

    predictions = pipeline.predict(
        X_test
    )


    # ========================================================
    # METRICS
    # ========================================================

    accuracy = accuracy_score(
        y_test,
        predictions
    )


    balanced_accuracy = balanced_accuracy_score(
        y_test,
        predictions
    )


    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro"
    )


    # ========================================================
    # STORE RESULT
    # ========================================================

    results.append({

        "Model":
            model_name,

        "Accuracy":
            accuracy,

        "Balanced Accuracy":
            balanced_accuracy,

        "Macro F1":
            macro_f1

    })


    # ========================================================
    # DISPLAY METRICS
    # ========================================================

    print(
        f"\nAccuracy          : "
        f"{accuracy:.4f}"
    )


    print(
        f"Balanced Accuracy : "
        f"{balanced_accuracy:.4f}"
    )


    print(
        f"Macro F1          : "
        f"{macro_f1:.4f}"
    )


    # ========================================================
    # CLASSIFICATION REPORT
    # ========================================================

    print(
        "\nClassification Report:"
    )


    print(

        classification_report(

            y_test,

            predictions,

            labels=[
                "Low",
                "Moderate",
                "High"
            ],

            digits=4,

            zero_division=0
        )
    )


    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    matrix = confusion_matrix(

        y_test,

        predictions,

        labels=[
            "Low",
            "Moderate",
            "High"
        ]
    )


    matrix_df = pd.DataFrame(

        matrix,

        index=[
            "Actual Low",
            "Actual Moderate",
            "Actual High"
        ],

        columns=[
            "Predicted Low",
            "Predicted Moderate",
            "Predicted High"
        ]
    )


    print(
        "\nConfusion Matrix:"
    )


    print(
        matrix_df
    )


# ============================================================
# FINAL MODEL COMPARISON
# ============================================================

results_df = pd.DataFrame(
    results
)


results_df = (

    results_df

    .sort_values(
        "Accuracy",
        ascending=False
    )

    .reset_index(
        drop=True
    )
)


print("\n" + "=" * 70)
print("FINAL MODEL COMPARISON")
print("=" * 70)


print(

    results_df.to_string(

        index=False,

        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# SAVE COMPARISON
#
# ONLY inside trained_models/
# ============================================================

RESULT_FILE = os.path.join(

    OUTPUT_FOLDER,

    "model_comparison_results.csv"

)


results_df.to_csv(
    RESULT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINISHED
# ============================================================

print("\n" + "=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)


print(
    "\nEverything saved inside:"
)

print(
    OUTPUT_FOLDER
)


print(
    "\nFiles:"
)


for filename in sorted(
    os.listdir(
        OUTPUT_FOLDER
    )
):

    print(
        " -",
        filename
    )