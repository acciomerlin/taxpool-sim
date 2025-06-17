import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_ctx_ratios(file_paths: dict, save_directory: str):
    """
    计算并绘制不同共识方法的 CTX 比例随分片数的变化。

    :param file_paths: 包含不同共识方法的 CSV 文件路径字典
    :param save_directory: 保存图像的文件夹
    """
    # **1. 定义分片数**
    shard_labels = [4, 8, 16, 32]
    shard_positions = range(len(shard_labels))

    # **2. 读取数据的函数**
    def read_ctx_ratios(file_list):
        ctx_ratios = []
        for idx, file in enumerate(file_list):
            df = pd.read_csv(file, header=None)

            if idx == len(file_list) - 1:  # CLPA 用综合 Epoch 数据
                sum_col2 = df.iloc[1:, 1].astype(float).sum()  # 第 2 列总和
                sum_col3 = df.iloc[1:, 2].astype(float).sum()  # 第 3 列总和
                ratio = sum_col3 / sum_col2 if sum_col2 != 0 else 0  # 避免除零错误
            else:
                ratio = float(df.iloc[1, 6])  # 读取 CSV 第二行第七列数据

            ctx_ratios.append(ratio)
        return ctx_ratios

    # **3. 读取所有共识方法的数据**
    ctx_ratios_data = {method: read_ctx_ratios(paths) for method, paths in file_paths.items()}

    # **4. 定义颜色**
    colors = {
        "Monoxide": ['#E6F6B2', '#B8E051', '#94C81C', '#5F7D05'],
        "BrokerChain": ['#f8e3b1', '#f1c94a', '#e8a32c', '#c67a1c'],
        "Monoxide+CLPA": ['#a7d3e0', '#72b1c9', '#4f9abf', '#2c5d74']
    }

    # **5. 创建 3 个子图**
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    for ax, (method, ctx_ratios) in zip(axes, ctx_ratios_data.items()):
        # 绘制柱状图
        ax.bar(shard_positions, ctx_ratios, width=0.5, color=colors[method])

        # 设置 y 轴范围
        ax.set_ylim(0, max(max(ctx_ratios_data.values())) * 1.1)

        # 添加数值标注
        for i, v in enumerate(ctx_ratios):
            ax.text(i, v + (max(ctx_ratios) * 0.02), f'{v:.4f}', ha='center', fontsize=10, fontweight='bold', color=colors[method][i])

        # 设置标题
        ax.set_title(f"CTX Ratio under {method} Model", fontsize=12)
        ax.set_xticks(shard_positions)
        ax.set_xticklabels(shard_labels)

    # **6. 统一 x 轴和 y 轴标签**
    fig.text(0.5, 0.04, "Shard Count", ha='center', fontsize=12)
    fig.text(0.04, 0.5, "CTX Ratio", va='center', rotation='vertical', fontsize=12)

    # **7. 调整子图间距**
    plt.tight_layout()

    # **8. 确保保存目录存在**
    os.makedirs(save_directory, exist_ok=True)

    # **9. 生成保存路径**
    save_path = os.path.join(save_directory, "ctx_ratios_per_shard.png")

    # **10. 保存图像**
    plt.savefig(save_path, dpi=300, bbox_inches='tight', format='png')
    print(f"✅ 图像已保存: {save_path}")

    # **11. 关闭图像，防止内存泄漏**
    plt.close()

# file_paths = {
#     "Monoxide": [
#         "expTest0_new_monoxide_4s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_monoxide_8s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_monoxide_16s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_monoxide_32s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv"
#     ],
#     "BrokerChain": [
#         "expTest0_new_b_4s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_b_8s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_b_16s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_b_32s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv"
#     ],
#     "Monoxide+CLPA": [
#         "expTest0_new_c_4s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_c_8s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_c_16s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv",
#         "expTest0_new_c_32s4n_f1000k/result/supervisor_measureOutput/CrossTransaction_ratio.csv"
#     ]
# }

# plot_ctx_ratios(file_paths, save_directory="output_plots")
