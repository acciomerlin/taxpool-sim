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
    last8_addr = addr[-8:] if len(addr) > 8 else addr

    try:
        num = int(last8_addr, 16)  # 解析十六进制地址
    except ValueError as e:
        print(f"地址解析失败: {e}")
        raise

    return num % shard_num


# **1. 设定分片数**
SHARD_NUM = 4

# **2. 读取输入交易 CSV**
file_path_input = "filtered_transactions_1000k.csv"
df_input = pd.read_csv(file_path_input)

# **3. 筛选输入交易中的 CTX**
df_input["from_shard"] = df_input["from"].apply(lambda x: addr_to_shard(x, SHARD_NUM))
df_input["to_shard"] = df_input["to"].apply(lambda x: addr_to_shard(x, SHARD_NUM))

df_input_ctx = df_input[df_input["from_shard"] != df_input["to_shard"]].copy()  # CTX: 跨分片交易

# **4. 读取上链交易 CSV**
file_path_onchain = f"expTest0_new_monoxide_{SHARD_NUM}s4n_f1000k/result/supervisor_measureOutput/Tx_Details.csv"
df_onchain = pd.read_csv(file_path_onchain)

# **5. 筛选上链 CTX（排除 ITX）**
df_onchain_ctx = df_onchain[df_onchain.iloc[:, 6].notna() & df_onchain.iloc[:, 7].notna()].copy()  # Relay1 或 Relay2 时间不为空

# **6. 提取 gasPrice 和 gasUsed 计算手续费**
df_input_ctx["gasPrice"] = df_input_ctx.iloc[:, 10].astype(float)
df_input_ctx["gasUsed"] = df_input_ctx.iloc[:, 11].astype(float)
df_input_ctx["fee"] = df_input_ctx["gasPrice"] * df_input_ctx["gasUsed"]

df_onchain_ctx["gasPrice"] = df_onchain_ctx.iloc[:, 11].astype(float)
df_onchain_ctx["gasUsed"] = df_onchain_ctx.iloc[:, 12].astype(float)
df_onchain_ctx["fee"] = df_onchain_ctx["gasPrice"] * df_onchain_ctx["gasUsed"]

# **7. 排序并选取前 50 交易**
df_input_top50 = df_input_ctx.sort_values(by="fee", ascending=False).head(50).copy()
df_onchain_top50 = df_onchain_ctx.sort_values(by="fee", ascending=False).head(50).copy()

# **8. 生成 X 轴排序**
x_values = np.arange(1, 51)

# **9. 设置颜色**
color_input = "#1c5a94"  # 深蓝色
color_onchain = "#c70000"  # 深红色

# **10. 创建图表**
plt.figure(figsize=(16, 8))
bar_width = 0.4

plt.bar(x_values - bar_width/2, df_input_top50["fee"] / 1e12, width=bar_width, color=color_input, label="Input CTX")
plt.bar(x_values[:len(df_onchain_top50)] + bar_width/2, df_onchain_top50["fee"] / 1e12, width=bar_width, color=color_onchain, label="On-Chain CTX")

plt.axhline(0, color='black', linewidth=1)

# **11. 设置标题**
plt.xlabel("Transaction Rank (Top 50)")
plt.ylabel("Fee (× 10¹² Wei)")
plt.title("Comparison of Gas Fees in Input CTX and On-Chain CTX")

plt.xticks(ticks=x_values, labels=[str(i) for i in x_values], fontsize=10)

# **12. 格式化 Y 轴**
def format_fee(x, pos):
    return f'{x:.0f}'

plt.gca().yaxis.set_major_formatter(FuncFormatter(format_fee))

plt.xlim(0.5, 50.5)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.legend()

# **13. 显示图表**
plt.show()
