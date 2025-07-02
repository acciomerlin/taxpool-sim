from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_updated_tax_metrics(method: int, shard_csv_dir: str, shard_num: int,
                             save_directory: str, alpha: float, beta: float):

    os.makedirs(save_directory, exist_ok=True)

    for shard_id in range(shard_num):
        # shard_path = os.path.join(shard_csv_dir, f"Shard{shard_id}{shard_num}.csv")
        # if not os.path.exists(shard_path):
        #     print(f"❌ Shard{shard_id}{shard_num}.CSV 不存在: {shard_path}")
        #     return

        # df = pd.read_csv(shard_path)
        df = pd.read_csv(shard_csv_dir)
        df.columns = [f"Col{i}" for i in range(df.shape[1])]

        # ------- 预处理 -------
        block_height = df["Col0"]
        tax = df["Col6"].replace("nil", np.nan).astype(float) / 1e18
        subsidy = df["Col7"].replace("nil", np.nan).astype(float) / 1e18
        f_itx_min = df["Col8"].replace("nil", np.nan).astype(float) / 1e18
        f_ctx_min = df["Col9"].replace("nil", np.nan).astype(float) / 1e18
        balance = df["Col4"].replace("nil", np.nan).astype(float) / 1e18
        deltabalance = df["Col5"].replace("nil", np.nan).astype(float) / 1e18

        

        # ------- 创建图和三个子图 -------
        fig, axes = plt.subplots(1, 4, figsize=(36, 6), dpi=300, sharex=True, gridspec_kw={'wspace': 0.25})
        fig.suptitle(f"Shard {shard_id} Metrics Overview\nMethod={method}, α={alpha}, β={beta}", fontsize=14)

        # 设置一组不重复的颜色
        colors = ['#3a86ff', '#ff7b3e', '#4cc9f0', '#f6b93b', '#3a0ca3', '#f72585']

        # --- Subplot 1: Tax & Subsidy （单 Y 轴）---
        ax1 = axes[0]
        p1 = ax1.plot(block_height, tax, marker='o', markersize=3, color=colors[0], label="Tax")[0]
        p2 = ax1.plot(block_height, subsidy, marker='s', markersize=3, linestyle='--', color=colors[1], label="Subsidy")[0]

        # 标记缺失值点（红色 x）
        ax1.plot(block_height[tax.isna()], [0]*tax.isna().sum(), 'rx', label="Missing Tax")
        ax1.plot(block_height[subsidy.isna()], [0]*subsidy.isna().sum(), 'r+', label="Missing Subsidy")

        ax1.set_xlabel("Block Height")
        ax1.set_ylabel("Value (ETH)")
        ax1.grid(True, linestyle="--", alpha=0.4)
        ax1.legend(loc='upper left')
        
        # # --- Subplot 1: Tax & Subsidy（symlog y 轴）---
        # ax1 = axes[0]
        # ax1_right = ax1.twinx()

        # p1, = ax1.plot(block_height, tax, marker='o', markersize=3, color=colors[0], label="Tax")
        # p2, = ax1_right.plot(block_height, subsidy, marker='s', markersize=3, linestyle='--', color=colors[1], label="Subsidy")

        # ax1.set_xlabel("Block Height")
        # ax1.set_ylabel("Tax (ETH, symlog)")
        # ax1_right.set_ylabel("Subsidy (ETH, symlog)")

        # # ✅ 使用 symlog：对称对数坐标（允许负数，接近0的范围为线性）
        # ax1.set_yscale("symlog", linthresh=1e-8)
        # ax1_right.set_yscale("symlog", linthresh=1e-8)

        # # symlog 原理解释（适合做注释）：
        # # - 正负两侧对称地使用对数缩放（适合处理负值、值域跨度大的数据）
        # # - 在接近 0 的线性区域 [-linthresh, linthresh]，避免 log 坐标的无限陡峭
        # # - 非常适合同时显示非常小与非常大的值，且可包含 0 与负值

        # ax1.grid(True, linestyle="--", alpha=0.4)
        # ax1_right.grid(True, linestyle="--", alpha=0.4)
        # ax1.legend(handles=[p1, p2], loc='upper left')


        # --- Subplot 2: F_itx_min & F_ctx_min ---
        ax2 = axes[1]
        ax2.plot(block_height, f_itx_min, marker='o', markersize=3, color=colors[2], label="F_itx_min")
        ax2.plot(block_height, f_ctx_min, marker='s', markersize=3, linestyle='--', color=colors[3], label="F_ctx_min")


        # ax2.plot(block_height[f_itx_min.isna()], [0]*f_itx_min.isna().sum(), 'rx', label="Missing F_itx_min")
        # ax2.plot(block_height[f_ctx_min.isna()], [0]*f_ctx_min.isna().sum(), 'r+', label="Missing F_ctx_min")

        ax2.set_xlabel("Block Height")
        ax2.set_ylabel("Min Fee (ETH)")
        # ax2.set_title("Min ITX/CTX Fee")
        ax2.set_ylim(bottom=0)  # ✅ 从 0 起始
        ax2.grid(True, linestyle="--", alpha=0.6)
        ax2.legend()

        # --- Subplot 3: Balance（含上下阈值）---
        ax3 = axes[2]
        ax3.plot(block_height, balance, marker='o', markersize=3, color=colors[4], label="Balance")
        ax3.axhline(beta, color="gray", linestyle="--", label=f"+EpsilonBalance")
        ax3.axhline(-beta, color="gray", linestyle="--", label=f"-EpsilonBalance")
        ax3.axhline(0, color="black", linestyle=":", linewidth=1)

        # 标记缺失值
        ax3.plot(block_height[balance.isna()], [0]*balance.isna().sum(), 'rx', label="Missing Balance")

        ax3.set_xlabel("Block Height")
        ax3.set_ylabel("Balance (ETH)")
        # ax3.set_title("Balance with ±β Threshold")
        ax3.grid(True, linestyle="--", alpha=0.4)
        ax3.legend()

        # --- Subplot 4: ΔBalance（含上下阈值）---
        ax4 = axes[3]
        ax4.plot(block_height, deltabalance, marker='^', markersize=3, linestyle='--', color=colors[5], label="ΔBalance")
        ax4.axhline(alpha, color="gray", linestyle="--", label=f"+EpsilonΔBalance")
        ax4.axhline(-alpha, color="gray", linestyle="--", label=f"-EpsilonΔBalance")
        ax4.axhline(0, color="black", linestyle=":", linewidth=1)

        # 标记缺失值
        ax4.plot(block_height[deltabalance.isna()], [0]*deltabalance.isna().sum(), 'r+', label="Missing ΔBalance")

        ax4.set_xlabel("Block Height")
        ax4.set_ylabel("ΔBalance (ETH)")
        # ax4.set_title("ΔBalance with ±α Threshold")
        ax4.grid(True, linestyle="--", alpha=0.4)
        ax4.legend()


        # # --- Subplot 3: Balance & DeltaBalance (symlog) ---
        # ax3 = axes[2]
        # ax3_right = ax3.twinx()

        # p3, = ax3.plot(block_height, balance, marker='o', markersize=3, color=colors[4], label="Balance")
        # p4, = ax3_right.plot(block_height, deltabalance, marker='^', markersize=3, linestyle='--', color=colors[5], label="ΔBalance")

        # # 对数坐标（对称对数 symlog 以处理负值）
        # ax3.set_yscale("symlog", linthresh=1e-2)
        # ax3_right.set_yscale("symlog", linthresh=1e-2)

        # # 添加 balance=0 的横线
        # zero_line = ax3.axhline(0, color="#f6b93b", linestyle="--", linewidth=1, label="Balance=0")
        # ax3_right.axhline(0, color="#f6b93b", linestyle="--", linewidth=1)

        # ax3.set_xlabel("Block Height")
        # ax3.set_ylabel("Balance (ETH, symlog)")
        # ax3_right.set_ylabel("ΔBalance (ETH, symlog)")
        # ax3.grid(True, linestyle="--", alpha=0.4)
        # ax3_right.grid(True, linestyle="--", alpha=0.4)

        # # 将三条线都加入图例
        # ax3.legend(handles=[p3, p4, zero_line], loc='lower left')



        # ------- 保存图像 -------
        # plt.tight_layout(rect=[0, 0, 1, 0.96])  # 留出 suptitle 空间
        # 当前时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 格式如：20250617_142301

        # 拼接带时间戳的文件路径
        output_path = os.path.join(save_directory, f"shard{shard_id}_{timestamp}.png")
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()

        print(f"✅ 已生成合并图：Shard {shard_id} → {output_path}")

    print("🎉 所有 shard 图表已生成完成！")

