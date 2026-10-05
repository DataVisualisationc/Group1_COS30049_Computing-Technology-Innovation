from pathlib import Path
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "trained_models"

FEATURES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
    "dew_point_2m_mean",
    "cloud_cover_mean",
    "pressure_msl_mean",
    "wind_speed_10m_max",
    "shortwave_radiation_sum",
    "month",
]

TARGET = "rain_class"

MODEL_FILES = {
    "Gradient Boosting": "gradient_boosting.joblib",
    "Random Forest": "random_forest.joblib",
    "CART": "cart.joblib",
    "SVM": "svm.joblib",
}


def load_testing_data():
    path = MODEL_DIR / "testing.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found.\n"
            "Train the Rain models first so testing.csv is created."
        )

    df = pd.read_csv(path)

    required = FEATURES + [TARGET]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise KeyError(f"testing.csv is missing columns: {missing}")

    return df


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

    actual_class = str(sample.iloc[0][TARGET])
    actual_rain = sample.iloc[0].get("rain_sum", None)

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

    if actual_rain is not None and pd.notna(actual_rain):
        print(f"\nActual rain: {float(actual_rain):.2f} mm")

    print("Actual class:", actual_class)

    print("\nPredictions:")
    print("-" * 70)

    for name, filename in MODEL_FILES.items():
        path = MODEL_DIR / filename

        if not path.exists():
            print(f"{name}: model file not found")
            continue

        model = joblib.load(path)
        predicted = str(model.predict(X)[0])
        result = "CORRECT" if predicted == actual_class else "INCORRECT"

        print(
            f"{name}\n"
            f"  Predicted : {predicted}\n"
            f"  Actual    : {actual_class}\n"
            f"  Result    : {result}"
        )

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X)[0]
            ranked = sorted(
                zip(model.classes_, probabilities),
                key=lambda x: x[1],
                reverse=True,
            )

            print("  Probabilities:")
            for cls, probability in ranked:
                print(f"    {cls}: {probability:.2%}")


def manual_prediction():
    print("\nEnter Rain input attributes:")

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
        predicted = str(model.predict(X)[0])

        print(f"{name}: {predicted}")

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X)[0]
            ranked = sorted(
                zip(model.classes_, probabilities),
                key=lambda x: x[1],
                reverse=True,
            )

            for cls, probability in ranked:
                print(f"  {cls}: {probability:.2%}")


def main():
    print("=" * 70)
    print("RAIN CLASSIFICATION MODEL TESTER")
    print("=" * 70)

    print("\n1. Test one row from testing.csv")
    print("2. Enter weather attributes manually")

    choice = input("\nChoose [1]: ").strip() or "1"

    if choice == "1":
        test = load_testing_data()
        test_single_row(test)

    elif choice == "2":
        manual_prediction()

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
