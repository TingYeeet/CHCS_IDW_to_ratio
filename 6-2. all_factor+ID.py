# 將IDW計算出的台灣空汙擴散圖整合成鄉鎮週暴露量（含ID欄位）
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

# 測項清單
factors = ["NO", "NO2", "NOx", "O3", "PM10", "PM25", "SO2"]

# === 1️⃣ 載入鄉鎮邊界（名稱欄位） ===
gml_path = "TOWN_MOI_1131028.gml"
taiwan_map = gpd.read_file(gml_path)
taiwan_map = taiwan_map.set_crs("EPSG:3824").to_crs("EPSG:4326")
taiwan_map = taiwan_map.rename(columns={"名稱": "town"})

# === 2️⃣ 載入鄉鎮對應ID ===
id_map = pd.read_csv("ID_CNAME.csv", dtype=str)
id_map = id_map.rename(columns={"ID1_CITY": "ID", "C_NAME": "town"})

# === 3️⃣ 建立 120x120 格點 ===
iInterval = (122.7 - 119) / 120
jInterval = (25.5 - 21.8) / 120
grid_points = [Point(119 + i * iInterval, 25.5 - j * jInterval) for j in range(120) for i in range(120)]
grid_gdf = gpd.GeoDataFrame(geometry=grid_points, crs="EPSG:4326")

# === 4️⃣ 儲存所有結果（主鍵為 town, year, week） ===
all_results = {}

# === 5️⃣ 處理每個測項 ===
for factor in factors:
    input_folder = f"./5_grid_output/{factor}"
    if not os.path.exists(input_folder):
        print(f"❌ 資料夾不存在: {input_folder}")
        continue

    for year in range(2015, 2020):
        for week in range(1, 52):
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

            # 空間連接：格點 → 鄉鎮
            joined = gpd.sjoin(grid_subset, taiwan_map[["geometry", "town"]], predicate='within', how='inner')

            # 計算每個鄉鎮覆蓋比例（以格點面積近似）
            grouped = joined.groupby('town')

            for town, group in grouped:
                # 該鄉鎮的邊界
                town_poly = taiwan_map.loc[taiwan_map["town"] == town, "geometry"].values[0]

                # 計算鄉鎮面積（使用 EPSG:3826 比較準）
                town_area = gpd.GeoSeries([town_poly], crs="EPSG:4326").to_crs(epsg=3826).area.values[0]

                # 該鄉鎮內格點代表的覆蓋面積
                # 每個格點代表的面積（以經緯度間隔近似）
                grid_area = (iInterval * jInterval) * (111000 ** 2)  # 約略換算平方公尺
                covered_area = len(group) * grid_area

                # 若覆蓋不到該鄉鎮面積的一半 → 略過
                if covered_area < 0.5 * town_area:
                    print(f"⚠️ {town} 覆蓋不足（覆蓋比例={covered_area / town_area:.2%}），略過。")
                    continue

                # 計算週暴露量（7天平均）
                avg_val = round(group["value"].mean(), 2)
                key = (town, year, week)
                if key not in all_results:
                    all_results[key] = {}
                all_results[key][factor] = avg_val

            print(f"✅ 完成：{factor} {year} week {week}")

# === 6️⃣ 組裝整合表 ===
records = []
for (town, year, week), values in all_results.items():
    record = {"town": town, "year": year, "week": week}
    for factor in factors:
        record[factor] = values.get(factor, None)
    records.append(record)

result_df = pd.DataFrame(records)

# === 7️⃣ 合併ID對照 ===
result_df = result_df.merge(id_map, on="town", how="left")

# 將 ID 欄位移到第一欄
cols = ["ID"] + [c for c in result_df.columns if c != "ID"]
result_df = result_df[cols]

# 警告：有未對應的鄉鎮
missing_ids = result_df[result_df["ID"].isna()]["town"].unique()
if len(missing_ids) > 0:
    print("⚠️ 下列鄉鎮無法在 ID_CNAME.csv 中找到對應：")
    for name in missing_ids:
        print("  -", name)

# === 8️⃣ 輸出結果 ===
output_folder = "./6_exposure_by_town"
os.makedirs(output_folder, exist_ok=True)

result_df = result_df.sort_values(by=["ID", "year", "week"])
result_df.to_csv(f"{output_folder}/factors_weekly_exposure_with_ID.csv", index=False, encoding="utf-8-sig")

print("✅ 最終輸出完成：6_exposure_by_town/factors_weekly_exposure_with_ID.csv")
