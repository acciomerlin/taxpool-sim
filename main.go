package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"os"
	"time"
)

const (
	ShardNum   = 4
	txsCsvPath = "./filtered_transactions_11000k.csv"
	//dataTotalNum = 30207 // 100k txsCsv数据条数
	dataTotalNum  = 3607054 // 1100k txsCsv数据条数
	blockSize     = 2000
	globalBatchSz = 10000 // 从 CSV 一次拉 10000 笔
)

var logChan = make(chan string, 100000000)

type BlockStats struct {
	BlockHeight   int
	TxPoolSize    int
	TxCount       int
	Diff          string
	Balance       string
	DeltaBalance  string
	Tax           string
	Subsidy       string
	F_itx_min     string
	F_ctx_min     string
	P_itx_min     string
	P_ctx_min     string
	StartTime     time.Time
	EndTime       time.Time
	BlockInterval time.Duration // 记录与上一个区块的时间差
}

var statsChan = make(chan BlockStats, 10000)
var batchReq = make(chan struct{}, 1) // 打包协程按需请求

func main() {
	// 1) 启动日志输出协程
	f, err := os.Create("exp.log")
	if err != nil {
		log.Fatal(err)
	}
	logger := log.New(f, "", log.Ldate|log.Ltime)
	go func() {
		for msg := range logChan {
			logger.Println(msg)
		}
	}()
	// 2) 启动 CSV 写入协程
	go startCSVWriter()
	//=========================================================================
	// 2) 启动读 CSV 协程
	done := make(chan bool)
	csvTxPool := &TxPool{
		TxQueue:   make([]*Transaction, 0),
		RelayPool: make(map[uint64][]*Transaction),
	}

	go ReadTxsCSV_SegmentAndRepeat(csvTxPool, done)

	// 3) 触发第一次批量读取
	batchReq <- struct{}{}

	// 4) 启动打包协程
	GenerateBlock(csvTxPool, done)

	// 停止读取协程
	close(batchReq)

	// 确保 logChan 输出完后退出
	time.Sleep(3 * time.Second)
	close(logChan)
	close(statsChan)
	f.Close()
}

// ReadTxsCSV 读入交易 csv，读完停机
func ReadTxsCSV(txpool *TxPool, done chan<- bool) {
	start := time.Now()
	nowDataNum := 0

	txfile, err := os.Open(txsCsvPath)
	if err != nil {
		log.Panic(err)
	}
	defer txfile.Close()
	reader := csv.NewReader(txfile)

	// 设置定期打印的时间间隔
	logInterval := 2 * time.Second
	lastLogTime := time.Now()

	for {
		<-batchReq
		txpool.lock.Lock()
		for i := 0; i < globalBatchSz; i++ {
			data, err := reader.Read()
			if err == io.EOF || nowDataNum >= dataTotalNum {
				txpool.lock.Unlock()
				done <- true
				return
			}
			if err != nil {
				txpool.lock.Unlock()
				log.Panic(err)
			}
			if tx, ok := data2tx(data, uint64(nowDataNum)); ok {
				//tx.PrintTx()  //打印调试
				txpool.TxQueue = append(txpool.TxQueue, tx)
				nowDataNum++
			}

			// 每隔 logInterval 秒打印一次状态
			if time.Since(lastLogTime) >= logInterval {
				elapsed := time.Since(start).Seconds()
				progress := float64(nowDataNum) / float64(dataTotalNum) * 100
				//logChan <- fmt.Sprintf("📊 正在读取交易：已读取 %d / %d (%.2f%%)，耗时 %.2f 秒",
				//	nowDataNum, dataTotalNum, progress, elapsed)
				fmt.Printf("📊 正在读取交易：已读取 %d / %d (%.2f%%)，耗时 %.2f 秒\n",
					nowDataNum, dataTotalNum, progress, elapsed)
				lastLogTime = time.Now()
			}
		}
		txpool.lock.Unlock()
	}

	duration := time.Since(start)
	logChan <- fmt.Sprintf("ReadTxsCSV=> TxsCSV 读取完成，共 %d 笔交易，用时 %.2f 秒", nowDataNum, duration.Seconds())
	done <- true // 通知主线程“读取完毕”
}

var originalTxs []*Transaction // 存储原始10000笔交易

// 只读取一次CSV，然后循环复用
func ReadTxsCSV_repeat(txpool *TxPool, done chan<- bool) {
	//start := time.Now()
	nowDataNum := 0
	maxRepeatNum := 10000 // 循环使用这10000笔

	txfile, err := os.Open(txsCsvPath)
	if err != nil {
		log.Panic(err)
	}
	defer txfile.Close()
	reader := csv.NewReader(txfile)

	// ========== 一次性读取 10000 笔 ==========
	for i := 0; i < maxRepeatNum; i++ {
		data, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Panic(err)
		}
		if tx, ok := data2tx(data, uint64(nowDataNum)); ok {
			originalTxs = append(originalTxs, tx)
			nowDataNum++
		}
	}
	fmt.Println("✅ ReadTxsCSV => 首次读取 %d 笔交易成功，开始循环复用...", nowDataNum)

	// ========== 循环监听 batchReq，复制复用 ==========
	for {
		_, ok := <-batchReq
		if !ok {
			break
		}
		txpool.lock.Lock()
		for _, tx := range originalTxs {
			cloned := *tx            // 浅拷贝
			cloned.Time = time.Now() // 时间更新
			txpool.TxQueue = append(txpool.TxQueue, &cloned)
		}
		txpool.lock.Unlock()
	}
	fmt.Println("ReadTxsCSV => 停止复用交易")
	done <- true
}

func ReadTxsCSV_repeat10w211w(txpool *TxPool, done chan<- bool) {
	start := time.Now()
	nowDataNum := 0
	startRepeatIdx := 100000
	endRepeatIdx := 110000

	txfile, err := os.Open(txsCsvPath)
	if err != nil {
		log.Panic(err)
	}
	defer txfile.Close()
	reader := csv.NewReader(txfile)

	// 预分配空间
	initialTxs := make([]*Transaction, 0, startRepeatIdx)
	repeatTxs := make([]*Transaction, 0, endRepeatIdx-startRepeatIdx)

	// 一次性读入 0 - 11w
	for nowDataNum < endRepeatIdx {
		data, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Panic(err)
		}
		if tx, ok := data2tx(data, uint64(nowDataNum)); ok {
			if nowDataNum < startRepeatIdx {
				initialTxs = append(initialTxs, tx)
			} else {
				repeatTxs = append(repeatTxs, tx)
			}
			nowDataNum++
		}
	}

	// 注入 0 ~ 10w（仅一次）
	txpool.lock.Lock()
	for _, tx := range initialTxs {
		txpool.TxQueue = append(txpool.TxQueue, tx)
	}
	txpool.lock.Unlock()
	fmt.Printf("ReadTxsCSV => 已注入前 %d 笔交易\n", len(initialTxs))

	// 等待 batchReq，循环注入 10w ~ 11w
	fmt.Printf("ReadTxsCSV => 开始循环注入 %d 笔交易\n", len(repeatTxs))
	for {
		_, ok := <-batchReq
		if !ok {
			break
		}
		txpool.lock.Lock()
		for _, tx := range repeatTxs {
			cloned := *tx
			cloned.Time = time.Now()
			txpool.TxQueue = append(txpool.TxQueue, &cloned)
		}
		txpool.lock.Unlock()
	}
	fmt.Println("ReadTxsCSV => 停止注入交易")

	end := time.Now()
	duration := end.Sub(start)
	fmt.Printf("ReadTxsCSV => 总耗时 %.2f 秒，终止时间：%s\n", duration.Seconds(), end.Format("2006-01-02 15:04:05"))

	done <- true
}

func ReadTxsCSV_SegmentAndRepeat(txpool *TxPool, done chan<- bool) {
	start := time.Now()
	txfile, err := os.Open(txsCsvPath)
	if err != nil {
		log.Panic(err)
	}
	defer txfile.Close()
	reader := csv.NewReader(txfile)

	totalNeeded := 1100000 // 读取 0~11w
	allTxs := make([]*Transaction, 0, totalNeeded)

	// ===== 1. 一次性读入前 11w 交易 =====
	idx := 0
	for idx < totalNeeded {
		data, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Panic(err)
		}
		if tx, ok := data2tx(data, uint64(idx)); ok {
			allTxs = append(allTxs, tx)
			idx++
		}
	}
	fmt.Printf("✅ 已读取 %d 笔交易（0~11w），开始按需注入...\n", len(allTxs))

	// ✅ 正确设置循环使用的交易子集（10w ~ 11w）
	repeatTxs := allTxs[1000000:1010000]

	// ===== 2. 请求控制注入 =====
	batchCount := 0

	for {
		_, ok := <-batchReq
		if !ok {
			break
		}

		if batchCount < 100 {
			// 注入前10w
			startIdx := batchCount * 10000
			endIdx := (batchCount + 1) * 10000
			if endIdx > 1000000 {
				endIdx = 1000000
			}
			txpool.lock.Lock()
			for _, tx := range allTxs[startIdx:endIdx] {
				txpool.TxQueue = append(txpool.TxQueue, tx)
			}
			txpool.lock.Unlock()
			fmt.Printf("📦 第 %d 次注入：%d ~ %d\n", batchCount+1, startIdx, endIdx-1)
		} else {
			// 之后每次循环注入10w~11w
			txpool.lock.Lock()
			for _, tx := range repeatTxs {
				cloned := *tx
				cloned.Time = time.Now()
				txpool.TxQueue = append(txpool.TxQueue, &cloned)
			}
			txpool.lock.Unlock()
			fmt.Printf("🔁 循环注入第 %d 次 10w~11w 交易（共 %d）\n", batchCount-9, len(repeatTxs))
		}
		batchCount++
	}

	fmt.Println("🚪 读取线程结束，已完成全部注入")
	done <- true

	duration := time.Since(start)
	fmt.Printf("ReadTxsCSV => 总耗时 %.2f 秒，终止时间：%s\n", duration.Seconds(), time.Now().Format("2006-01-02 15:04:05"))
}

// GenerateBlock_version_timeSleep 负责打包交易并输出记录,用 time sleep控制出块间隔版本
func GenerateBlock(csvPool *TxPool, done <-chan bool) {
	shardQ := NewTxPool()
	prevEnd := time.Time{}

	taxpool := NewTaxPool()
	blockNum := 1
	csvFinished := false

	for !csvFinished {
		// 如果 shardQ 不足 blockSize，先从 csvPool 拉入满足 shard 的
		//if len(shardQ.TxQueue) < blockSize {
		if true {
			// 批量过滤
			filtered := make([]*Transaction, 0)
			csvPool.lock.Lock()
			for _, tx := range csvPool.TxQueue {
				if Addr2Shard(tx.Sender) == 0 {
					filtered = append(filtered, tx)
				}
			}
			csvPool.TxQueue = csvPool.TxQueue[:0] // 清空 CSV 池
			csvPool.lock.Unlock()
			shardQ.AddTxs2Pool(filtered)

			// 发请求再拉下一批
			select {
			case batchReq <- struct{}{}:
			default:
			}
		}

		// 如果池中没一笔，且 CSV 完了，就退出
		if len(shardQ.TxQueue) == 0 && csvFinished {
			return
		}

		// —— 等待 CSV 完毕标识
		select {
		case <-done:
			csvFinished = true
		default:
		}

		if shardQ.GetTxQueueLen() == 0 {
			time.Sleep(10 * time.Millisecond)
			continue
		}

		logChan <- fmt.Sprintf("GenerateBlock=>  Block %d - 当前交易池大小：%d\n", blockNum, shardQ.GetTxQueueLen())

		// 记录打包时间
		start := time.Now()

		// 每次打包最多 blockSize 个交易
		txs := shardQ.PackTxs(blockSize, taxpool)
		// 给每个交易赋值shardID & BlockNumber，这里假装是4分片中的0分片
		for _, tx := range txs {
			tx.ShardID = 0 // 可视情况分配
			tx.BlockNumber = uint64(blockNum)
		}

		// 更新 taxpool
		//taxpool.UpdateDiffAndBalance(txs) //看 f_itx_min和f_ctx_min是否符合预期调试
		taxpool.UpdateTaxAndSubsidy_v3_4(txs)

		end := time.Now()
		interval := time.Duration(0)
		if !prevEnd.IsZero() {
			interval = start.Sub(prevEnd)
		}
		prevEnd = end

		statsChan <- BlockStats{
			BlockHeight:   blockNum,
			TxPoolSize:    len(shardQ.TxQueue),
			TxCount:       len(txs),
			Diff:          taxpool.Diff_withsign.String(),
			Balance:       taxpool.Balance.String(),
			DeltaBalance:  taxpool.DeltaBalance.String(),
			Tax:           taxpool.Tax.String(),
			Subsidy:       taxpool.Subsidy.String(),
			F_itx_min:     safeStr(taxpool.F_itx_min),
			F_ctx_min:     safeStr(taxpool.F_ctx_min),
			P_itx_min:     safeStr(taxpool.P_itx_min),
			P_ctx_min:     safeStr(taxpool.P_ctx_min),
			StartTime:     start,
			EndTime:       end,
			BlockInterval: interval,
		}

		//fmt.Printf("完成区块 %d 打包：共 %d 笔交易\n", blockNum, len(txs))
		logChan <- fmt.Sprintf("GenerateBlock=> 完成区块 %d 打包：共 %d 笔交易", blockNum, len(txs))

		blockNum++
		//batchReq <- struct{}{}

		if blockNum > 600 {
			fmt.Println("达到 600 个区块，终止出块")
			break
		}
	}
}

func startCSVWriter() {
	outputDir := "outputCSV"
	timestamp := time.Now().Format("20060102_150405")
	filename := fmt.Sprintf("%s/shard_%s.csv", outputDir, timestamp)
	err := os.MkdirAll(outputDir, os.ModePerm)
	if err != nil {
		log.Fatalf("创建目录失败: %v", err)
	}
	file, err := os.Create(filename)
	if err != nil {
		log.Fatalf("无法创建 CSV 文件: %v", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	header := []string{
		"Block Height", "TxPool Size", "# of all Txs",
		"Diff", "Balance", "DeltaBalance", "Tax", "Subsidy", "f_itx_min", "f_ctx_min",
		"P_itx_min", "P_ctx_min", "StartTime", "EndTime", "BlockInterval(ms)",
	}
	writer.Write(header)

	for stat := range statsChan {
		row := []string{
			fmt.Sprint(stat.BlockHeight),
			fmt.Sprint(stat.TxPoolSize),
			fmt.Sprint(stat.TxCount),
			//fmt.Sprint(stat.Relay1Count),
			//fmt.Sprint(stat.Relay2Count),
			stat.Diff,
			stat.Balance,
			stat.DeltaBalance,
			stat.Tax,
			stat.Subsidy,
			stat.F_itx_min,
			stat.F_ctx_min,
			stat.P_itx_min,
			stat.P_ctx_min,
		}
		writer.Write(row)
	}
}
