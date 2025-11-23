# 做Kmeans k=5分群，並加入隨機初始化n_init=50
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from shapely.geometry import box
from matplotlib.patches import Patch

# 程式跳出的警告不影響執行
# 1. Could not find the number of physical cores = joblib 嘗試用 wmic 指令查核心數，但新版 Windows 不再預設包含這個工具
# 2. KMeans is known to have a memory leak on Windows with MKL = Windows + MKL + 多執行緒的組合下有已知記憶體洩漏

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Microsoft YaHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# === 0️⃣ 輸出資料夾 ===
output_folder = "./8_clustering_result"
os.makedirs(output_folder, exist_ok=True)

# === 1️⃣ 載入資料 ===
csv_path = "./6_exposure_by_town/PM25_weekly_exposure_with_ID.csv"
gml_path = "./TOWN_MOI_1131028.gml"

df = pd.read_csv(csv_path)

# === 2️⃣ 讀取並轉換鄉鎮邊界 ===
taiwan_map = gpd.read_file(gml_path)
taiwan_map = taiwan_map.set_crs("EPSG:3824").to_crs("EPSG:4326")
taiwan_map = taiwan_map.rename(columns={"名稱": "town"})

# 移除離島（澎湖、金門、馬祖）
main_island_bounds = box(119.9, 21.8, 122.1, 25.5)
taiwan_main = taiwan_map[taiwan_map.intersects(main_island_bounds)].copy()

# === 3️⃣ 定義顏色（由高到低） ===
# colors_hex = ["#AA04AA", "#FF0000", "#FFA500", "#FFFF00", "#23B623"]
colors_hex = ["#D62728", "#FF7F0E", "#BCBD22", "#2CA02C", "#1F77B4"]

# === 4️⃣ 逐年執行分群 ===
for year in range(2015, 2020):
    print(f"\n=== 處理 {year} 年 ===")

    df_year = df[df["year"] == year].copy()
    if df_year.empty:
        print(f"⚠️ {year} 無資料，略過。")
        continue

    # 每鄉鎮 × 每週矩陣
    df_pivot = df_year.pivot_table(index=["ID", "town"], columns="week", values="PM25")
    df_pivot = df_pivot.reindex(columns=range(1, 53))  # 確保週數一致
    df_pivot = df_pivot.fillna(df_pivot.mean(axis=1))  # 補上缺值

    # === KMeans 分群 ===
    kmeans = KMeans(n_clusters=5, n_init=50, random_state=42)
    df_pivot["cluster"] = kmeans.fit_predict(df_pivot.values)
    print(f"✅ {year} 分群完成 (k=5, n_init=50)")

    # === 計算每群平均 PM2.5 ===
    cluster_means = df_pivot.drop(columns=["cluster"]).mean(axis=1).groupby(df_pivot["cluster"]).mean().sort_values(ascending=False)
    cluster_order = cluster_means.index.tolist()  # 群組由高→低
    cluster_color_map = {cluster: colors_hex[i] for i, cluster in enumerate(cluster_order)}
    cluster_mean_map = {cluster: round(val, 2) for cluster, val in zip(cluster_order, cluster_means)}

    # === 重新編號群（高→低） ===
    new_cluster_map = {old: i+1 for i, old in enumerate(cluster_order)}
    df_pivot["cluster_ranked"] = df_pivot["cluster"].map(new_cluster_map)

    # === 輸出各群鄉鎮 ===
    for rank, group_id in enumerate(cluster_order, start=1):
        cluster_df = df_pivot[df_pivot["cluster"] == group_id].reset_index()[["ID", "town"]]
        cluster_df.to_csv(f"{output_folder}/PM25_time_group_{year}_rank{rank}.csv", index=False, encoding="utf-8-sig")

    # === 合併地理資料 ===
    df_cluster = df_pivot.reset_index()[["town", "cluster", "cluster_ranked"]]
    map_with_cluster = taiwan_main.merge(df_cluster, on="town", how="inner")

    # === 畫地圖 ===
    fig, ax = plt.subplots(figsize=(6, 9))
    taiwan_main.boundary.plot(ax=ax, color="gray", linewidth=0.3)

    for c_idx, row in map_with_cluster.iterrows():
        color = cluster_color_map[row["cluster"]]
        gpd.GeoSeries([row["geometry"]], crs="EPSG:4326").plot(ax=ax, color=color, edgecolor="black", linewidth=0.2)

    ax.set_xlim(119.9, 122.1)
    ax.set_ylim(21.8, 25.5)
    ax.set_axis_off()

    # === 標題 ===
    fig.suptitle(f"{year} 年台灣 PM2.5 時序分群 (K=5)", fontsize=14, y=0.96, ha="center")

    # === 自訂圖例 ===
    legend_elements = [
        Patch(facecolor=colors_hex[i], edgecolor='black', label=f"群組 {i+1}：平均 {cluster_means.iloc[i]:.2f}")
        for i in range(5)
    ]
    ax.legend(handles=legend_elements, title="群組（由高至低）", loc="lower left", fontsize=8)

    plt.tight_layout()
    plt.savefig(f"{output_folder}/PM25_timeseries_cluster_map_{year}.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ {year} 地圖輸出完成：PM25_timeseries_cluster_map_{year}.png")

print("\n🎯 全部年份分群與地圖繪製完成！")
