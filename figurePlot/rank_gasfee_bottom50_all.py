import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter


def addr_to_shard(addr: str, shard_num: int) -> int:
    """计算地址 addr 属于哪个分片（Shard）。"""
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

# **3. 计算 Input ITX & CTX**
df_input["from_shard"] = df_input["from"].apply(lambda x: addr_to_shard(x, SHARD_NUM))
df_input["to_shard"] = df_input["to"].apply(lambda x: addr_to_shard(x, SHARD_NUM))

df_input_itx = df_input[df_input["from_shard"] == df_input["to_shard"]].copy()  # 片内交易 ITX
df_input_ctx = df_input[df_input["from_shard"] != df_input["to_shard"]].copy()  # 跨片交易 CTX

# **4. 读取上链交易 CSV**
file_path_onchain = f"expTest0_new_monoxide_{SHARD_NUM}s4n_f1000k/result/supervisor_measureOutput/Tx_Details.csv"
df_onchain = pd.read_csv(file_path_onchain)

# **5. 筛选上链 ITX & CTX**
df_onchain_itx = df_onchain[df_onchain.iloc[:, 6].isna() & df_onchain.iloc[:, 7].isna()].copy()  # ITX: Relay1 & Relay2 均为空
df_onchain_ctx = df_onchain[df_onchain.iloc[:, 6].notna() & df_onchain.iloc[:, 7].notna()].copy()  # CTX: Relay1 或 Relay2 非空

# **6. 计算手续费**
def compute_fee(df, gas_col=10, gas_used_col=11):
    df["gasPrice"] = df.iloc[:, gas_col].astype(float)
    df["gasUsed"] = df.iloc[:, gas_used_col].astype(float)
    df["fee"] = df["gasPrice"] * df["gasUsed"]
    return df

df_input_itx = compute_fee(df_input_itx)
df_input_ctx = compute_fee(df_input_ctx)
df_onchain_itx = compute_fee(df_onchain_itx, gas_col=11, gas_used_col=12)
df_onchain_ctx = compute_fee(df_onchain_ctx, gas_col=11, gas_used_col=12)

# **7. 统一排序并选取** 【手续费最小的 50 笔交易】
df_input_itx_bottom50 = df_input_itx.sort_values(by="fee", ascending=True).head(50).copy()
df_input_ctx_bottom50 = df_input_ctx.sort_values(by="fee", ascending=True).head(50).copy()
df_onchain_itx_bottom50 = df_onchain_itx.sort_values(by="fee", ascending=True).head(50).copy()
df_onchain_ctx_bottom50 = df_onchain_ctx.sort_values(by="fee", ascending=True).head(50).copy()

# **8. 生成 X 轴**
x_values = np.arange(1, 51)
bar_width = 0.2  # 调整柱子宽度

# **9. 颜色配置**
color_input_itx = "#1c5a94"  # 深蓝
color_onchain_itx = "#c70000"  # 深红
color_input_ctx = "#008000"   # 绿色
color_onchain_ctx = "#ffa500"  # 橙色

# **10. 创建图表**
plt.figure(figsize=(16, 8))

# **11. 画 4 组柱子**
plt.bar(x_values - 1.5 * bar_width, df_input_itx_bottom50["fee"] / 1e12, width=bar_width, color=color_input_itx, label="Input ITX")
plt.bar(x_values - 0.5 * bar_width, df_onchain_itx_bottom50["fee"] / 1e12, width=bar_width, color=color_onchain_itx, label="On-Chain ITX")
plt.bar(x_values + 0.5 * bar_width, df_input_ctx_bottom50["fee"] / 1e12, width=bar_width, color=color_input_ctx, label="Input CTX")
plt.bar(x_values + 1.5 * bar_width, df_onchain_ctx_bottom50["fee"] / 1e12, width=bar_width, color=color_onchain_ctx, label="On-Chain CTX")

plt.axhline(0, color='black', linewidth=1)

# **12. 设置标题**
plt.xlabel("Transaction Rank (Bottom 50)")
plt.ylabel("Fee (× 10¹² Wei)")
plt.title("Comparison of Gas Fees in Input vs. On-Chain Transactions\n(ITX & CTX - Bottom 50)", fontsize=14)

# **13. X 轴优化**
plt.xticks(ticks=x_values, labels=[str(i) for i in x_values], fontsize=10)

# **14. Y 轴格式化**
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:.0f}'))

# **15. X 轴范围**
plt.xlim(0.5, 50.5)

# **16. 添加网格**
plt.grid(axis="y", linestyle="--", alpha=0.7)

# **17. 添加图例**
plt.legend()

# **18. 显示图表**
plt.show()
