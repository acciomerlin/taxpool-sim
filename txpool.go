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

// Pack transactions for a proposal
func (txpool *TxPool) PackTxs(max_txs uint64, tp *TaxPool) []*Transaction {
	txpool.lock.Lock()
	defer txpool.lock.Unlock()

	// sort by 手续费
	sortTxQueue(txpool.TxQueue, tp)

	txNum := max_txs
	if uint64(len(txpool.TxQueue)) < txNum {
		txNum = uint64(len(txpool.TxQueue))
	}

	txs_Packed := txpool.TxQueue[:txNum]
	txpool.TxQueue = txpool.TxQueue[txNum:]
	return txs_Packed
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
