import os

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

def generate_txpool_heatmap(method: int, csv_source: str, shard_num: int, save_directory: str):
    """
    生成交易池大小的热力图。
    :param method: 选择方法（0-3）。method=0,2 时使用 broker。
    :param csv_source: CSV 文件来源路径。
    :param shard_num: 分片总数。
    :param save_directory: 图像保存路径。
    """
    all_blocks = []
    shard_dfs = {}

    for shard_id in range(shard_num):
        file_path = f"{csv_source}/Shard{shard_id}{shard_num}.csv"
        try:
            df = pd.read_csv(file_path)
            shard_dfs[shard_id] = df
            all_blocks.extend(df["Block Height"].tolist())  # 收集所有区块编号
        except FileNotFoundError:
            print(f"Warning: {file_path} not found, skipping.")

    unique_blocks = sorted(set(all_blocks))
    heatmap_data = np.full((shard_num, len(unique_blocks)), np.nan)

    for shard_id, df in shard_dfs.items():
        for i, block_num in enumerate(unique_blocks):
            block_data = df[df["Block Height"] == block_num]
            if not block_data.empty:
                heatmap_data[shard_id, i] = block_data["TxPool Size"].sum()  # 计算该区块内的交易池大小

    plt.figure(figsize=(12, 6), dpi=300)
    # sns.heatmap(heatmap_data, annot=False, cmap="YlGnBu", linewidths=0.5, cbar=True)
    sns.heatmap(heatmap_data, annot=False, cmap="RdBu_r", linewidths=0, cbar=True)


    plt.xticks(ticks=np.arange(len(unique_blocks)), labels=unique_blocks, fontsize=4, rotation=45)
    plt.yticks(ticks=np.arange(shard_num) + 0.5, labels=[f"{i}" for i in range(shard_num)], fontsize=9)

    plt.xlabel("Block Height", fontsize=14)
    plt.ylabel("Shard Index", fontsize=14)

    if method == 3:
        title_method = "Monoxide"
    elif method == 1:
        title_method = "CLPA"
    else:
        title_method = "Broker"
    plt.title(f"Transaction Pool Size Heatmap\nMethod: {title_method}", fontsize=16)
    # 确保保存目录存在
    os.makedirs(save_directory, exist_ok=True)
    save_path = f"{save_directory}/6_txpoolsize_heatmap_blocks{method}_{shard_num}s4n.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight', format='png')
    plt.close()


# 示例调用
# generate_txpool_heatmap(3, "expTest0_new_monoxide_4s4n_f1000k_100/result/pbft_shardNum=4", 4, "./output_plots_T")
