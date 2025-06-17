import time

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
import os

def load_brokers(file_path: str, top_n: int = 10):
    """从文件中加载前 top_n 个 Broker 地址，并标准化格式为 0x 开头小写地址"""
    brokers = set()
    try:
        with open(file_path, 'r') as file:
            for _, line in zip(range(top_n), file):
                raw = line.strip().lower()
                if not raw.startswith("0x"):
                    raw = "0x" + raw
                brokers.add(raw)
    except FileNotFoundError:
        print(f"Broker file not found: {file_path}")
    return brokers



def addr_to_shard(addr: str, shard_num: int) -> int:
    """计算地址 addr 属于哪个分片（Shard）。"""
    last8_addr = addr[-8:] if len(addr) > 8 else addr
    try:
        num = int(last8_addr, 16)  # 解析十六进制地址
    except ValueError as e:
        print(f"地址解析失败: {e}")
        raise
    return num % shard_num


def compute_fee(df, gas_col=10, gas_used_col=11):
    """计算手续费 = gasPrice × gasUsed"""
    df["gasPrice"] = df.iloc[:, gas_col].astype(float)
    df["gasUsed"] = df.iloc[:, gas_used_col].astype(float)
    df["fee"] = df["gasPrice"] * df["gasUsed"]
    return df


def plot_fee_comparison(method,input_csv, onchain_csv, shard_num=4, save_directory=None):
    """绘制 Input vs. On-Chain 交易费用对比（Top 50 & Bottom 50）"""
    # **1. 读取交易数据**
    df_input = pd.read_csv(input_csv)
    df_input["from_shard"] = df_input["from"].apply(lambda x: addr_to_shard(x, shard_num))
    df_input["to_shard"] = df_input["to"].apply(lambda x: addr_to_shard(x, shard_num))

    df_input_itx = df_input[df_input["from_shard"] == df_input["to_shard"]].copy()  # 片内交易 ITX
    df_input_ctx = df_input[df_input["from_shard"] != df_input["to_shard"]].copy()  # 跨片交易 CTX


    if method in [0, 2]:
        # brokers = load_brokers("./broker/broker")  # 加载 broker 地址
        # df_input_ctx = df_input_ctx[
        #     ~(df_input_ctx["from"].isin(brokers) | df_input_ctx["to"].isin(brokers))
        # ]
        df_onchain = pd.read_csv(onchain_csv)
        df_onchain_itx = df_onchain[df_onchain.iloc[:, 8].isna() & df_onchain.iloc[:, 9].isna()].copy()  # ITX: Relay1 & Relay2 为空
        df_onchain_ctx = df_onchain[df_onchain.iloc[:, 8].notna() & df_onchain.iloc[:, 9].notna()].copy()  # CTX: Relay1 或 Relay2 非空
    else:
        df_onchain = pd.read_csv(onchain_csv)
        df_onchain_itx = df_onchain[df_onchain.iloc[:, 6].isna() & df_onchain.iloc[:, 7].isna()].copy()  # ITX: Relay1 & Relay2 为空
        df_onchain_ctx = df_onchain[df_onchain.iloc[:, 6].notna() & df_onchain.iloc[:, 7].notna()].copy()  # CTX: Relay1 或 Relay2 非空



    # **2. 计算手续费**
    df_input_itx = compute_fee(df_input_itx)
    df_input_ctx = compute_fee(df_input_ctx)
    df_onchain_itx = compute_fee(df_onchain_itx, gas_col=11, gas_used_col=12)
    df_onchain_ctx = compute_fee(df_onchain_ctx, gas_col=11, gas_used_col=12)

    # **3. 选取 Top 50 和 Bottom 50**
    df_input_itx_top50 = df_input_itx.sort_values(by="fee", ascending=False).head(50).copy()
    df_input_ctx_top50 = df_input_ctx.sort_values(by="fee", ascending=False).head(50).copy()
    df_onchain_itx_top50 = df_onchain_itx.sort_values(by="fee", ascending=False).head(50).copy()
    df_onchain_ctx_top50 = df_onchain_ctx.sort_values(by="fee", ascending=False).head(50).copy()

    df_input_itx_bottom50 = df_input_itx.sort_values(by="fee", ascending=True).head(50).copy()
    df_input_ctx_bottom50 = df_input_ctx.sort_values(by="fee", ascending=True).head(50).copy()
    df_onchain_itx_bottom50 = df_onchain_itx.sort_values(by="fee", ascending=True).head(50).copy()
    df_onchain_ctx_bottom50 = df_onchain_ctx.sort_values(by="fee", ascending=True).head(50).copy()

    # 输出前十 on-chain 和 input 账户
    # top_onchain_addrs = pd.concat([df_onchain_itx, df_onchain_ctx])["from"].value_counts().head(10)
    # top_input_addrs = df_input["from"].value_counts().head(10)
    #
    # print("Top 10 On-Chain Addresses by Transaction Count:")
    # print(top_onchain_addrs)
    # print("\nTop 10 Input Addresses by Transaction Count:")
    # print(top_input_addrs)

    # **4. 生成 X 轴**
    x_values = np.arange(1, 51)
    bar_width = 0.2  # 调整柱子宽度

    # **5. 颜色配置**
    color_input_itx = "#1c5a94"  # 深蓝
    color_onchain_itx = "#c70000"  # 深红
    color_input_ctx = "#008000"  # 绿色
    color_onchain_ctx = "#ffa500"  # 橙色

    # **6. 创建图表**
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))  # 1 行 2 列子图

    # **7. 绘制 Top 50**
    ax1 = axes[0]
    ax1.bar(x_values - 1.5 * bar_width, df_input_itx_top50["fee"] / 1e12, width=bar_width, color=color_input_itx, label="Input ITX")
    ax1.bar(x_values - 0.5 * bar_width, df_onchain_itx_top50["fee"] / 1e12, width=bar_width, color=color_onchain_itx, label="On-Chain ITX")
    ax1.bar(x_values + 0.5 * bar_width, df_input_ctx_top50["fee"] / 1e12, width=bar_width, color=color_input_ctx, label="Input CTX")
    ax1.bar(x_values + 1.5 * bar_width, df_onchain_ctx_top50["fee"] / 1e12, width=bar_width, color=color_onchain_ctx, label="On-Chain CTX")
    ax1.set_title("Top 50 Transactions", fontsize=14)

    # **8. 绘制 Bottom 50**
    ax2 = axes[1]
    ax2.bar(x_values - 1.5 * bar_width, df_input_itx_bottom50["fee"] / 1e12, width=bar_width, color=color_input_itx, label="Input ITX")
    ax2.bar(x_values - 0.5 * bar_width, df_onchain_itx_bottom50["fee"] / 1e12, width=bar_width, color=color_onchain_itx, label="On-Chain ITX")
    ax2.bar(x_values + 0.5 * bar_width, df_input_ctx_bottom50["fee"] / 1e12, width=bar_width, color=color_input_ctx, label="Input CTX")
    ax2.bar(x_values + 1.5 * bar_width, df_onchain_ctx_bottom50["fee"] / 1e12, width=bar_width, color=color_onchain_ctx, label="On-Chain CTX")
    ax2.set_title("Bottom 50 Transactions", fontsize=14)

    # **9. 设置统一参数**
    for ax in axes:
        ax.set_xlabel("Transaction Rank")
        ax.set_ylabel("Fee (× 10¹² Wei)")
        ax.set_xticks(ticks=x_values)
        ax.set_xticklabels([str(i) for i in x_values], fontsize=9, rotation=90)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:.0f}'))
        ax.set_xlim(0.5, 50.5)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

    # **10. 添加图例**
    axes[0].legend()
    axes[1].legend()

    if method == 3:
        title_method = "Monoxide"
    elif method == 1:
        title_method = "CLPA"
    else:
        title_method = "Broker"

    # **11. 显示 & 保存**
    plt.tight_layout()
    if save_directory:
        os.makedirs(save_directory, exist_ok=True)
        save_path = os.path.join(save_directory, f"fee_comparison_{title_method}_{shard_num}s4n_{time.localtime()}.png")
        plt.savefig(save_path, dpi=300)
        plt.close()
    # plt.show()

# plot_fee_comparison("filtered_transactions_1000k.csv", "expTest0_new_monoxide_4s4n_f1000k/result/supervisor_measureOutput/Tx_Details.csv", shard_num=4, save_directory="./output_plots")
