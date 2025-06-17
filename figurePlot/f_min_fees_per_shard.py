import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_min_fees_per_block(method: int, csv_source: str, shard_num: int, save_directory: str):
    """
    绘制每个分片的 ITX 和 CTX 交易最小手续费随区块变化的曲线。
    :param method: 0-3，method=0,2 时使用 Broker 进行 ITX/CTX 区分
    :param csv_source: CSV 文件路径
    :param shard_num: 分片数
    :param save_directory: 结果保存目录
    """
    # 读取 CSV 文件
    df = pd.read_csv(csv_source)

    # 计算手续费（Fee = Gas Price * Gas Used）
    df["Fee"] = df["Gas Price"].astype(float) * df["Gas Used"].astype(float)

    # 过滤无效交易
    df = df[df["Fee"] > 0]

    # 区分 ITX 和 CTX 交易
    if method in [0, 2]:  # Broker 方式
        df_itx = df[df["Broker1 Tx commit timestamp (not a broker tx -> nil)"].isna() &
                    df["Broker2 Tx commit timestamp (not a broker tx -> nil)"].isna()]
        df_ctx = df[df["Broker1 Tx commit timestamp (not a broker tx -> nil)"].notna() &
                    df["Broker2 Tx commit timestamp (not a broker tx -> nil)"].notna()]
    else:  # Relay 方式
        df_itx = df[df["Relay1 Tx commit timestamp (not a relay tx -> nil)"].isna() &
                    df["Relay2 Tx commit timestamp (not a relay tx -> nil)"].isna()]
        df_ctx = df[df["Relay1 Tx commit timestamp (not a relay tx -> nil)"].notna() &
                    df["Relay2 Tx commit timestamp (not a relay tx -> nil)"].notna()]

    # 计算每个 (Shard ID, Block Number) 内 ITX 和 CTX 的最小手续费
    itx_min_fees = df_itx.groupby(["Shard ID", "Block Number"])["Fee"].min().reset_index()
    ctx_min_fees = df_ctx.groupby(["Shard ID", "Block Number"])["Fee"].min().reset_index()

    # 创建图像
    plt.figure(figsize=(12, 6), dpi=300)

    # 选取调色板
    itx_palette = sns.color_palette("Greens_d", n_colors=shard_num)  # 深绿色
    ctx_palette = sns.color_palette("Reds_d", n_colors=shard_num)  # 深红色


# itx_palette = sns.cubehelix_palette(n_colors=shard_num, start=0, rot=0.8, light=0.7, dark=0.2)
    # ctx_palette = sns.cubehelix_palette(n_colors=shard_num, start=2, rot=-0.8, light=0.7, dark=0.2)


# 绘制 ITX 最小手续费曲线
    sns.lineplot(data=itx_min_fees, x="Block Number", y="Fee", hue="Shard ID", palette=itx_palette, marker="o", legend="full")

    # 绘制 CTX 最小手续费曲线
    sns.lineplot(data=ctx_min_fees, x="Block Number", y="Fee", hue="Shard ID", palette=ctx_palette, marker=".", legend="full")

    # 设置坐标轴和标题
    plt.xlabel("Block Number", fontsize=12)
    plt.ylabel("Min Fee (Wei)", fontsize=12)
    plt.yscale("log")  # 使用对数坐标

    if method == 3:
        title_method = "Monoxide"
    elif method == 1:
        title_method = "CLPA"
    else:
        title_method = "Broker"
    plt.title(f"Min Transaction Fees per Block (ITX vs CTX)\nMethod: {title_method}", fontsize=14)

    # 添加网格
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # 添加 ITX 和 CTX 说明
    plt.scatter([], [], color='green', label="ITX", marker="o", s=10)
    plt.scatter([], [], color='red', label="CTX", marker="o", s=10)

    # 显示图例（两列+放到图外）
    plt.legend(title="Shard ID", fontsize=10, loc="upper left", bbox_to_anchor=(1.05, 1), ncol=2)

    # 确保保存目录存在
    os.makedirs(save_directory, exist_ok=True)

    # 生成保存路径
    save_path = os.path.join(save_directory, f"4_min_fees_block_method{method}_{shard_num}s4n.png")

    # 保存图像
    plt.savefig(save_path, dpi=300, bbox_inches='tight', format='png')
    print(f"✅ 图像已保存: {save_path}")

    # 关闭图像，防止内存泄漏
    plt.close()

# 示例调用：
# plot_min_fees_per_block(
#     method=3,
#     csv_source="expTest0_new_monoxide_4s4n_f1000k/result/supervisor_measureOutput/Tx_Details.csv",
#     shard_num=4,
#     save_directory="output_plots"
# )
