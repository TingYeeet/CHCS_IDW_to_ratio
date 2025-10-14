# 繪製2016年第45周的PM2.5暴露情況做確認
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Microsoft YaHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# === 1️⃣ 讀取資料 ===
csv_path = "./6_exposure_by_town/PM25_weekly_exposure_with_ID.csv"
gml_path = "./TOWN_MOI_1131028.gml"

df = pd.read_csv(csv_path)
df_2016w45 = df[(df["year"] == 2016) & (df["week"] == 45) & (df["PM25"].notna())]
print(f"共有 {len(df_2016w45)} 個鄉鎮有有效資料")

# === 2️⃣ 讀取鄉鎮邊界 ===
taiwan_map = gpd.read_file(gml_path)
taiwan_map = taiwan_map.set_crs("EPSG:3824").to_crs("EPSG:4326")
taiwan_map = taiwan_map.rename(columns={"名稱": "town"})

# === 3️⃣ 只保留台灣本島 ===
# 定義台灣主島的經緯度邊界（排除澎湖、金門、馬祖）
main_island_bounds = box(119.9, 21.8, 122.1, 25.5)
taiwan_main = taiwan_map[taiwan_map.intersects(main_island_bounds)].copy()

# === 4️⃣ 合併空間資料 ===
map_with_data = taiwan_main.merge(df_2016w45, on="town", how="inner")

# === 5️⃣ 畫地圖 ===
fig, ax = plt.subplots(figsize=(6, 9))

# 底圖邊界
taiwan_main.boundary.plot(ax=ax, linewidth=0.3, color="lightgray")

# 資料圖層
map_with_data.plot(
    column="PM25",
    ax=ax,
    legend=True,
    cmap="OrRd",
    linewidth=0.2,
    edgecolor="black",
    legend_kwds={
        "label": "PM2.5 (μg/m³)",
        "orientation": "vertical",
        "shrink": 0.6,
        "pad": 0.02
    }
)

# === 6️⃣ 美化 ===
ax.set_xlim(119.9, 122.1)
ax.set_ylim(21.8, 25.5)
ax.set_axis_off()

# 標題置中
fig.suptitle("2016 年第 45 週 台灣本島鄉鎮 PM2.5 暴露量", fontsize=14, y=0.95, ha="center")

plt.tight_layout()

# === 7️⃣ 儲存圖片 ===
plt.savefig("./6_exposure_by_town/PM25_2016-45.png", dpi=300, bbox_inches="tight")
