package main

import (
	"log"
	"math/big"
	"strconv"
	"time"
)

func Addr2Shard(addr Address) int {
	last8_addr := addr
	if len(last8_addr) > 8 {
		last8_addr = last8_addr[len(last8_addr)-8:]
	}
	num, err := strconv.ParseUint(last8_addr, 16, 64)
	if err != nil {
		log.Panic(err)
	}
	return int(num) % ShardNum
}

// transform data to transaction
func data2tx(data []string, nonce uint64) (*Transaction, bool) {
	if data[6] == "0" && data[7] == "0" && len(data[3]) > 16 && len(data[4]) > 16 && data[3] != data[4] {

		// 解析交易费用 value
		val, ok := new(big.Int).SetString(data[8], 10)
		if !ok {
			log.Panic("failed to parse tx value\n")
		}
		// 解析 gasPrice, gasUsed
		gasPrice, ok1 := new(big.Int).SetString(data[10], 10)
		if !ok1 {
			log.Panic("failed to parse tx gasPrice\n")
		}
		gasUsed, ok2 := new(big.Int).SetString(data[11], 10)
		if !ok2 {
			log.Panic("failed to parse tx gasUsed\n")
		}

		// new tx
		tx := NewTransaction(
			data[3][2:], // sender
			data[4][2:], // recipient
			val,         // value
			gasPrice,    // gasPrice
			gasUsed,     // gasUsed
			nonce,       // nonce
			time.Now(),  // timestamp
		)
		return tx, true
	}
	return &Transaction{}, false
}

func safeStr(v *big.Int) string {
	if v == nil {
		return "nil"
	}
	return v.String()
}

// GetFactor factor计算函数，根据当前偏离值和epsilon容忍区间决定
func GetFactor(deviation, epsilon *big.Int) *big.Float {
	absDev := new(big.Float).SetInt(new(big.Int).Abs(deviation))
	eps := new(big.Float).SetInt(epsilon)

	if eps.Cmp(big.NewFloat(0)) == 0 {
		return big.NewFloat(1.0)
	}

	factor := new(big.Float).Quo(absDev, eps)

	// 上下界
	minFactor := big.NewFloat(1)
	maxFactor := big.NewFloat(8.0)

	if factor.Cmp(minFactor) < 0 {
		return minFactor
	}
	if factor.Cmp(maxFactor) > 0 {
		return maxFactor
	}
	return factor
}
