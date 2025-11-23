import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from shapely.geometry import box
from matplotlib.patches import Patch

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Microsoft YaHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# === 0️⃣ 輸出資料夾 ===
output_folder = "./8-3_clustering_result_5year_mean"
os.makedirs(output_folder, exist_ok=True)

# === 1️⃣ 🚀 改成讀取五年平均檔案 ===
csv_path = "./6_exposure_by_town/PM25_5year_mean.csv"   # <── 改這裡
gml_path = "./TOWN_MOI_1131028.gml"

df = pd.read_csv(csv_path)

# === 2️⃣ 讀取鄉鎮邊界 ===
taiwan_map = gpd.read_file(gml_path)
taiwan_map = taiwan_map.set_crs("EPSG:3824").to_crs("EPSG:4326")
taiwan_map = taiwan_map.rename(columns={"名稱": "town"})

# 移除離島
main_island_bounds = box(119.9, 21.8, 122.1, 25.5)
taiwan_main = taiwan_map[taiwan_map.intersects(main_island_bounds)].copy()

# === 3️⃣ 定義顏色（由高到低） ===
colors_hex = ["#AA04AA", "#FF0000", "#FFA500", "#FFFF00", "#23B623"]

# === 4️⃣ 🚀 建立「ID × week」矩陣（不分年） ===
df_pivot = df.pivot_table(index=["ID", "town"], columns="week", values="PM25")
df_pivot = df_pivot.reindex(columns=range(1, 53))
df_pivot = df_pivot.fillna(df_pivot.mean(axis=1))

# === 5️⃣ KMeans 分群（一次而已） ===
kmeans = KMeans(n_clusters=5, n_init=50, random_state=42)
df_pivot["cluster"] = kmeans.fit_predict(df_pivot.values)
print("✅ 五年平均 PM2.5 分群完成 (k=5, n_init=50)")

# === 6️⃣ 計算群平均並重新編號 ===
cluster_means = df_pivot.drop(columns=["cluster"]).mean(axis=1).groupby(df_pivot["cluster"]).mean().sort_values(ascending=False)
cluster_order = cluster_means.index.tolist()
cluster_color_map = {cluster: colors_hex[i] for i, cluster in enumerate(cluster_order)}

new_cluster_map = {old: i + 1 for i, old in enumerate(cluster_order)}
df_pivot["cluster_ranked"] = df_pivot["cluster"].map(new_cluster_map)

# === 7️⃣ 輸出每群的鄉鎮名單 ===
for rank, group_id in enumerate(cluster_order, start=1):
    cluster_df = df_pivot[df_pivot["cluster"] == group_id].reset_index()[["ID", "town"]]
    cluster_df.to_csv(f"{output_folder}/PM25_mean_group_rank{rank}.csv", index=False, encoding="utf-8-sig")

# === 8️⃣ 畫地圖 ===
df_cluster = df_pivot.reset_index()[["town", "cluster", "cluster_ranked"]]
map_with_cluster = taiwan_main.merge(df_cluster, on="town", how="inner")

fig, ax = plt.subplots(figsize=(6, 9))
taiwan_main.boundary.plot(ax=ax, color="gray", linewidth=0.3)

for _, row in map_with_cluster.iterrows():
    color = cluster_color_map[row["cluster"]]
    gpd.GeoSeries([row["geometry"]], crs="EPSG:4326").plot(ax=ax, color=color, edgecolor="black", linewidth=0.2)

ax.set_xlim(119.9, 122.1)
ax.set_ylim(21.8, 25.5)
ax.set_axis_off()

fig.suptitle("2015–2019 五年平均 PM2.5 時序分群 (K=5)", fontsize=14, y=0.96, ha="center")

legend_elements = [
    Patch(facecolor=colors_hex[i], edgecolor='black', label=f"群組 {i+1}：平均 {cluster_means.iloc[i]:.2f}")
    for i in range(5)
]
ax.legend(handles=legend_elements, title="群組（由高至低）", loc="lower left", fontsize=8)

plt.tight_layout()
plt.savefig(f"{output_folder}/PM25_5year_mean_cluster_map.png", dpi=300, bbox_inches="tight")
plt.close()

print("🎯 五年平均 PM2.5 分群與地圖繪製完成！")
