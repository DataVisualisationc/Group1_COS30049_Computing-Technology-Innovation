import os
import joblib
import pandas as pd


# ============================================================
# SETTINGS
# ============================================================

MODEL_FOLDER = "trained_models"

MODEL_FILE = os.path.join(
    MODEL_FOLDER,
    "gradient_boosting_model.joblib"
)

TEST_FILE = os.path.join(
    MODEL_FOLDER,
    "testing_set.csv"
)

# Change this number to test a different row
ROW_NUMBER = 0


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

print("=" * 70)
print("LOAD TRAINED MODEL")
print("=" * 70)

model = joblib.load(
    MODEL_FILE
)

print(
    "Model loaded:",
    MODEL_FILE
)


# ============================================================
# LOAD TEST DATA
# ============================================================

test_df = pd.read_csv(
    TEST_FILE
)

print(
    "Testing data loaded:",
    TEST_FILE
)

print(
    "Testing rows:",
    len(test_df)
)


# ============================================================
# CHECK ROW NUMBER
# ============================================================

if ROW_NUMBER < 0 or ROW_NUMBER >= len(test_df):

    raise IndexError(
        f"ROW_NUMBER {ROW_NUMBER} is invalid. "
        f"Choose between 0 and {len(test_df) - 1}."
    )


# ============================================================
# SELECT ONE TEST ROW
# ============================================================

row = test_df.iloc[
    [ROW_NUMBER]
].copy()


# ============================================================
# DISPLAY ORIGINAL ROW INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("TEST ROW")
print("=" * 70)

print(
    "Row number:",
    ROW_NUMBER
)


if "storm_name" in row.columns:

    print(
        "Storm name:",
        row["storm_name"].iloc[0]
    )


if "date" in row.columns:

    print(
        "Date:",
        row["date"].iloc[0]
    )


if "datetime" in row.columns:

    print(
        "Datetime:",
        row["datetime"].iloc[0]
    )


if "latitude" in row.columns:

    print(
        "Latitude:",
        row["latitude"].iloc[0]
    )


if "longitude" in row.columns:

    print(
        "Longitude:",
        row["longitude"].iloc[0]
    )


if "nearest_prefecture" in row.columns:

    print(
        "Nearest prefecture:",
        row["nearest_prefecture"].iloc[0]
    )


if "distance_to_prefecture_km" in row.columns:

    print(
        "Distance to prefecture:",
        row["distance_to_prefecture_km"].iloc[0],
        "km"
    )


if "days_before_landfall" in row.columns:

    print(
        "Days before landfall:",
        row["days_before_landfall"].iloc[0]
    )


if "relative_day" in row.columns:

    print(
        "Relative day:",
        row["relative_day"].iloc[0]
    )


if "risk" in row.columns:

    print(
        "Actual risk:",
        row["risk"].iloc[0]
    )


# ============================================================
# COLUMNS THAT WERE NOT USED DURING TRAINING
# ============================================================
#
# IMPORTANT:
# This must match the DROP_COLUMNS from the training script.
#
# ============================================================

DROP_COLUMNS = [

    # --------------------------------------------------------
    # TARGET
    # --------------------------------------------------------

    "risk",


    # --------------------------------------------------------
    # DIRECT TARGET LEAKAGE
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
    # DATE / TIME
    # --------------------------------------------------------

    "datetime",

    "date",

    "datetime_yymmddhh",


    # --------------------------------------------------------
    # STORM IDENTIFIERS
    # --------------------------------------------------------

    "intl_id",

    "storm_number",

    "storm_name",

    "last_revision_date",


    # --------------------------------------------------------
    # DATASET CONSTRUCTION
    # --------------------------------------------------------

    "complete_4day_sequence",

    "row_key",

    "weather_download_status",

    "weather_error",

    "openmeteo_timezone",


    # --------------------------------------------------------
    # PREFECTURE NAME
    #
    # We excluded the prefecture name during training.
    # distance_to_prefecture_km is still allowed.
    # --------------------------------------------------------

    "nearest_prefecture",
]


# ============================================================
# ONLY DROP COLUMNS THAT EXIST
# ============================================================

DROP_COLUMNS = [

    column

    for column in DROP_COLUMNS

    if column in row.columns
]


# ============================================================
# CREATE MODEL INPUT
# ============================================================

X = row.drop(
    columns=DROP_COLUMNS
)


# ============================================================
# DISPLAY FEATURES SENT TO MODEL
# ============================================================

print("\n" + "=" * 70)
print("FEATURES SENT TO MODEL")
print("=" * 70)


for column in X.columns:

    value = X[
        column
    ].iloc[0]

    print(
        f"{column}: {value}"
    )


# ============================================================
# MAKE PREDICTION
# ============================================================

prediction = model.predict(
    X
)[0]


# ============================================================
# DISPLAY PREDICTION
# ============================================================

print("\n" + "=" * 70)
print("PREDICTION RESULT")
print("=" * 70)


print(
    "Predicted risk:",
    prediction
)


# ============================================================
# DISPLAY ACTUAL ANSWER
# ============================================================

if "risk" in row.columns:

    actual_risk = row[
        "risk"
    ].iloc[0]

    print(
        "Actual risk   :",
        actual_risk
    )


    # ========================================================
    # CORRECT / INCORRECT
    # ========================================================

    if prediction == actual_risk:

        print(
            "\nCORRECT PREDICTION"
        )

    else:

        print(
            "\nINCORRECT PREDICTION"
        )


# ============================================================
# PREDICTION PROBABILITIES
# ============================================================

if hasattr(
    model,
    "predict_proba"
):

    probabilities = model.predict_proba(
        X
    )[0]

    classes = model.classes_

    print("\n" + "=" * 70)
    print("PREDICTION PROBABILITIES")
    print("=" * 70)


    # --------------------------------------------------------
    # Convert probabilities into dictionary
    # --------------------------------------------------------

    probability_dict = {}

    for class_name, probability in zip(
        classes,
        probabilities
    ):

        probability_dict[
            class_name
        ] = probability


    # --------------------------------------------------------
    # Display in Low -> Moderate -> High order
    # --------------------------------------------------------

    display_order = [
        "Low",
        "Moderate",
        "High"
    ]


    for risk_level in display_order:

        if risk_level in probability_dict:

            probability = (
                probability_dict[
                    risk_level
                ]
            )

            print(
                f"{risk_level:<10}: "
                f"{probability * 100:.2f}%"
            )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)


if "storm_name" in row.columns:

    print(
        "Storm:",
        row["storm_name"].iloc[0]
    )


if "nearest_prefecture" in row.columns:

    print(
        "Nearest prefecture:",
        row[
            "nearest_prefecture"
        ].iloc[0]
    )


if "days_before_landfall" in row.columns:

    print(
        "Days before landfall:",
        row[
            "days_before_landfall"
        ].iloc[0]
    )


print(
    "Model prediction:",
    prediction
)


if "risk" in row.columns:

    print(
        "Actual answer:",
        actual_risk
    )


print("\nTesting complete.")