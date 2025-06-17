import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_latency_vs_fee(csv_path, method=0, shard_num=4, save_directory=None):
    """
    生成交易手续费 vs 时延的散点图。
    :param csv_path: CSV 文件路径
    :param method: 选择不同的处理方式 (0-3)
    :param shard_num: 分片数量（当前代码未使用，可扩展）
    :param save_directory: 保存图像的目录（可选）
    """
    # 读取 CSV 文件
    df = pd.read_csv(csv_path)

    # 计算时延（最终提交时间 - 提案时间）
    df["Latency (ms)"] = df.iloc[:, 5] - df.iloc[:, 3]  # `Tx finally commit timestamp` - `Tx propose timestamp`

    # 计算手续费（Gas Price * Gas Used）
    df["Fee (Wei)"] = df.iloc[:, 11].astype(float) * df.iloc[:, 12].astype(float)

    # 过滤掉无效数据（时延或手续费小于等于 0）
    df = df[(df["Latency (ms)"] >= 0) & (df["Fee (Wei)"] >= 0)]

    # 交易类型区分（CTX：跨片交易，ITX：片内交易）
    if method in [0, 2]:  # 使用 Broker 进行区分
        df_ctx = df[df[df.columns[8]].notna() & df[df.columns[9]].notna()]
        df_itx = df[df[df.columns[8]].isna() & df[df.columns[9]].isna()]
    else:  # 传统方式区分 CTX 和 ITX
        df_ctx = df[df[df.columns[6]].notna() & df[df.columns[7]].notna()]
        df_itx = df[df[df.columns[6]].isna() & df[df.columns[7]].isna()]

    # 创建绘图
    plt.figure(figsize=(10, 6), dpi=300)

    # CTX（跨片交易，橙色）
    plt.scatter(df_ctx["Fee (Wei)"] / 1e12, df_ctx["Latency (ms)"],
                alpha=0.8, c="#f6c56f", edgecolors="none", s=5, marker="o", label="Cross-Shard Transactions (CTX)")

    # ITX（片内交易，蓝色）
    plt.scatter(df_itx["Fee (Wei)"] / 1e12, df_itx["Latency (ms)"],
                alpha=0.8, c="#457b9d", edgecolors="none", s=5, marker="o", label="Intra-Shard Transactions (ITX)")

    # 对数缩放 X 轴（手续费）
    plt.xscale('symlog')

    if method == 3:
        title_method = "Monoxide"
    elif method == 1:
        title_method = "CLPA"
    else:
        title_method = "Broker"

    # 设置坐标轴
    plt.xlabel("Fee (× 10¹² Wei)", fontsize=12)
    plt.ylabel("Latency (ms)", fontsize=12)
    plt.title(f"Transaction Fee vs. Latency\nMethod: {title_method}", fontsize=14)

    # 添加网格线
    plt.grid(True, linestyle="--", alpha=0.7)

    # 添加图例
    plt.legend()

    # 保存图像
    if save_directory:
        os.makedirs(save_directory, exist_ok=True)
        save_path = os.path.join(save_directory, f"3_latency_vs_fee_method{method}_{shard_num}s4n.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight', format='png')
        plt.close()

    # 显示图像
    # plt.show()

# 调用示例
# plot_latency_vs_fee("expTest0_new_monoxide_4s4n_f1000k/result/supervisor_measureOutput/Tx_Details.csv", method=3, save_directory="./output_plots")
