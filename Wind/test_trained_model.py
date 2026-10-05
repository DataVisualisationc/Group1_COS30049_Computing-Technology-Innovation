from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "trained_models"

FEATURES = [
    "surface_pressure_mean",
    "surface_pressure_max",
    "surface_pressure_min",
    "pressure_change",
    "wind_direction_10m_dominant",
]

TARGET = "wind_speed_10m_max"

MODEL_FILES = {
    "Multiple Linear Regression": "multiple_linear_regression.joblib",
    "Gradient Boosting": "gradient_boosting.joblib",
    "HistGradientBoosting": "hist_gradient_boosting.joblib",
}


def load_testing_data():
    path = MODEL_DIR / "testing.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found.\n"
            "Run train_wind_models_split.ipynb first."
        )

    df = pd.read_csv(path)

    required = FEATURES + [TARGET]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise KeyError(f"testing.csv is missing columns: {missing}")

    return df


def evaluate_all_models(test):
    X_test = test[FEATURES]
    y_test = test[TARGET]

    results = []

    print("\n" + "=" * 70)
    print("FULL 2026 TEST SET EVALUATION")
    print("=" * 70)

    for name, filename in MODEL_FILES.items():
        path = MODEL_DIR / filename

        if not path.exists():
            print(f"SKIP {name}: {filename} not found")
            continue

        model = joblib.load(path)
        pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, pred)
        rmse = np.sqrt(mean_squared_error(y_test, pred))
        r2 = r2_score(y_test, pred)

        results.append({
            "Model": name,
            "MAE (km/h)": mae,
            "RMSE (km/h)": rmse,
            "R2": r2,
        })

    if not results:
        print("No trained models were found.")
        return

    results_df = pd.DataFrame(results).sort_values("RMSE (km/h)")

    print()
    print(results_df.to_string(index=False))

    best = results_df.iloc[0]

    print("\nBest model by RMSE:")
    print(best["Model"])
    print(f'RMSE: {best["RMSE (km/h)"]:.4f} km/h')


def test_single_row(test):
    print("\nTesting rows available:", len(test))

    while True:
        try:
            row = int(input(f"Choose row (0-{len(test)-1}): "))

            if 0 <= row < len(test):
                break

            print("Row is outside the valid range.")

        except ValueError:
            print("Please enter an integer.")

    sample = test.iloc[[row]]
    X = sample[FEATURES]
    actual = float(sample.iloc[0][TARGET])

    print("\n" + "=" * 70)
    print("SELECTED TEST ROW")
    print("=" * 70)

    if "date" in sample.columns:
        print("Date:", sample.iloc[0]["date"])

    if "prefecture" in sample.columns:
        print("Prefecture:", sample.iloc[0]["prefecture"])

    if "town" in sample.columns:
        print("Town:", sample.iloc[0]["town"])

    print("\nInput features:")
    for feature in FEATURES:
        print(f"{feature}: {sample.iloc[0][feature]}")

    print(f"\nActual wind speed: {actual:.2f} km/h")

    print("\nPredictions:")
    print("-" * 70)

    for name, filename in MODEL_FILES.items():
        path = MODEL_DIR / filename

        if not path.exists():
            print(f"{name}: model file not found")
            continue

        model = joblib.load(path)
        predicted = float(model.predict(X)[0])
        error = abs(predicted - actual)

        print(
            f"{name}\n"
            f"  Predicted : {predicted:.2f} km/h\n"
            f"  Actual    : {actual:.2f} km/h\n"
            f"  Abs Error : {error:.2f} km/h"
        )


def manual_prediction():
    print("\nEnter Wind input attributes:")

    values = {}

    for feature in FEATURES:
        while True:
            try:
                values[feature] = float(input(f"{feature}: "))
                break
            except ValueError:
                print("Please enter a numeric value.")

    X = pd.DataFrame([values])

    print("\nPredictions:")
    print("-" * 70)

    for name, filename in MODEL_FILES.items():
        path = MODEL_DIR / filename

        if not path.exists():
            print(f"{name}: model file not found")
            continue

        model = joblib.load(path)
        predicted = float(model.predict(X)[0])

        print(f"{name}: {predicted:.2f} km/h")


def main():
    print("=" * 70)
    print("WIND REGRESSION MODEL TESTER")
    print("=" * 70)

    print("\n1. Evaluate all models using the full 2026 testing dataset")
    print("2. Test one row from testing.csv")
    print("3. Enter weather attributes manually")

    choice = input("\nChoose [1]: ").strip() or "1"

    if choice == "1":
        test = load_testing_data()
        evaluate_all_models(test)

    elif choice == "2":
        test = load_testing_data()
        test_single_row(test)

    elif choice == "3":
        manual_prediction()

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
