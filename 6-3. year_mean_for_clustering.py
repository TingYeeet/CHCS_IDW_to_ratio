import os
import pandas as pd

# === 1️⃣ 檔案路徑設定 ===
input_path = "./6_exposure_by_town/PM25_weekly_exposure_with_ID.csv"
output_path = "./6_exposure_by_town/PM25_5year_mean.csv"

# === 2️⃣ 讀取資料 ===
df = pd.read_csv(input_path, dtype={"ID": str})

# === 3️⃣ 移除空值（若有） ===
df = df.dropna(subset=["PM25"])

# === 4️⃣ 依據 ID 和 week 計算多年平均（不需所有年份都存在） ===
df_mean = (
    df.groupby(["ID", "week"], as_index=False)
    .agg({
        "town": lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0],  # 保留最常見或第一筆 town 名稱
        "PM25": "mean"
    })
    .round({"PM25": 2})
)

# === 5️⃣ 輸出 ===
df_mean.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"✅ 已輸出：{output_path}")
print(f"共 {len(df_mean)} 筆資料")
