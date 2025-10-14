# 偵測缺值，並把缺值情況統計結果輸出成missing_values_summary.csv，供內插法補值前後使用
import os
import pandas as pd

# 輸出資料夾路徑（你之前處理好的結果）
input_dir = "3_interpolated_output"

# 儲存缺值紀錄的清單
missing_records = []

# 遞迴走訪每個輸出的 CSV 檔案
for dirpath, dirnames, filenames in os.walk(input_dir):
    for filename in filenames:
        if filename.endswith(".csv"):
            file_path = os.path.join(dirpath, filename)
            try:
                df = pd.read_csv(file_path, encoding="utf-8-sig")

                # 找出每個欄位為 NaN 的位置
                for row_idx, row in df.iterrows():
                    for col in df.columns:
                        if pd.isna(row[col]):
                            missing_records.append({
                                "日期": row["日期"] if "日期" in row else None,
                                "地區": row["地區"] if "地區" in row else None,
                                "測項": col,
                            })

            except Exception as e:
                print(f"❌ 無法讀取 {file_path}，錯誤原因：{e}")

# 組成 DataFrame 並匯出
if missing_records:
    missing_df = pd.DataFrame(missing_records)
    output_path = os.path.join(input_dir, "missing_values_summary.csv")
    missing_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 缺值紀錄已儲存：{output_path}")
else:
    print("✅ 所有檔案中皆無缺值。")
