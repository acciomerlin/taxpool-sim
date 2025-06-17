import os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_transaction_comparison(input_csv, onchain_csv, save_directory="output_plots"):
    """
    读取输入交易和链上交易数据，并绘制对比柱状图

    :param save_directory:
    :param input_csv: 输入交易 CSV 文件路径（包含 'from' 和 'to' 列）
    :param onchain_csv: 链上交易 CSV 文件路径（包含 'Sender' 和 'Recipient' 列）
    """
    # 读取输入交易数据
    input_df = pd.read_csv(input_csv)
    from_counts = input_df['from'].value_counts()
    to_counts = input_df['to'].value_counts()
    input_total_counts = from_counts.add(to_counts, fill_value=0)
    top_input_accounts = input_total_counts.nlargest(100)

    # 计算平均交易次数（输入交易）
    avg_input_transactions = input_total_counts.sum() / len(input_total_counts)

    # 读取链上交易数据
    onchain_df = pd.read_csv(onchain_csv)
    sender_counts = onchain_df['Sender'].value_counts()
    recipient_counts = onchain_df['Recipient'].value_counts()
    onchain_total_counts = sender_counts.add(recipient_counts, fill_value=0)
    top_onchain_accounts = onchain_total_counts.nlargest(100)

    # 计算平均交易次数（链上交易）
    avg_onchain_transactions = onchain_total_counts.sum() / len(onchain_total_counts)

    # 设置绘图风格
    sns.set(style="whitegrid")

    # 创建包含两个子图的画布
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), dpi=300)
    plt.subplots_adjust(wspace=0.4)

    # 绘制输入交易统计图
    sns.barplot(ax=axes[0], x=top_input_accounts.values, y=top_input_accounts.index, palette="magma")
    axes[0].set_xlabel("Transaction Count", fontsize=12)
    axes[0].set_ylabel("Account Address", fontsize=10)
    axes[0].set_title(f"Top 100 Accounts by Input Transactions\n(Avg: {avg_input_transactions:.2f} transactions/account)", fontsize=14)
    axes[0].tick_params(axis='y', labelsize=4)  # 调整 y 轴标签大小

    # 绘制链上交易统计图
    sns.barplot(ax=axes[1], x=top_onchain_accounts.values, y=["0x" + addr for addr in top_onchain_accounts.index], palette="viridis")
    axes[1].set_xlabel("Transaction Count", fontsize=12)
    axes[1].set_ylabel("Account Address", fontsize=10)
    axes[1].set_title(f"Top 100 Accounts by On-chain Transactions\n(Avg: {avg_onchain_transactions:.2f} transactions/account)", fontsize=14)
    axes[1].tick_params(axis='y', labelsize=4)  # 调整 y 轴标签大小

    save_path = os.path.join(save_directory, "1_transaction_comparison.png")
    # 确保保存目录存在
    os.makedirs(save_directory, exist_ok=True)
    # 保存图像
    plt.savefig(save_path, dpi=300, bbox_inches='tight', format='png')

    print(f"✅ 交易统计图已保存至 {save_path}")
    plt.close()


# plot_transaction_comparison(
#     input_csv="filtered_transactions_1000k.csv",
#     onchain_csv="expTest0_new_4s4n_f1000k/result/supervisor_measureOutput/Tx_Details.csv",
# )