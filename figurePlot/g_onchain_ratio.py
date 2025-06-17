import os

import pandas as pd
import matplotlib.pyplot as plt


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
    """
    计算地址 addr 属于哪个分片（Shard）。
    :param addr: 地址（字符串形式的十六进制数）
    :param shard_num: 分片总数
    :return: 计算得到的分片 ID
    """
    last8_addr = addr[-8:] if len(addr) > 8 else addr
    try:
        num = int(last8_addr, 16)
    except ValueError as e:
        print(f"地址解析失败: {e}")
        raise
    return num % shard_num

def analyze_transaction_sharding(method: int, shard_num: int, input_csv: str, onchain_csv: str, save_path: str = None):
    """
    计算并可视化跨片（CTX）和片内（ITX）交易的分布及上链比率。
    :param shard_num: 分片总数
    :param input_csv: 输入交易 CSV 文件路径
    :param onchain_csv: 上链交易 CSV 文件路径
    :param save_path: 可选，保存图像的路径
    """
    df_input = pd.read_csv(input_csv)
    input_ctx_num, input_itx_num = 0, 0

    brokers = load_brokers("./broker/broker") if method in [0, 2] else set()  # 只加载一次

    for _, row in df_input.iterrows():
        from_shard = addr_to_shard(row["from"], shard_num)
        to_shard = addr_to_shard(row["to"], shard_num)

        if from_shard == to_shard:
            input_itx_num += 1
        else:
            # 是跨片，但如果是 broker，则视为 ITX
            if row["from"] in brokers or row["to"] in brokers:
                input_itx_num += 1
            else:
                input_ctx_num += 1

    print(f"\ninput_itx_num:{input_itx_num}\n")
    # 读取上链交易 CSV
    df_onchain = pd.read_csv(onchain_csv)
    if method == 1:
        # method == 1 时，clpa累加各个epoch
        onchain_ctx_num = df_onchain.iloc[:, 2].sum()
        onchain_itx_num = df_onchain.iloc[:, 3].sum()
    else:
        # 默认只读取第一行
        onchain_ctx_num = int(df_onchain.iloc[0, 2])
        onchain_itx_num = int(df_onchain.iloc[0, 3])
    print(f"\nonchain_itx_num:{onchain_itx_num}\n")
    # 计算上链比率
    ctx_onchain_ratio = (onchain_ctx_num / input_ctx_num * 100) if input_ctx_num > 0 else 0
    itx_onchain_ratio = (onchain_itx_num / input_itx_num * 100) if input_itx_num > 0 else 0
    print(f"\nitx_onchain_ratio:{itx_onchain_ratio}\n")
    # if ctx_onchain_ratio > 100 : ctx_onchain_ratio = 100
    # if itx_onchain_ratio > 100 : itx_onchain_ratio = 100

    # 绘制柱状图
    labels = ["CTX (Cross-Shard)", "ITX (Intra-Shard)"]
    input_values = [input_ctx_num, input_itx_num]
    onchain_values = [onchain_ctx_num, onchain_itx_num]
    x = range(len(labels))

    plt.figure(figsize=(8, 6))
    plt.bar(x, input_values, width=0.4, label="Input Transactions", color="#90caf9", alpha=0.7)
    plt.bar([i + 0.4 for i in x], onchain_values, width=0.4, label="On-Chain Transactions", color="#ffab91", alpha=0.7)
    plt.xticks([i + 0.2 for i in x], labels)
    plt.ylabel("Transaction Count")
    plt.title(f"Input vs. On-Chain Transactions (CTX & ITX)\n"
              f"CTX On-Chain Rate: {ctx_onchain_ratio:.2f}%  |  ITX On-Chain Rate: {itx_onchain_ratio:.2f}%",
              fontsize=14)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    save_path = os.path.join(save_path, f"5_on-chain-ratio.png")

    # 保存或显示图像
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    # plt.show()


# shard_num = 4
# input_csv = "filtered_transactions_1000k.csv"
# onchain_csv = "expTest1_0404_broker_4s4n_f1000k_400/result/supervisor_measureOutput/CrossTransaction_ratio.csv"
# save_path = "output_plots0407"

# analyze_transaction_sharding(shard_num, input_csv, onchain_csv, save_path)

