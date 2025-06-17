package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/gob"
	"fmt"
	"log"
	"math/big"
	"time"
)

type Address = string

type Transaction struct {
	Sender    Address
	Recipient Address
	Nonce     uint64
	Signature []byte // not implemented now.
	Value     *big.Int
	GasPrice  *big.Int // 手续费 = GasPrice*GasUsed
	GasUsed   *big.Int
	TxHash    []byte

	Time time.Time // TimeStamp the tx proposed.

	// 所属分片和区块编号
	ShardID     uint64
	BlockNumber uint64

	//是否为跨分片交易
	isCTX bool
}

// NewTransaction new a transaction
func NewTransaction(sender, recipient string, value, gasPrice, gasUsed *big.Int, nonce uint64, proposeTime time.Time) *Transaction {
	tx := &Transaction{
		Sender:    sender,
		Recipient: recipient,
		Value:     value,
		GasPrice:  gasPrice,
		GasUsed:   gasUsed,
		Nonce:     nonce,
		Time:      proposeTime,
	}
	hash := sha256.Sum256(tx.Encode())
	tx.TxHash = hash[:]

	//根据 sender 和 receiver 所在分片判断是否为跨分片交易
	tx.isCTX = isCtx(sender, recipient)

	return tx
}

func (tx *Transaction) PrintTx() {
	fmt.Printf("IsCTX: %t | Sender: %s | Recipient: %s | Value: %s | GasPrice: %s | GasUsed: %s | TxHash: %x\n",
		tx.isCTX,
		tx.Sender,
		tx.Recipient,
		tx.Value.String(),
		tx.GasPrice.String(),
		tx.GasUsed.String(),
		tx.TxHash,
	)
}

// Encode transaction for storing
func (tx *Transaction) Encode() []byte {
	var buff bytes.Buffer

	enc := gob.NewEncoder(&buff)
	err := enc.Encode(tx)
	if err != nil {
		log.Panic(err)
	}

	return buff.Bytes()
}

// Decode transaction
func DecodeTx(to_decode []byte) *Transaction {
	var tx Transaction

	decoder := gob.NewDecoder(bytes.NewReader(to_decode))
	err := decoder.Decode(&tx)
	if err != nil {
		log.Panic(err)
	}

	return &tx
}

func isCtx(sender Address, recipient Address) bool {
	ssid := uint64(Addr2Shard(sender))
	rsid := uint64(Addr2Shard(recipient))
	if ssid != rsid {
		return true
	} else {
		return false
	}
}
