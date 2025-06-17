import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter


def addr_to_shard(addr: str, shard_num: int) -> int:
    """
    计算地址 addr 属于哪个分片（Shard）。
    :param addr: 地址（字符串形式的十六进制数）
    :param shard_num: 分片总数
    :return: 计算得到的分片 ID
    """
    # 取地址的最后 8 位
    last8_addr = addr[-8:] if len(addr) > 8 else addr

    try:
        # 解析十六进制字符串为整数
        num = int(last8_addr, 16)
    except ValueError as e:
        print(f"地址解析失败: {e}")
        raise

    return num % shard_num

# 定义分片总数
SHARD_NUM = 4

# 读取输入交易 CSV
file_path_input = "filtered_transactions_1000k.csv"  # 输入交易 CSV 文件路径
df_input = pd.read_csv(file_path_input)
# 筛选输入交易中的 ITX
df_input["from_shard"] = df_input["from"].apply(lambda x: addr_to_shard(x, SHARD_NUM))
df_input["to_shard"] = df_input["to"].apply(lambda x: addr_to_shard(x, SHARD_NUM))
df_input_itx = df_input[df_input["from_shard"] == df_input["to_shard"]].copy()

# 读取上链交易 CSV
file_path_onchain = f"expTest0_new_monoxide_{SHARD_NUM}s4n_f1000k/result/supervisor_measureOutput/Tx_Details.csv"  # 上链交易 CSV 文件路径
df_onchain = pd.read_csv(file_path_onchain)

# ctx filter
# df_onchain = df_onchain.dropna(subset=[df_onchain.columns[4], df_onchain.columns[5]])

# itx filter
df_onchain = df_onchain[
    df_onchain[df_onchain.columns[6]].isna() & df_onchain[df_onchain.columns[7]].isna()
    ]


# 计算手续费
df_input_itx["gasPrice"] = df_input.iloc[:, 10].astype(float)
df_input_itx["gasUsed"] = df_input.iloc[:, 11].astype(float)
df_input_itx["fee"] = df_input["gasPrice"] * df_input["gasUsed"]

df_onchain["gasPrice"] = df_onchain.iloc[:, 11].astype(float)
df_onchain["gasUsed"] = df_onchain.iloc[:, 12].astype(float)
df_onchain["fee"] = df_onchain["gasPrice"] * df_onchain["gasUsed"]

# 统一排序，按手续费降序排列
df_input_sorted = df_input_itx.sort_values(by="fee", ascending=False).reset_index(drop=True)
df_onchain_sorted = df_onchain.sort_values(by="fee", ascending=False).reset_index(drop=True)

# 选取前 50 交易
df_input_top50 = df_input_sorted.head(50).copy()
df_onchain_top50 = df_onchain_sorted.head(50).copy()

# 生成排序序号（确保 x 轴从 1 开始）
x_values = np.arange(1, 51)

# 设置颜色
color_input = "#1c5a94"  # 输入交易颜色（深蓝色）
color_onchain = "#c70000"  # 上链交易颜色（深红色）

# 设置柱状图宽度
bar_width = 0.4  # 增加宽度，使间隔更大

# 创建图表
plt.figure(figsize=(16, 8))

# 绘制输入交易（蓝色）
plt.bar(x_values - bar_width/2, df_input_top50["fee"] / 1e12, width=bar_width, color=color_input, label="Input Transactions")

# 绘制上链交易（红色）
plt.bar(x_values + bar_width/2, df_onchain_top50["fee"] / 1e12, width=bar_width, color=color_onchain, label="On-Chain Transactions")

# 添加横轴线
plt.axhline(0, color='black', linewidth=1)

# 设置标题和标签
plt.xlabel("Transaction Rank (Top 50)")
plt.ylabel("Fee (× 10¹² Wei)")  # 在 y 轴标签上注明单位
# plt.title("Comparison of Gas Fees in Input and On-Chain Transactions")
plt.title("Comparison of Gas Fees in Input Itx and On-Chain Itx")

# 优化 x 轴刻度
plt.xticks(
    ticks=x_values,  # 这里使用完整的 1-50 作为刻度
    labels=[str(i) for i in x_values],  # 确保 labels 也有 50 个
    fontsize=10  # 调整字体大小，避免刻度太密集
)

# 设置 y 轴刻度格式（确保整洁）
def format_fee(x, pos):
    return f'{x:.0f}'  # 直接显示缩放后的值，无需额外单位

plt.gca().yaxis.set_major_formatter(FuncFormatter(format_fee))

# **扩展 x 轴范围，增加间隔**
plt.xlim(0.5, 50.5)  # 让 x 轴范围比 1-50 略宽一点，使柱子不拥挤

# 添加网格
plt.grid(axis="y", linestyle="--", alpha=0.7)

# 显示图例
plt.legend()

# 显示图表
plt.show()
