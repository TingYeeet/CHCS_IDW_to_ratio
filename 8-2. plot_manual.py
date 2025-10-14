# 因8. Kmeans k=5.py的結果再分群有不合理之處，故將分群結果基於2019年的結果手動修改並繪製分群地圖
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box
from matplotlib.patches import Patch

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Microsoft YaHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# 輸出資料夾
output_folder = "./8_clustering_result/cluster_manual_based_on_2019"
os.makedirs(output_folder, exist_ok=True)

# 顏色設定（高→低）
colors_hex = ["#AA04AA", "#FF0000", "#FFA500", "#FFFF00", "#23B623"]

# 讀取鄉鎮邊界
gml_path = "./TOWN_MOI_1131028.gml"
taiwan_map = gpd.read_file(gml_path)
taiwan_map = taiwan_map.set_crs("EPSG:3824").to_crs("EPSG:4326")
taiwan_map = taiwan_map.rename(columns={"名稱": "town"})

# 移除離島（澎湖、金門、馬祖）
main_island_bounds = box(119.9, 21.8, 122.1, 25.5)
taiwan_main = taiwan_map[taiwan_map.intersects(main_island_bounds)].copy()

# === 讀取手動分群結果 ===
manual_folder = "./8_clustering_result/cluster_manual_based_on_2019"
cluster_files = [f"PM25_time_group_2019_rank{i}.csv" for i in range(1, 6)]

cluster_list = []
for rank, file in enumerate(cluster_files, start=1):
    df = pd.read_csv(os.path.join(manual_folder, file))
    df["cluster_ranked"] = rank  # 高到低
    cluster_list.append(df)

df_cluster_manual = pd.concat(cluster_list, ignore_index=True)

# 合併地理資料
map_with_cluster = taiwan_main.merge(df_cluster_manual, on="town", how="inner")

# 畫地圖
fig, ax = plt.subplots(figsize=(6, 9))
taiwan_main.boundary.plot(ax=ax, color="gray", linewidth=0.3)

# 填色
for _, row in map_with_cluster.iterrows():
    color = colors_hex[row["cluster_ranked"] - 1]  # rank 1→colors_hex[0]
    gpd.GeoSeries([row["geometry"]], crs="EPSG:4326").plot(ax=ax, color=color, edgecolor="black", linewidth=0.2)

ax.set_xlim(119.9, 122.1)
ax.set_ylim(21.8, 25.5)
ax.set_axis_off()
fig.suptitle("基於2019年資料的 PM2.5 手動分群地圖 (K=5)", fontsize=14, y=0.96, ha="center")

# 自訂圖例
legend_elements = [
    Patch(facecolor=colors_hex[i], edgecolor='black', label=f"群組 {i+1}")
    for i in range(5)
]
ax.legend(handles=legend_elements, title="群組（高→低）", loc="lower left", fontsize=8)

plt.tight_layout()
plt.savefig(f"{output_folder}/PM25_manual_cluster_map_2019.png", dpi=300, bbox_inches="tight")
plt.close()
print("✅ 2019 手動分群地圖輸出完成：PM25_manual_cluster_map_2019.png")
