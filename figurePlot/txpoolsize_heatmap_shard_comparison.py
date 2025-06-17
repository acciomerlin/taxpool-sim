import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# 定义分片数
# shard_counts = [4, 8, 16, 32]
shard_counts = [4]

# 创建一个 32×4 的矩阵用于存储数据（未使用的部分填 NaN 显示为空白）
# heatmap_data = np.full((32, len(shard_counts)), np.nan)
heatmap_data = np.full((4, len(shard_counts)), np.nan)

# 遍历不同分片数
for col_idx, shard_count in enumerate(shard_counts):
    for shard_id in range(shard_count):
        file_path = f"expTest_f1000k_{shard_count}s4n_stop/result/pbft_shardNum={shard_count}/Shard{shard_id}{shard_count}.csv"
        try:
            df = pd.read_csv(file_path)
            heatmap_data[shard_id, col_idx] = df["TxPool Size"].sum()
        except FileNotFoundError:
            print(f"Warning: {file_path} not found, skipping.")

# 创建热力图
plt.figure(figsize=(8, 10), dpi=300)
sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="YlGnBu", linewidths=0.5, cbar=True)

# 设置坐标轴
plt.xticks(ticks=np.arange(len(shard_counts)) + 0.5, labels=shard_counts, fontsize=12)
plt.yticks(ticks=np.arange(32) + 0.5, labels=np.arange(32), fontsize=10)
plt.xlabel("Shard Count", fontsize=14)
plt.ylabel("Shard Index", fontsize=14)
plt.title("Transaction Pool Size Heatmap", fontsize=16)

# 保存图像
plt.savefig("txpoolsize_heatmap32.png", dpi=300, bbox_inches='tight', format='png')

# 显示图像
# plt.show()
