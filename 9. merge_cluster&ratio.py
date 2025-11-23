# 把就診比例資料(周就診轉比例)和空汙資料(6_exposure_by_town)合併
# 然後使用PM25_manual_cluster_2019.csv把就診比例資料換算成以大區域為單位的
import os
import pandas as pd
from functools import reduce

# === 1️⃣ 檔案路徑設定 ===
disease_folder = "./周就醫轉比例"
exposure_folder = "./6_exposure_by_town"
cluster_path = "./8_clustering_result/PM25_cluster_2019.csv"
output_folder = "./9_disease_with_exposure"
os.makedirs(output_folder, exist_ok=True)

# === 2️⃣ 讀取手動分群結果 ===
df_cluster = pd.read_csv(cluster_path)
df_cluster["ID"] = df_cluster["ID"].astype(str)

cluster_name_map = {
    1: "高屏",
    2: "雲嘉南",
    3: "苗中彰投",
    4: "北北基桃竹",
    5: "宜花東"
}

# === 3️⃣ 自動讀取並合併所有污染物檔案 ===
pollutant_dfs = []
for file in os.listdir(exposure_folder):
    if not file.endswith("_weekly_exposure_with_ID.csv"):
        continue

    pollutant_name = file.split("_")[0]  # 取 "NO"、"NO2"、"PM25" 等
    df = pd.read_csv(os.path.join(exposure_folder, file))
    df["ID"] = df["ID"].astype(str)
    df = df.rename(columns={pollutant_name: pollutant_name.upper()})
    pollutant_dfs.append(df[["ID", "year", "week", pollutant_name.upper()]])

# 合併成一張總表
df_expo = reduce(lambda left, right: pd.merge(left, right, on=["ID", "year", "week"], how="outer"), pollutant_dfs)

# 合併 cluster
df_expo = df_expo.merge(df_cluster, on="ID", how="left")

# === 4️⃣ 依群、年、週計算平均 ===
pollutants = [c for c in df_expo.columns if c in ["NO", "NO2", "NOX", "O3", "PM10", "PM25", "SO2"]]

df_expo_grouped = (
    df_expo.groupby(["year", "week", "cluster"], as_index=False)[pollutants]
    .mean()
)
df_expo_grouped[pollutants] = df_expo_grouped[pollutants].round(2)
df_expo_grouped["region"] = df_expo_grouped["cluster"].map(cluster_name_map)

print("✅ 空污群平均計算完成，共", len(df_expo_grouped), "筆")

# === 5️⃣ 整合疾病資料 ===
for file in os.listdir(disease_folder):
    if not file.endswith("_filtered.csv"):
        continue

    disease_name = file.replace("_filtered.csv", "")
    print(f"\n=== 處理疾病：{disease_name} ===")

    df_disease = pd.read_csv(os.path.join(disease_folder, file))
    df_disease["ID"] = df_disease["ID1_CITY"].astype(str)

    # 合併 cluster
    df_disease = df_disease.merge(df_cluster, on="ID", how="left")

    # 依群集、年、週加總病例與人口數
    df_disease_grouped = (
        df_disease.groupby(["year", "week", "cluster"], as_index=False)
        .agg({
            "case_c": "sum",
            "pop_total": "sum"
        })
    )
    # 重新計算每千人就診率
    df_disease_grouped["case_per_capita(‰)"] = (
        df_disease_grouped["case_c"] / df_disease_grouped["pop_total"] * 1000
    ).round(2)

    # 合併空污群平均
    merged = pd.merge(
        df_disease_grouped,
        df_expo_grouped,
        on=["year", "week", "cluster"],
        how="left"
    )

    # === 檢查特定週缺漏情況（可移除或註解） ===
    print("\n🔍 檢查宜花東 2016 week 1")
    print("=== 疾病資料 ===")
    print(df_disease_grouped.query("cluster == 5 and year == 2016 and week == 1"))

    print("=== 空汙資料 ===")
    print(df_expo_grouped.query("cluster == 5 and year == 2016 and week == 1"))

    print("=== 合併後 ===")
    print(merged.query("cluster == 5 and year == 2016 and week == 1"))

    # 保留需要的欄位
    merged = merged[[
        "region", "year", "week",
        "case_c", "pop_total", "case_per_capita(‰)",
        *pollutants
    ]]

    # 移除第 53 週（可選）
    merged = merged[merged["week"] != 53]

    # 依地區排序
    merged = merged.sort_values(by=["region", "year", "week"])

    # 輸出
    output_path = os.path.join(output_folder, f"{disease_name}.csv")
    merged.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 已輸出：{output_path}，共 {len(merged)} 筆")

print("\n🎯 所有疾病與空污資料整合完成！")
