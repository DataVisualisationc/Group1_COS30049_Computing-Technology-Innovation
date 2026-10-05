from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
M = ROOT / "trained_models"

FEATURES = [
    "shortwave_radiation_sum",
    "sunshine_duration",
    "daylight_duration",
    "cloud_cover_mean",
    "dew_point_2m_mean",
    "month",
]

FILES = {
    "Multiple Linear Regression": "linear_regression_temp_max.joblib",
    "Gradient Boosting": "gradient_boosting_temp_max.joblib",
    "HistGradientBoosting": "hist_gradient_boosting_temp_max.joblib",
}


def predict(X):
    predictions = {}

    for name, filename in FILES.items():
        path = M / filename

        if not path.exists():
            print(f"{name}: model file not found -> {filename}")
            continue

        model = joblib.load(path)
        predictions[name] = float(model.predict(X)[0])

    return predictions


print("=" * 70)
print("TEMPERATURE REGRESSION MODEL TESTER")
print("=" * 70)

print("""
1. Test one row from testing.csv
2. Enter weather attributes manually
""")

choice = input("Choose [1]: ").strip() or "1"

if choice == "1":
    d = pd.read_csv(M / "testing.csv")

    print("\nTesting rows available:", len(d))
    i = int(input(f"Choose row (0-{len(d)-1}): "))

    row = d.iloc[[i]]
    X = row[FEATURES]

    print("\n" + "=" * 70)
    print("SELECTED TEST ROW")
    print("=" * 70)

    for column, label in [
        ("date", "Date"),
        ("prefecture", "Prefecture"),
        ("town", "Town"),
    ]:
        if column in row.columns:
            print(f"{label}: {row.iloc[0][column]}")

    print("\nInput features:")
    for feature in FEATURES:
        print(f"{feature}: {row.iloc[0][feature]}")

    actual = float(row.iloc[0]["temperature_2m_max"])

    print(f"\nActual max temperature: {actual:.2f} °C")

    print("\nPredictions:")
    print("-" * 70)

    for name, predicted in predict(X).items():
        print(name)
        print(f"  Predicted max : {predicted:.2f} °C")
        print(f"  Actual max    : {actual:.2f} °C")
        print(f"  Absolute error: {abs(predicted - actual):.2f} °C")
        print("-" * 70)

elif choice == "2":
    values = {}

    print("\nEnter input features:")
    for feature in FEATURES:
        values[feature] = float(input(f"{feature}: "))

    X = pd.DataFrame([values])

    print("\nPredictions:")
    print("-" * 70)

    for name, predicted in predict(X).items():
        print(f"{name}: {predicted:.2f} °C")

else:
    print("Invalid option.")
