# 將手動修改的分結果整合成cluster-ID的單一檔案
import os
import pandas as pd

# 手動分群資料夾
manual_folder = "./8_clustering_result"

# 五個分群檔案
cluster_files = [f"PM25_time_group_2019_rank{i}.csv" for i in range(1, 6)]

# 顏色或群編號由高→低，rank 1 對應 cluster 1
cluster_list = []
for rank, file in enumerate(cluster_files, start=1):
    df = pd.read_csv(os.path.join(manual_folder, file))
    df_cluster = df[["ID"]].copy()
    df_cluster["cluster"] = rank
    cluster_list.append(df_cluster)

# 合併所有群
df_all_cluster = pd.concat(cluster_list, ignore_index=True)

# 去除重複（萬一 ID 出現多次）
df_all_cluster = df_all_cluster.drop_duplicates(subset=["ID"])

# 輸出
output_path = os.path.join(manual_folder, "PM25_cluster_2019.csv")
df_all_cluster.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"✅ 手動分群整合完成，輸出檔案：{output_path}")
