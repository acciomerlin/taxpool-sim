package main

import (
	"fmt"
	"math/big"
	"strings"
)

// const Delta2 = 1000000000000000  // for taxpool balance用不同步长方案
const Delta = 100000000000                    // 10^11
const EpsilonDelay = 10000000000000           // 10^13
const EpsilonBalance = 100000000000000000     // 10^17
const EpsilonDeltaBalance = 10000000000000000 // 10^16

type TaxPool struct {
	Tax             *big.Int // 最新出块区块理想情况下 itx 被收的税，被用作下一高度区块打包时 itx 实际被收的税
	Subsidy         *big.Int // 最新出块区块理想情况下 ctx 被发的补贴，被用作下一高度区块打包时 ctx 实际被发的补贴
	TotalTaxNum     *big.Int // n_itx 最新出块区块累计被收税 itx 数目
	TotalSubsidyNum *big.Int // n_ctx 最新出块区块累计被发补贴 ctx 数目
	TotalTax        *big.Int // 此分片 itx 在最新出块高度时的累计被收税
	TotalSubsidy    *big.Int // 此分片 ctx 在最新出块高度时的累计被发补贴
	TotalTax_i      *big.Int // 最新出块区块 itx 累计被收税
	TotalSubsidy_i  *big.Int // 最新出块区块 ctx 累计被发补贴
	Diff            *big.Int // ｜最新出块区块最低ctx手续费 - 最新出块区块最低itx手续费｜
	Diff_withsign   *big.Int // 最新出块区块最低ctx手续费 - 最新出块区块最低itx手续费
	Balance         *big.Int // TotalTax - TotalSubsidy, 不用绝对值，这样可根据正负设计最近一段时间要偏向发补贴还是收税
	DeltaBalance    *big.Int // 最新出块区块 TotalTax_i - TotalSubsidy_i, 也=Balance(i)-Balance(i+1)
	F_itx_min       *big.Int // 最新出块区块最低itx手续费
	F_ctx_min       *big.Int // 最新出块区块最低ctx手续费
	P_itx_min       *big.Int // 最新出块区块最低itx收益 = F_itx_min - tax
	P_ctx_min       *big.Int // 最新出块区块最低itx收益 = F_ctx_min/2 + subsidy
}

func NewTaxPool() *TaxPool {
	return &TaxPool{
		Tax:             big.NewInt(0),
		Subsidy:         big.NewInt(0),
		TotalTaxNum:     big.NewInt(0),
		TotalSubsidyNum: big.NewInt(0),
		TotalTax:        big.NewInt(0),
		TotalSubsidy:    big.NewInt(0),
		TotalTax_i:      big.NewInt(0),
		TotalSubsidy_i:  big.NewInt(0),
		Diff:            big.NewInt(0),
		Diff_withsign:   big.NewInt(0),
		Balance:         big.NewInt(0),
		DeltaBalance:    big.NewInt(0),
		F_itx_min:       big.NewInt(0),
		F_ctx_min:       big.NewInt(0),
		P_itx_min:       big.NewInt(0),
		P_ctx_min:       big.NewInt(0),
	}
}

func (tp *TaxPool) ToString() string {
	var sb strings.Builder

	sb.WriteString("----------- TaxPool 状态 -----------\n")
	sb.WriteString(fmt.Sprintf("Tax:             %s\n", tp.Tax.String()))
	sb.WriteString(fmt.Sprintf("Subsidy:         %s\n", tp.Subsidy.String()))
	sb.WriteString(fmt.Sprintf("TotalTaxNum:     %s\n", tp.TotalTaxNum.String()))
	sb.WriteString(fmt.Sprintf("TotalSubsidyNum: %s\n", tp.TotalSubsidyNum.String()))
	sb.WriteString(fmt.Sprintf("TotalTax:        %s\n", tp.TotalTax.String()))
	sb.WriteString(fmt.Sprintf("TotalSubsidy:    %s\n", tp.TotalSubsidy.String()))
	sb.WriteString(fmt.Sprintf("TotalTax_i:      %s\n", tp.TotalTax_i.String()))
	sb.WriteString(fmt.Sprintf("TotalSubsidy_i:  %s\n", tp.TotalSubsidy_i.String()))
	sb.WriteString(fmt.Sprintf("Diff:            %s\n", tp.Diff.String()))
	sb.WriteString(fmt.Sprintf("Diff_withsign:   %s\n", tp.Diff_withsign.String()))
	sb.WriteString(fmt.Sprintf("Balance:         %s\n", tp.Balance.String()))
	sb.WriteString(fmt.Sprintf("DeltaBalance:    %s\n", tp.DeltaBalance.String()))

	if tp.F_itx_min != nil {
		sb.WriteString(fmt.Sprintf("F_itx_min:       %s\n", tp.F_itx_min.String()))
	} else {
		sb.WriteString("F_itx_min:       nil\n")
	}

	if tp.F_ctx_min != nil {
		sb.WriteString(fmt.Sprintf("F_ctx_min:       %s\n", tp.F_ctx_min.String()))
	} else {
		sb.WriteString("F_ctx_min:       nil\n")
	}

	if tp.P_itx_min != nil {
		sb.WriteString(fmt.Sprintf("P_itx_min:       %s\n", tp.P_itx_min.String()))
	} else {
		sb.WriteString("P_itx_min:       nil\n")
	}

	if tp.P_ctx_min != nil {
		sb.WriteString(fmt.Sprintf("P_ctx_min:       %s\n", tp.P_ctx_min.String()))
	} else {
		sb.WriteString("P_ctx_min:       nil\n")
	}

	sb.WriteString("------------------------------------")

	return sb.String()
}

func (tp *TaxPool) UpdateDiffAndBalance(txs []*Transaction) {
	var minITXFee, minCTXFee *big.Int
	firstITX, firstCTX := true, true

	tp.TotalSubsidy_i = big.NewInt(0)
	tp.TotalSubsidyNum = big.NewInt(0)
	tp.TotalTax_i = big.NewInt(0)
	tp.TotalTaxNum = big.NewInt(0)
	tp.DeltaBalance = big.NewInt(0)

	prevBalance := new(big.Int).Set(tp.Balance)

	for _, tx := range txs {
		if tx == nil {
			continue
		}
		fee := new(big.Int).Mul(tx.GasPrice, tx.GasUsed)
		isCTX := isCtx(tx.Sender, tx.Recipient)

		if isCTX {
			tp.TotalSubsidyNum.Add(tp.TotalSubsidyNum, big.NewInt(1))
			tp.TotalSubsidy.Add(tp.TotalSubsidy, tp.Subsidy)
			tp.TotalSubsidy_i.Add(tp.TotalSubsidy_i, tp.Subsidy)
			// tp.Balance.Sub(tp.Balance, tp.Subsidy)
			tp.DeltaBalance.Sub(tp.DeltaBalance, tp.Subsidy)
			if firstCTX || (minCTXFee != nil && fee.Cmp(minCTXFee) < 0) {
				minCTXFee = new(big.Int).Set(fee)
				firstCTX = false
			}
		} else {
			tp.TotalTaxNum.Add(tp.TotalTaxNum, big.NewInt(1))
			tp.TotalTax.Add(tp.TotalTax, tp.Tax)
			tp.TotalTax_i.Add(tp.TotalTax_i, tp.Tax)
			// tp.Balance.Add(tp.Balance, tp.Tax)
			tp.DeltaBalance.Add(tp.DeltaBalance, tp.Tax)
			if firstITX || (minITXFee != nil && fee.Cmp(minITXFee) < 0) {
				minITXFee = new(big.Int).Set(fee)
				firstITX = false
			}
		}

	}

	tp.Balance = new(big.Int).Add(prevBalance, tp.DeltaBalance)

	// 防止v2计算分子有0
	if tp.TotalSubsidyNum.Cmp(big.NewInt(0)) == 0 {
		tp.TotalSubsidyNum.Add(tp.TotalSubsidyNum, big.NewInt(1))
	}
	if tp.TotalTaxNum.Cmp(big.NewInt(0)) == 0 {
		tp.TotalTaxNum.Add(tp.TotalTaxNum, big.NewInt(1))
	}

	if minCTXFee == nil && minITXFee == nil {
		// 两个都为 nil，不合法，赋值为 0 避免崩溃
		tp.F_itx_min = big.NewInt(0)
		tp.F_ctx_min = big.NewInt(0)
		tp.Diff_withsign = big.NewInt(0)
		tp.Diff = big.NewInt(0)
		logChan <- fmt.Sprintf("UpdateDiffAndBalance=> !Both minCTXFee and minITXFee are nil. Assigned zero to prevent crash.")
		return
	}

	if minITXFee == nil {
		tp.F_itx_min = nil
		tp.F_ctx_min = minCTXFee
		if len(txs) < blockSize {
			tp.Diff_withsign = big.NewInt(0)
			tp.Diff = big.NewInt(0)
		} else {
			tp.Diff_withsign = new(big.Int).Neg(minCTXFee)
			tp.Diff = new(big.Int).Abs(minCTXFee)
		}
		return
	}

	if minCTXFee == nil {
		tp.F_itx_min = minITXFee
		tp.F_ctx_min = nil
		if len(txs) < blockSize {
			tp.Diff_withsign = big.NewInt(0)
			tp.Diff = big.NewInt(0)
		} else {
			tp.Diff_withsign = new(big.Int).Set(minITXFee)
			tp.Diff = new(big.Int).Abs(minITXFee)
		}
		return
	}

	// 两个都不为 nil
	tp.F_itx_min = minITXFee
	tp.F_ctx_min = minCTXFee
	diff := new(big.Int).Sub(minCTXFee, minITXFee)
	tp.Diff_withsign = diff
	tp.Diff = new(big.Int).Abs(diff)

}

func (tp *TaxPool) UpdateTaxAndSubsidy_v1(a float64, b float64, txs []*Transaction) {
	tp.UpdateDiffAndBalance(txs)
	if tp.DeltaBalance.Sign() <= 0 { // 补贴大于税收时，补贴发少一点(*b)，税收多一点(*a)
		DiffFloat := new(big.Float).SetInt(tp.Diff) // 把 *big.Int 转为 *big.Float
		DiffFloat.Mul(DiffFloat, big.NewFloat(a))
		DiffFloat.Int(tp.Tax)                      // 转回整数，小数部分会被截断
		DiffFloat = new(big.Float).SetInt(tp.Diff) // 把 *big.Int 转为 *big.Float
		DiffFloat.Mul(DiffFloat, big.NewFloat(b))
		DiffFloat.Int(tp.Subsidy)
	} else {
		DiffFloat := new(big.Float).SetInt(tp.Diff) // 把 *big.Int 转为 *big.Float
		DiffFloat.Mul(DiffFloat, big.NewFloat(b))
		DiffFloat.Int(tp.Tax)                      // 转回整数，小数部分会被截断
		DiffFloat = new(big.Float).SetInt(tp.Diff) // 把 *big.Int 转为 *big.Float
		DiffFloat.Mul(DiffFloat, big.NewFloat(a))
		DiffFloat.Int(tp.Subsidy)
	}

}

func (tp *TaxPool) UpdateTaxAndSubsidy_v2(txs []*Transaction) {
	tp.UpdateDiffAndBalance(txs)

	// 正确计算 P_ctx_min
	halfFctx := new(big.Int).Div(tp.F_ctx_min, big.NewInt(2))
	tp.P_ctx_min = new(big.Int).Add(halfFctx, tp.Subsidy)

	// 正确计算 P_itx_min
	tp.P_itx_min = new(big.Int).Sub(tp.F_itx_min, tp.Tax)

	// 开始推导 s 和 t：
	if tp.TotalTaxNum.Sign() > 0 && tp.TotalSubsidyNum.Sign() > 0 {
		p_ctx := new(big.Float).SetInt(tp.P_ctx_min)
		p_itx := new(big.Float).SetInt(tp.P_itx_min)

		nItxFloat := new(big.Float).SetInt(tp.TotalTaxNum)
		nCtxFloat := new(big.Float).SetInt(tp.TotalSubsidyNum)

		// numerator = 2 * P_ctx - P_itx
		num := new(big.Float).Mul(big.NewFloat(2), p_ctx)
		num.Sub(num, p_itx)

		// s = numerator / (2 + n_ctx/n_itx)
		denS := new(big.Float).Quo(nCtxFloat, nItxFloat)
		denS.Add(denS, big.NewFloat(2))
		sFloat := new(big.Float).Quo(num, denS)

		// t = numerator / (2n_itx/n_ctx + 1)
		denT := new(big.Float).Quo(nItxFloat, nCtxFloat)
		denT.Mul(denT, big.NewFloat(2))
		denT.Add(denT, big.NewFloat(1))
		tFloat := new(big.Float).Quo(num, denT)

		// 转回 big.Int，截断小数
		tp.Subsidy = new(big.Int)
		tp.Tax = new(big.Int)
		sFloat.Int(tp.Subsidy)
		tFloat.Int(tp.Tax)
	}
}

func (tp *TaxPool) UpdateTaxAndSubsidy_v3(txs []*Transaction) {
	tp.UpdateDiffAndBalance(txs)

	// 检查是否满足平衡条件
	// ε_d 和 ε_b 是判断“是否近似为0”的上下限（可配置）
	epsilon1 := big.NewInt(EpsilonDelay)
	epsilon2 := big.NewInt(EpsilonBalance)

	// 判断时延平衡是否在 [-ε, ε] 区间内
	delayBalanced := tp.Diff_withsign.Cmp(epsilon1) <= 0 && tp.Diff_withsign.Cmp(new(big.Int).Neg(epsilon1)) >= 0

	// 判断税池平衡是否在 [-ε', ε'] 区间内
	taxpoolBalanced := tp.DeltaBalance.Cmp(epsilon2) <= 0 && tp.DeltaBalance.Cmp(new(big.Int).Neg(epsilon2)) >= 0

	// n_itx 和 n_ctx
	nItx := new(big.Int).Set(tp.TotalTaxNum)
	nCtx := new(big.Int).Set(tp.TotalSubsidyNum)

	// 防止除0
	if nItx.Sign() == 0 {
		nItx = big.NewInt(1)
	}
	if nCtx.Sign() == 0 {
		nCtx = big.NewInt(1)
	}

	// 用于调整的 delta
	delta := big.NewInt(Delta)

	// 时延平衡，税池平衡
	if delayBalanced && taxpoolBalanced {
		// 不做调整
		return
	}

	// 时延不平衡，税池平衡 + 都不平衡，优先处理时延
	if !delayBalanced {
		if tp.Diff_withsign.Cmp(big.NewInt(0)) > 0 {
			// ctx 时延高，Tax + Δ*(n-1), Subsidy + Δ
			tp.Tax.Add(tp.Tax, new(big.Int).Mul(delta, big.NewInt(int64(ShardNum-1))))
			tp.Subsidy.Add(tp.Subsidy, delta)
		} else {
			// itx 时延高，Tax - Δ*(n-1), Subsidy - Δ
			tp.Tax.Sub(tp.Tax, new(big.Int).Mul(delta, big.NewInt(int64(ShardNum-1))))
			tp.Subsidy.Sub(tp.Subsidy, delta)
		}

		return
	} else if !taxpoolBalanced {
		{ // 时延平衡，税池不平衡
			if tp.DeltaBalance.Sign() > 0 {
				// taxpool 增长：Tax - Δ、subsidy +Δ
				tp.Tax.Sub(tp.Tax, delta)
				tp.Subsidy.Add(tp.Subsidy, delta)
			} else {
				// taxpool 减少：Tax +Δ 、subsidy -Δ
				tp.Tax.Add(tp.Tax, delta)
				tp.Subsidy.Sub(tp.Subsidy, delta)
			}
			return
		}
	}
}

func (tp *TaxPool) UpdateTaxAndSubsidy_v3_2(txs []*Transaction) {
	tp.UpdateDiffAndBalance(txs)

	// 容忍区间
	epsilon1 := big.NewInt(EpsilonDelay)
	epsilon2 := big.NewInt(EpsilonBalance)

	// 判断是否平衡
	delayBalanced := tp.Diff_withsign.Cmp(epsilon1) <= 0 && tp.Diff_withsign.Cmp(new(big.Int).Neg(epsilon1)) >= 0
	//taxpoolBalanced := tp.DeltaBalance.Cmp(epsilon2) <= 0 && tp.DeltaBalance.Cmp(new(big.Int).Neg(epsilon2)) >= 0
	taxpoolBalanced := tp.Balance.Cmp(epsilon2) <= 0 && tp.Balance.Cmp(new(big.Int).Neg(epsilon2)) >= 0 // 用balance判断

	// 原始步长
	baseDelta := big.NewInt(Delta)
	//baseDelta2 := big.NewInt(Delta2)

	// 平衡就不调整
	if delayBalanced && taxpoolBalanced {
		return
	}

	// 动态计算扩大因子（偏离/容忍区间）
	// 返回 *big.Float 支持小数因子
	getFactor := func(deviation, epsilon *big.Int) *big.Float {
		absDev := new(big.Float).SetInt(new(big.Int).Abs(deviation))
		eps := new(big.Float).SetInt(epsilon)

		if eps.Cmp(big.NewFloat(0)) == 0 {
			return big.NewFloat(1.0)
		}

		factor := new(big.Float).Quo(absDev, eps)

		// 设置小数上下界
		minFactor := big.NewFloat(0.1)
		maxFactor := big.NewFloat(8.0)

		if factor.Cmp(minFactor) < 0 {
			return minFactor
		}
		if factor.Cmp(maxFactor) > 0 {
			return maxFactor
		}
		return factor
	}

	if !delayBalanced {
		// 时延偏离因子
		//logChan <- fmt.Sprintf("UpdateTaxAndSubsidy_v3_2, Diff_with_sign: %s", tp.Diff_withsign.String())
		delayFactor := getFactor(tp.Diff_withsign, epsilon1)

		// 计算有效的 Δ,因为可能是小数，所以用 big.Float 计算，再转回 big.Int
		baseDeltaFloat := new(big.Float).SetInt(baseDelta)
		effectiveDelta := new(big.Float).Mul(baseDeltaFloat, delayFactor)
		effectiveDeltaInt := new(big.Int)
		effectiveDelta.Int(effectiveDeltaInt)

		if tp.Diff_withsign.Sign() > 0 {
			// ctx 时延高：Tax + Δ*(n-1), Subsidy + Δ
			tp.Tax.Add(tp.Tax, new(big.Int).Mul(effectiveDeltaInt, big.NewInt(int64(ShardNum-1))))
			tp.Subsidy.Add(tp.Subsidy, effectiveDeltaInt)
		} else {
			// itx 时延高：Tax - Δ*(n-1), Subsidy - Δ
			tp.Tax.Sub(tp.Tax, new(big.Int).Mul(effectiveDeltaInt, big.NewInt(int64(ShardNum-1))))
			tp.Subsidy.Sub(tp.Subsidy, effectiveDeltaInt)
		}
		return
	} else if !taxpoolBalanced {
		// 税池偏离因子
		balanceFactor := getFactor(tp.Balance, epsilon2)

		// 计算有效的 Δ,因为可能是小数，所以用 big.Float 计算，再转回 big.Int
		baseDeltaFloat := new(big.Float).SetInt(baseDelta)
		effectiveDelta := new(big.Float).Mul(baseDeltaFloat, balanceFactor)
		effectiveDeltaInt := new(big.Int)
		effectiveDelta.Int(effectiveDeltaInt)

		if tp.Balance.Sign() > 0 {
			// 税池增长：Tax - Δ、Subsidy + Δ
			tp.Tax.Sub(tp.Tax, effectiveDeltaInt)
			tp.Subsidy.Add(tp.Subsidy, effectiveDeltaInt)
		} else {
			// 税池减少：Tax + Δ、Subsidy - Δ
			tp.Tax.Add(tp.Tax, effectiveDeltaInt)
			tp.Subsidy.Sub(tp.Subsidy, effectiveDeltaInt)
		}
		return
	}
}

func (tp *TaxPool) UpdateTaxAndSubsidy_v3_3(txs []*Transaction) {
	tp.UpdateDiffAndBalance(txs)

	// 容忍区间
	epsilonDelay := big.NewInt(EpsilonDelay)
	epsilonBalance := big.NewInt(EpsilonBalance)

	// 判断时延平衡
	delayBalanced := tp.Diff_withsign.Cmp(epsilonDelay) <= 0 && tp.Diff_withsign.Cmp(new(big.Int).Neg(epsilonDelay)) >= 0
	// 判断balance平衡
	taxpoolBalanced := tp.Balance.Cmp(epsilonBalance) <= 0 && tp.Balance.Cmp(new(big.Int).Neg(epsilonBalance)) >= 0

	// 税收和补贴调整步长，此版本时延平衡和税池平衡调整步长统一
	delta := big.NewInt(Delta)

	// 时延平衡 && 税池平衡，不调整税收或者补贴返回
	if delayBalanced && taxpoolBalanced {
		return
	}

	// 优先调整时延平衡
	if !delayBalanced {
		delayFactor := GetFactor(tp.Diff_withsign, epsilonDelay)

		// 计算 factor * delta,因可能是小数，所以先用 big.Float 计算再转回 big.Int
		baseDeltaFloat := new(big.Float).SetInt(delta)
		effectiveDelta := new(big.Float).Mul(baseDeltaFloat, delayFactor)
		effectiveDeltaInt := new(big.Int)
		effectiveDelta.Int(effectiveDeltaInt)

		if tp.Diff_withsign.Sign() > 0 {
			// ctx 时延高，ctx 竞争不过itx，加税：Tax + factor_delay * delta * (n-1), Subsidy + factor * delta
			tp.Tax.Add(tp.Tax, new(big.Int).Mul(effectiveDeltaInt, big.NewInt(int64(ShardNum-1))))
			tp.Subsidy.Add(tp.Subsidy, effectiveDeltaInt)
		} else {
			// itx 时延高，itx竞争不过ctx，减税：Tax - factor_delay * delta * (n-1), Subsidy - factor * delta
			tp.Tax.Sub(tp.Tax, new(big.Int).Mul(effectiveDeltaInt, big.NewInt(int64(ShardNum-1))))
			tp.Subsidy.Sub(tp.Subsidy, effectiveDeltaInt)
		}
		return
	} else if !taxpoolBalanced {
		// 税池偏离因子
		balanceFactor := GetFactor(tp.Balance, epsilonBalance)

		baseDeltaFloat := new(big.Float).SetInt(delta)
		effectiveDelta := new(big.Float).Mul(baseDeltaFloat, balanceFactor)
		effectiveDeltaInt := new(big.Int)
		effectiveDelta.Int(effectiveDeltaInt)

		if tp.Balance.Sign() > 0 {
			// 税池增长，税收多了：Tax - factor_balance * delta、Subsidy + factor_balance * delta
			tp.Tax.Sub(tp.Tax, effectiveDeltaInt)
			tp.Subsidy.Add(tp.Subsidy, effectiveDeltaInt)
		} else {
			// 税池减少，税收少了：Tax + factor_balance * delta、Subsidy - factor_balance * delta
			tp.Tax.Add(tp.Tax, effectiveDeltaInt)
			tp.Subsidy.Sub(tp.Subsidy, effectiveDeltaInt)
		}
		return
	}
}

func (tp *TaxPool) UpdateTaxAndSubsidy_v3_4(txs []*Transaction) {
	tp.UpdateDiffAndBalance(txs)

	// 3个epsilon 容忍区间
	epsilonDelay := big.NewInt(EpsilonDelay)
	epsilonBalance := big.NewInt(EpsilonBalance)
	epsilonDeltaBalance := big.NewInt(EpsilonDeltaBalance)

	// 调整 tax & subsidy 步长
	delta := big.NewInt(Delta)

	// 判断时延平衡
	delayBalanced := tp.Diff_withsign.Cmp(epsilonDelay) <= 0 && tp.Diff_withsign.Cmp(new(big.Int).Neg(epsilonDelay)) >= 0

	// 优先调整时延平衡
	if !delayBalanced {
		delayFactor := GetFactor(tp.Diff_withsign, epsilonDelay)

		// 计算 factor * delta,因可能是小数，所以先用 big.Float 计算再转回 big.Int
		baseDeltaFloat := new(big.Float).SetInt(delta)
		effectiveDelta := new(big.Float).Mul(baseDeltaFloat, delayFactor)
		effectiveDeltaInt := new(big.Int)
		effectiveDelta.Int(effectiveDeltaInt)

		if tp.Diff_withsign.Sign() > 0 {
			// ctx 时延高，ctx 竞争不过itx，加税：Tax + factor_delay * delta * (n-1), Subsidy + factor * delta
			tp.Tax.Add(tp.Tax, new(big.Int).Mul(effectiveDeltaInt, big.NewInt(int64(ShardNum-1))))
			tp.Subsidy.Add(tp.Subsidy, effectiveDeltaInt)
		} else {
			// itx 时延高，itx竞争不过ctx，减税：Tax - factor_delay * delta * (n-1), Subsidy - factor * delta
			tp.Tax.Sub(tp.Tax, new(big.Int).Mul(effectiveDeltaInt, big.NewInt(int64(ShardNum-1))))
			tp.Subsidy.Sub(tp.Subsidy, effectiveDeltaInt)
		}
		return
	}

	// 先计算 factor_balance&deltabalance避免重复计算
	balancePlusDeltabalance := new(big.Int).Add(tp.Balance, tp.DeltaBalance)
	epsilonSum := new(big.Int).Add(epsilonBalance, epsilonDeltaBalance)
	balanceAndDeltaBalanceFactor := GetFactor(balancePlusDeltabalance, epsilonSum)
	baseDeltaFloat := new(big.Float).SetInt(delta)
	effectiveDelta := new(big.Float).Mul(baseDeltaFloat, balanceAndDeltaBalanceFactor)
	effectiveDeltaInt := new(big.Int)
	effectiveDelta.Int(effectiveDeltaInt)

	// 然后再调税池平衡
	if tp.Balance.Cmp(big.NewInt(0)) <= 0 { // balance < 0
		if tp.DeltaBalance.Cmp(big.NewInt(0)) <= 0 {
			// 表格蓝色区域：+tax -subsidy
			tp.Tax.Add(tp.Tax, effectiveDeltaInt)
			tp.Subsidy.Sub(tp.Subsidy, effectiveDeltaInt)
		} else {
			if tp.Balance.Cmp(new(big.Int).Neg(epsilonBalance)) < 0 {
				// 表格蓝色区域：+tax -subsidy
				tp.Tax.Add(tp.Tax, effectiveDeltaInt)
				tp.Subsidy.Sub(tp.Subsidy, effectiveDeltaInt)
			} else {
				if tp.DeltaBalance.Cmp(epsilonDeltaBalance) <= 0 {
					// 表格黄色区域：tax, subsidy 不变
				} else {
					// 表格红色区域：-tax +subsidy
					tp.Tax.Sub(tp.Tax, effectiveDeltaInt)
					tp.Subsidy.Add(tp.Subsidy, effectiveDeltaInt)
				}
			}
		}
	} else { // balance > 0
		if tp.DeltaBalance.Cmp(big.NewInt(0)) > 0 {
			// 表格红色区域：-tax +subsidy
			tp.Tax.Sub(tp.Tax, effectiveDeltaInt)
			tp.Subsidy.Add(tp.Subsidy, effectiveDeltaInt)
		} else {
			if tp.Balance.Cmp(epsilonBalance) > 0 {
				// 表格红色区域：-tax +subsidy
				tp.Tax.Sub(tp.Tax, effectiveDeltaInt)
				tp.Subsidy.Add(tp.Subsidy, effectiveDeltaInt)
			} else {
				if tp.DeltaBalance.Cmp(new(big.Int).Neg(epsilonDeltaBalance)) > 0 {
					// 表格黄色区域：tax, subsidy 不变
				} else {
					// 表格蓝色区域：+tax -subsidy
					tp.Tax.Add(tp.Tax, effectiveDeltaInt)
					tp.Subsidy.Sub(tp.Subsidy, effectiveDeltaInt)
				}
			}
		}
	}

}
