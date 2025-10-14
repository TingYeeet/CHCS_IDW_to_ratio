# 將IDW計算出的台灣空汙擴散圖，以五個大區塊做區分，屬於該區塊中的所有網格點將被平均成區塊的代表值，相當於對空間資料模糊化，消弭無法統計跨區就診的影響
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

# 測項清單
factors = ["NO", "NO2", "NOx", "O3", "PM10", "PM2.5", "SO2"]

# 定義縣市對應區域
region_map = {
    '北北基桃竹苗': ['臺北市', '新北市', '基隆市', '桃園市', '新竹市', '新竹縣', '苗栗縣'],
    '中彰投': ['臺中市', '彰化縣', '南投縣'],
    '雲嘉南': ['雲林縣', '嘉義市', '嘉義縣', '臺南市'],
    '高屏': ['高雄市', '屏東縣'],
    '宜花東': ['宜蘭縣', '花蓮縣', '臺東縣']
}

def assign_region(county):
    for region, counties in region_map.items():
        if any(c in county for c in counties):
            return region
    return '其他'

# 載入鄉鎮邊界
taiwan_map = gpd.read_file("TOWN_MOI_1131028.gml")
taiwan_map = taiwan_map.set_crs("EPSG:3824").to_crs("EPSG:4326")
taiwan_map["region"] = taiwan_map["名稱"].apply(assign_region)

# 建立 120x120 格點
iInterval = (122.7 - 119) / 120
jInterval = (25.5 - 21.8) / 120
grid_points = [Point(119 + i * iInterval, 25.5 - j * jInterval) for j in range(120) for i in range(120)]
grid_gdf = gpd.GeoDataFrame(geometry=grid_points, crs="EPSG:4326")

# 儲存結果
results = []

output_folder = "6_exposure_by_region"
os.makedirs(output_folder, exist_ok=True)

# 處理每個測項
for factor in factors:
    input_folder = f"./5_grid_output/{factor.replace('.', '')}"
    if not os.path.exists(input_folder):
        print(f"❌ 資料夾不存在: {input_folder}")
        continue

    for year in range(2016, 2020):
        for week in range(1, 53):  # 最多 53 週
            grid_path = os.path.join(input_folder, f"{factor}_{year}_week_{week}.csv")
            if not os.path.exists(grid_path):
                continue

            try:
                grid_values = pd.read_csv(grid_path, skiprows=1, header=None).values.flatten()
            except Exception as e:
                print(f"❌ 無法讀取 {grid_path}: {e}")
                continue

            if len(grid_values) != len(grid_gdf):
                print(f"⚠️ 長度不符：{grid_path} ({len(grid_values)} vs {len(grid_gdf)})")
                continue

            valid_mask = grid_values != -1
            if valid_mask.sum() == 0:
                print(f"⚠️ 全為 -1：{grid_path}")
                continue

            grid_subset = grid_gdf[valid_mask].copy()
            grid_subset["value"] = grid_values[valid_mask]

            joined = gpd.sjoin(grid_subset, taiwan_map[["geometry", "region"]], predicate='within', how='inner')
            grouped = joined.groupby('region')

            for region, group in grouped:
                avg_val = group["value"].mean() * 7  # 週暴露量 = 每日平均 * 7
                results.append({
                    "region": region,
                    "year": year,
                    "week": week,
                    "value": round(avg_val, 2)
                })

            print(f"✅ 完成：{factor} {year} week {week}")

    # 輸出結果
    if results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(f"./{output_folder}/{factor}_weekly_exposure_by_region.csv", index=False, encoding="utf-8-sig")
        print(f"✅ 輸出完成：{factor}_weekly_exposure_by_region.csv")
    else:
        print("⚠️ 無任何有效結果輸出")
