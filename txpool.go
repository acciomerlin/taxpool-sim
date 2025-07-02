package main

import (
	"math/big"
	"sort"
	"sync"
	"time"
)

type TxPool struct {
	TxQueue   []*Transaction            // transaction Queue
	RelayPool map[uint64][]*Transaction //designed for sharded blockchain, from Monoxide
	lock      sync.Mutex
	// The pending list is ignored
}

func NewTxPool() *TxPool {
	return &TxPool{
		TxQueue:   make([]*Transaction, 0),
		RelayPool: make(map[uint64][]*Transaction),
	}
}

// Add a transaction to the pool (consider the queue only)
func (txpool *TxPool) AddTx2Pool(tx *Transaction) {
	txpool.lock.Lock()
	defer txpool.lock.Unlock()
	if tx.Time.IsZero() {
		tx.Time = time.Now()
	}
	txpool.TxQueue = append(txpool.TxQueue, tx)
}

// Add a list of transactions to the pool
func (txpool *TxPool) AddTxs2Pool(txs []*Transaction) {
	txpool.lock.Lock()
	defer txpool.lock.Unlock()
	for _, tx := range txs {
		if tx.Time.IsZero() {
			tx.Time = time.Now()
		}
		txpool.TxQueue = append(txpool.TxQueue, tx)
	}
}

// add transactions into the pool head
func (txpool *TxPool) AddTxs2Pool_Head(tx []*Transaction) {
	txpool.lock.Lock()
	defer txpool.lock.Unlock()
	txpool.TxQueue = append(tx, txpool.TxQueue...)
}

// PackTxs Pack transactions for a proposal
func (txpool *TxPool) PackTxs(max_txs uint64, tp *TaxPool) []*Transaction {
	txpool.lock.Lock()
	defer txpool.lock.Unlock()

	// 分开加了税/补贴后为负和为正的交易，只打包收益为正的交易
	positiveTxs := make([]*Transaction, 0, len(txpool.TxQueue))
	negativeTxs := make([]*Transaction, 0) // 用于保留未选中交易
	for _, tx := range txpool.TxQueue {
		fee := new(big.Int).Mul(tx.GasPrice, tx.GasUsed)
		if isCtx(tx.Sender, tx.Recipient) {
			fee = new(big.Int).Div(fee, big.NewInt(2))
			fee.Add(fee, tp.Subsidy)
		} else {
			fee.Sub(fee, tp.Tax)
		}
		if fee.Sign() >= 0 {
			positiveTxs = append(positiveTxs, tx)
		} else {
			negativeTxs = append(negativeTxs, tx)
		}
	}

	// 按手续费排序
	sort.Slice(positiveTxs, func(i, j int) bool {
		priceI := new(big.Int).Mul(positiveTxs[i].GasPrice, positiveTxs[i].GasUsed)
		if isCtx(positiveTxs[i].Sender, positiveTxs[i].Recipient) {
			priceI.Div(priceI, big.NewInt(2))
			priceI.Add(priceI, tp.Subsidy)
		} else {
			priceI.Sub(priceI, tp.Tax)
		}

		priceJ := new(big.Int).Mul(positiveTxs[j].GasPrice, positiveTxs[j].GasUsed)
		if isCtx(positiveTxs[j].Sender, positiveTxs[j].Recipient) {
			priceJ.Div(priceJ, big.NewInt(2))
			priceJ.Add(priceJ, tp.Subsidy)
		} else {
			priceJ.Sub(priceJ, tp.Tax)
		}
		return priceI.Cmp(priceJ) > 0
	})

	// 最多只打包blocksize个交易
	if uint64(len(positiveTxs)) > max_txs {
		positiveTxs = positiveTxs[:max_txs]
	}

	remaining := make([]*Transaction, 0, len(txpool.TxQueue)-len(positiveTxs))
	packedMap := make(map[*Transaction]bool)
	for _, tx := range positiveTxs {
		packedMap[tx] = true
	}
	for _, tx := range txpool.TxQueue {
		if !packedMap[tx] {
			remaining = append(remaining, tx)
		}
	}

	// 恢复包括此次收益为负的交易的交易队列
	txpool.TxQueue = remaining

	// 返回此此次要打包的交易
	return positiveTxs
}

// txpool get locked
func (txpool *TxPool) GetLocked() {
	txpool.lock.Lock()
}

// txpool get unlocked
func (txpool *TxPool) GetUnlocked() {
	txpool.lock.Unlock()
}

// get the length of tx queue
func (txpool *TxPool) GetTxQueueLen() int {
	txpool.lock.Lock()
	defer txpool.lock.Unlock()
	return len(txpool.TxQueue)
}

// sort by 手续费(手续费/2 if relayTX)
func sortTxQueue(txQueue []*Transaction, tp *TaxPool) {
	sort.Slice(txQueue, func(i, j int) bool {
		priceI := new(big.Int).Mul(txQueue[i].GasPrice, txQueue[i].GasUsed)
		isCTX := isCtx(txQueue[i].Sender, txQueue[i].Recipient)
		if isCTX {
			priceI = new(big.Int).Div(priceI, big.NewInt(2))
			priceI.Add(priceI, tp.Subsidy)
		} else {
			priceI.Sub(priceI, tp.Tax)
		}

		priceJ := new(big.Int).Mul(txQueue[j].GasPrice, txQueue[j].GasUsed)
		isCTX = isCtx(txQueue[j].Sender, txQueue[j].Recipient)
		if isCTX {
			priceJ = new(big.Int).Div(priceJ, big.NewInt(2))
			priceJ.Add(priceJ, tp.Subsidy)
		} else {
			priceJ.Sub(priceJ, tp.Tax)
		}
		return priceI.Cmp(priceJ) > 0
	})
}
