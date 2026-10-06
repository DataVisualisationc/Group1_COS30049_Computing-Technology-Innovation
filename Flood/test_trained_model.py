from pathlib import Path
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "trained_models"
TEST_FILE = MODEL_DIR / "testing.csv"

MODEL_FILES = {
    "CART": "cart_flood.joblib",
    "Gradient Boosting": "gradient_boosting_flood.joblib",
    "ID3-style Entropy Tree": "id3_flood.joblib",
}

models = {name: joblib.load(MODEL_DIR / fn) for name, fn in MODEL_FILES.items()}

def expected_features(model):
    if hasattr(model, "feature_names_in_"):
        return list(model.feature_names_in_)
    raise AttributeError("Saved model does not contain feature_names_in_.")

FEATURES = expected_features(next(iter(models.values())))

def predict_row(row):
    missing = [c for c in FEATURES if c not in row.index]
    if missing:
        raise KeyError(f"Missing model features: {missing}")

    X = row.to_frame().T[FEATURES]
    for c in FEATURES:
        X[c] = pd.to_numeric(X[c], errors="coerce")

    if X.isna().any().any():
        bad = X.columns[X.isna().any()].tolist()
        raise ValueError(f"Missing/non-numeric values in: {bad}")

    print("\n" + "="*70)
    for name, model in models.items():
        pred = model.predict(X)[0]
        print(f"{name}: {pred}")

        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)[0]
            print(" Probabilities:")
            for cls, p in zip(model.classes_, probs):
                print(f"   {cls}: {p:.4f}")

def test_csv_row():
    df = pd.read_csv(TEST_FILE)
    print(f"\nTesting rows available: {len(df)}")
    idx = int(input(f"Choose row index (0-{len(df)-1}): "))
    row = df.iloc[idx]

    for c in ["date","prefecture","town","flood_class"]:
        if c in row.index:
            print(f"{c}: {row[c]}")

    print("\nModel inputs:")
    for c in FEATURES:
        print(f"{c}: {row[c]}")

    if "flood_class" in row.index:
        actual = row["flood_class"]
        print("\nActual:", actual)

    predict_row(row)

def manual():
    values = {}
    print("\nEnter the flood-condition attributes:")
    for c in FEATURES:
        values[c] = float(input(f"{c}: "))
    predict_row(pd.Series(values))

print("="*70)
print("FLOOD MODEL TESTER")
print("="*70)
print("1. Test one row from testing.csv")
print("2. Enter attributes manually")

choice = input("\nChoose option: ").strip()

if choice == "1":
    test_csv_row()
elif choice == "2":
    manual()
else:
    print("Invalid option.")
