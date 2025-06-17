import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

def plot_latency_distribution(method, csv_path, shard_num, save_directory):
    """
    根据给定的 method, csv 文件路径, 和 shard 数量，绘制交易延迟分布小提琴图。

    :param method: 选择方法 (0-3), method=0 或 2 使用 broker
    :param csv_path: CSV 文件路径
    :param shard_num: 片数量
    :param save_directory: 结果保存目录
    """
    # 读取CSV文件
    df = pd.read_csv(csv_path)

    # 确定使用 Relay 还是 Broker
    use_broker = method in [0, 2]
    if use_broker:
        relay1_col = "Broker1 Tx commit timestamp (not a broker tx -> nil)"
        relay2_col = "Broker2 Tx commit timestamp (not a broker tx -> nil)"
    else:
        relay1_col = "Relay1 Tx commit timestamp (not a relay tx -> nil)"
        relay2_col = "Relay2 Tx commit timestamp (not a relay tx -> nil)"

    # 确保时间戳为数值类型
    time_cols = [
        "Tx propose timestamp",
        "Block propose timestamp",
        "Tx finally commit timestamp",
        relay1_col,
        relay2_col
    ]
    for col in time_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 计算所有交易的确认时延
    df["All_Latency"] = df["Tx finally commit timestamp"] - df["Tx propose timestamp"]

    # 筛选跨片交易（Relay1/Relay2 不为空的行）
    cross_shard_mask = df[relay1_col].notna() & df[relay2_col].notna()
    cross_shard_df = df[cross_shard_mask].copy()

    # 计算跨片交易的时延
    cross_shard_df["Cross_Avg"] = cross_shard_df[relay2_col] - cross_shard_df["Tx propose timestamp"]
    cross_shard_df["Cross_Phase1"] = cross_shard_df[relay1_col] - cross_shard_df["Tx propose timestamp"]
    cross_shard_df["Cross_Phase2"] = cross_shard_df[relay2_col] - cross_shard_df[relay1_col]

    # 筛选片内交易（Relay1/Relay2 为空的行）
    intra_shard_mask = df[relay1_col].isna() & df[relay2_col].isna()
    intra_shard_df = df[intra_shard_mask].copy()
    intra_shard_df["Intra_Latency"] = intra_shard_df["Tx finally commit timestamp"] - intra_shard_df["Tx propose timestamp"]

    # 合并数据用于绘图
    plot_data = pd.DataFrame({
        "Type": ["All Transactions"] * len(df) +
                ["Intra-Shard"] * len(intra_shard_df) +
                ["Cross-Shard Avg"] * len(cross_shard_df) +
                ["Cross-Shard Phase1"] * len(cross_shard_df) +
                ["Cross-Shard Phase2"] * len(cross_shard_df),
        "Latency(ms)": pd.concat([
            df["All_Latency"],
            intra_shard_df["Intra_Latency"],
            cross_shard_df["Cross_Avg"],
            cross_shard_df["Cross_Phase1"],
            cross_shard_df["Cross_Phase2"],
        ], ignore_index=True)
    })

    # 绘制小提琴图
    plt.figure(figsize=(14, 8))
    sns.violinplot(
        x="Type",
        y="Latency(ms)",
        data=plot_data,
        width=1,
        linewidth=2,
        palette="Set2",
        orient="v",
        inner="box",
    )

    if method == 3:
        title_method = "Monoxide"
    elif method == 1:
        title_method = "CLPA"
    else:
        title_method = "Broker"

    plt.title(f"Transaction Latency Distribution (Method {title_method}, {shard_num} Shards)", fontsize=14)
    plt.xlabel("Latency Type", fontsize=12)
    plt.ylabel("Latency (ms)", fontsize=12)
    plt.xticks(rotation=15)
    sns.despine()

    # 保存图像
    os.makedirs(save_directory, exist_ok=True)
    output_path = os.path.join(save_directory, f"2_latency_distribution_method{method}_{shard_num}s4n.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
    # plt.show()
    plt.close()

    print(f"✅ 交易延迟分布图已保存至 {output_path}")

# plot_latency_distribution(method=3,
#                           csv_path="expTest0_new_c_4s4n_f1000k/result/supervisor_measureOutput/Tx_Details.csv",
#                           shard_num=4,
#                           save_directory="./output_plots")
