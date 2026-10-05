from pathlib import Path
import pandas as pd, joblib
R=Path(__file__).resolve().parent; M=R/"trained_models"
F=["temperature_2m_max","temperature_2m_min","relative_humidity_2m_mean","dew_point_2m_mean","cloud_cover_mean","pressure_msl_mean","wind_speed_10m_max","shortwave_radiation_sum","month"]
models={"1":("Gradient Boosting","gradient_boosting.joblib"),"2":("Random Forest","random_forest.joblib"),"3":("CART","cart.joblib"),"4":("SVM","svm.joblib")}
print("RAIN CLASSIFICATION MODEL TEST")
for k,v in models.items(): print(k,v[0])
k=input("Model [1]: ").strip() or "1"; name,file=models.get(k,models["1"]); model=joblib.load(M/file)
mode=input("1=manual, 2=testing.csv row [2]: ").strip() or "2"
if mode=="1":
 X=pd.DataFrame([{f:float(input(f+" : ")) for f in F}]); actual=None
else:
 d=pd.read_csv(M/"testing.csv"); i=int(input(f"Row 0-{len(d)-1}: ")); actual=d.iloc[i]; X=pd.DataFrame([actual[F].to_dict()])
pred=model.predict(X)[0]; print("\nModel:",name,"\nPrediction:",pred)
if hasattr(model,"predict_proba"):
 for c,p in sorted(zip(model.classes_,model.predict_proba(X)[0]),key=lambda x:x[1],reverse=True): print(f"{c}: {p:.2%}")
if actual is not None: print("Actual rain:",actual.get("rain_sum"),"mm\nActual class:",actual.get("rain_class"),"\nResult:","CORRECT" if pred==actual.get("rain_class") else "INCORRECT")
