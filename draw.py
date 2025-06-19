from figurePlot.plot_tax_metrics_over_blocks import plot_updated_tax_metrics


TAXPOOL_SIM_INPUT_CSV = "outputCSV/shard_20250620_010043.csv"
METHOD=3 # 3是monoxide方法
DATE = '0617'
# TYPE = 'v32_e12_12_2_018'
TYPE = '0'
input_csv="filtered_transactions_                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             11000k.csv"
DATASET = 'f11000k'

shard_list = [1]
inject_speed_list = [1000] #现在这里是blocksize

for SHARD_NUM in shard_list:
    for INJECT_SPEED in inject_speed_list:
        onchain_csv = f"expTest{TYPE}_{DATE}_{SHARD_NUM}s4n_{DATASET}_{INJECT_SPEED}/result/supervisor_measureOutput/Tx_Details.csv"
        onchain_cr_csv = f"expTest{TYPE}_{DATE}_{SHARD_NUM}s4n_{DATASET}_{INJECT_SPEED}/result/supervisor_measureOutput/CrossTransaction_ratio.csv"
        # onchain_s_csv = f"expTest{TYPE}_{DATE}_{METHODNAME}_{SHARD_NUM}s4n_{DATASET}_{INJECT_SPEED}/result/pbft_shardNum={SHARD_NUM}"
        onchain_s_csv = TAXPOOL_SIM_INPUT_CSV
        # save_directory = f"outputPlots_{TYPE}_{DATE}_{METHOD}_{SHARD_NUM}_{INJECT_SPEED}_{DATASET}"
        save_directory = f"outputPlots"

        # 以下为原有函数调用，不做修改，直接复用
        # plot_transaction_comparison(input_csv, onchain_csv, save_directory=save_directory)

        # plot_latency_distribution(method=METHOD,
        #                           csv_path=onchain_csv,
        #                           shard_num=SHARD_NUM,
        #                           save_directory=save_directory)

        # plot_fee_comparison(method=METHOD, input_csv=input_csv,
        #                     onchain_csv=onchain_csv,
        #                     shard_num=SHARD_NUM,
        #                     save_directory=save_directory)
        #
        # plot_latency_vs_fee(onchain_csv, method=METHOD,
        #                     shard_num=SHARD_NUM,
        #                     save_directory=save_directory)
        #
        # plot_min_fees_per_block(method=METHOD,
        #                         csv_source=onchain_csv,
        #                         shard_num=SHARD_NUM,
        #                         save_directory=save_directory)
        #
        # analyze_transaction_sharding(METHOD, SHARD_NUM,
        #                              input_csv, onchain_cr_csv,
        #                              save_directory)
        #
        # generate_txpool_heatmap(METHOD, onchain_s_csv,
        #                         SHARD_NUM,
        #                         save_directory)

        #======现在先只画 tax 实验相关图
        plot_updated_tax_metrics(
            method=METHOD,
            shard_csv_dir=onchain_s_csv,
            shard_num=SHARD_NUM,
            save_directory=save_directory,
            alpha=0,
            beta=0
        )
