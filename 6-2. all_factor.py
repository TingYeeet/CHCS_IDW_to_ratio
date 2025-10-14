# 將6. inverse_weight2cluster.py的結果整合成單一csv檔
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

# 測項清單
factors = ["NO", "NO2", "NOx", "O3", "PM10", "PM25", "SO2"]

# 縣市與區域對照
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

# 儲存所有結果（主鍵為 region, year, week）
all_results = {}

# 處理每個測項
for factor in factors:
    input_folder = f"./5_grid_output/{factor}"
    if not os.path.exists(input_folder):
        print(f"❌ 資料夾不存在: {input_folder}")
        continue

    for year in range(2016, 2020):
        for week in range(1, 53):
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
                key = (region, year, week)
                avg_val = round(group["value"].mean() * 7, 2)  # 週暴露量
                if key not in all_results:
                    all_results[key] = {}
                all_results[key][factor] = avg_val

            print(f"✅ 完成：{factor} {year} week {week}")

# 組裝 DataFrame
records = []
for (region, year, week), values in all_results.items():
    record = {"region": region, "year": year, "week": week}
    for factor in factors:
        record[factor] = values.get(factor, None)
    records.append(record)

# 輸出
result_df = pd.DataFrame(records)
result_df = result_df.sort_values(by=["region", "year", "week"])
result_df.to_csv("./6_exposure_by_region/factors_weekly_exposure.csv", index=False, encoding="utf-8-sig")
print("✅ 最終輸出完成：factors_weekly_exposure.csv")
