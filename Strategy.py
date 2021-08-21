import pandas as pd
import numpy as np
import warnings
from dateutil.parser import parse
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = 'Times New Roman'
import seaborn as sns
sns.set_style('whitegrid')

### 一、数据清洗

option_contract = pd.read_excel('option_contract.xlsx')

#### 获取期权合约数据，
# 剔除华泰柏瑞的信息，以及多余的列：'kind', 'name', 'exercise_type’

##剔除华泰柏瑞的信息

list_name = list(option_contract.name)

del_rows = [i for i in range(len(list_name)) if '华泰柏瑞' in list_name[i]]

option_contract_2 = option_contract.drop(del_rows)

##剔除多余的列：'kind', 'name', 'exercise_type’

option_contract_3 = option_contract_2.drop(['kind', 'name', 'exercise_type'] \
                                           , axis=1)

#### 插入一列，列名为'ttm'，代表存续期，以天为单位表示，
# 并保留存续期大于30天的期权合约

##插入一列，列名为'ttm'
option_contract_3['ttm'] = pd.Series(pd.to_datetime(option_contract_3['maturity_date']) \
                                     - pd.to_datetime(option_contract_3['list_date']))

##以天为单位表示
option_contract_3['ttm'] = option_contract_3['ttm']. \
    map(lambda x: x.days)

##保留存续期大于30天的期权合约
df = option_contract_3.drop(option_contract_3[option_contract_3.ttm <= 30].index)

#### 剔除到期日在2019年之后的期权合约，
# 并将剩下所有的maturity_date储存在一个新的容器里，

##生成一个新的DataFrame，储存到期日在2020年以前所有的期权合约
df_2 = df.drop(df[df.maturity_date >= '2020-1-1'].index)

##将剩下所有的maturity_date储存在一个新的序列maturity_date_cleaned里
maturity_date_cleaned = df_2.maturity_date.value_counts().sort_index().index

#### 生成一个新的options列表，列表中每个元素用以储存每个到期日的所有期权合约
options = [df_2[df_2.maturity_date == i] for i in maturity_date_cleaned]

#### 读取price_start和price end数据
# price_strat储存着每月第一个交易日所有期权的收盘价
# price_end储存着每月到期日所有期权的收盘价

price_start = pd.read_excel('price_start.xlsx')
price_end = pd.read_excel('price_end.xlsx')
##获得每月第一个交易日据具体日期
start_date = price_start.trade_date.value_counts().sort_index().index

# 把用int数字表示的日期转化为真正的日期形式
price_start['Date_True'] = pd.Series([parse(str(y)) for y in list(price_start.trade_date)])

##获得每月到期日具体日期
end_date = price_end.trade_date.value_counts().sort_index().index

# 把用int数字表示的日期转化为真正的日期形式
ls = pd.Series([parse(str(y)) for y in list(price_end.trade_date)])
price_end['Date_True'] = ls
####搜集每个price_strat和price_end中所有日期标的资产的收盘价，
# 整理成excel文件并读取

ETF_start = pd.read_excel('50ETF_Start.xlsx')
ETF_end = pd.read_excel('50ETF_End.xlsx')

### 二. 构建期权对冲交易策略

#### 找出第一月的第一个交易日的要卖出和买入的期权合约,以及对应的期权价格

i = 0
# 第一个交易日的要买入的期权合约
opt_buy = options[i + 1]
# 第一个交易日的要卖出的期权合约
opt_sell = options[i]
# 第一个交易日的期权价格数据
price_data = price_start[price_start['Date_True'] == (list(ETF_start['Date'])[i])]
##要买入的期权合约在第一个交易日的价格
opt_buy = pd.merge(opt_buy, price_data, on='ts_code', how='inner')
##要卖出的期权合约在第一个交易日的价格
opt_sell = pd.merge(opt_sell, price_data, on='ts_code', how='inner')

#### 找出第一月的到期日时次月到期合约的价格，并计算当月到期合约的收益

# 第i个月到期日期权价格
price_data = price_end[price_end['Date_True'] == (list(ETF_end['Date'])[i])]

# 把到期日表弟资产价格插入DataFrame opt_sell中
opt_sell['50ETF_price'] = list(ETF_end['close'])[i]

# 把opt_sell和price_data合并
opt_buy = pd.merge(opt_buy, price_data, on='ts_code', how='inner')

# 计算第一个交易日所出售期权在交易日的收益(对多头而言是收益，对我们（空头）而言为损失)
opt_sell['payoff'] = (opt_sell['call_put'] == 'C') * np.maximum(opt_sell['50ETF_price'] - \
                                                                opt_sell['exercise_price'], 0) + (
                                 opt_sell['call_put'] == 'P') * np.maximum( \
    opt_sell['exercise_price'] - opt_sell['50ETF_price'], 0)

#### 计算第一个交易日建仓的成本，到期日平仓的收益，以及最终的收益率

cost = opt_buy['close_x'].sum() + opt_sell['payoff'].sum()
payoff = opt_buy['close_y'].sum() + opt_sell['close'].sum()
returns = (payoff - cost) / cost

#### 使用for loop计算得到之后每月的策略收益率


returns = []

for i in range(len(ETF_start) - 1):
    # 第i月第一个交易日的要买入的期权合约
    opt_buy = options[i + 1]
    # 第i月第一个交易日的要卖出的期权合约
    opt_sell = options[i]
    # 第i月第一个交易日的期权价格数据
    price_data = price_start[price_start['Date_True'] == (list(ETF_start['Date'])[i])]
    ##要买入的期权合约在第i月第一个交易日的价格
    opt_buy = pd.merge(opt_buy, price_data, on='ts_code', how='inner')
    ##要卖出的期权合约在第i月第一个交易日的价格
    opt_sell = pd.merge(opt_sell, price_data, on='ts_code', how='inner')

    #### 找出第i月的到期日时次月到期合约的价格，并计算当月到期合约的收益

    # 第i个月到期日期权价格
    price_data = price_end[price_end['Date_True'] == (list(ETF_end['Date'])[i])]

    # 把到期日表弟资产价格插入DataFrame opt_sell中
    opt_sell['50ETF_price'] = list(ETF_end['close'])[i]

    # 把opt_sell和price_data合并
    opt_buy = pd.merge(opt_buy, price_data, on='ts_code', how='inner')

    # 计算第i月第一个交易日所出售期权在交易日的收益(对多头而言是收益，对我们（空头）而言为损失)
    opt_sell['payoff'] = (opt_sell['call_put'] == 'C') * np.maximum(opt_sell['50ETF_price'] - \
                                                                    opt_sell['exercise_price'], 0) + (
                                 opt_sell['call_put'] == 'P') * np.maximum( \
        opt_sell['exercise_price'] - opt_sell['50ETF_price'], 0)

    #### 计算第i月第一个交易日建仓的成本，到期日平仓的收益，以及最终的收益率

    cost = opt_buy['close_x'].sum() + opt_sell['payoff'].sum()
    payoff = opt_buy['close_y'].sum() + opt_sell['close'].sum()
    returns.append((payoff - cost) / cost)

#### 作图展示策略每期收益率，并与上证50ETF基金的同期收益率作比较

plt.figure(figsize=[15, 8])
plt.plot(maturity_date_cleaned[:-1], returns, color='royalblue', marker='o', \
         markersize=9)
fund_retuns = (ETF_end['close'] - ETF_start['close']) / ETF_start['close']
plt.plot(maturity_date_cleaned, fund_retuns, 'r', marker='o' \
         , markersize=9)
plt.legend(['Option strategy', '50ETF Fund'], fontsize=14)
plt.xlabel('Years', fontsize=16)
plt.ylabel('Return', fontsize=16)
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.grid()
plt.savefig('p1.svg')
plt.show()

#### 作图展示策略累计收益率，并与上证50ETF基金的累计收益率作比较

plt.figure(figsize=[14, 7])
plt.plot(maturity_date_cleaned[:-1], np.cumprod(1 + np.array(returns)), color='royalblue', marker='o', \
         markersize=9)
fund_retuns = (ETF_end['close'] - ETF_start['close']) / ETF_start['close']
plt.plot(maturity_date_cleaned, np.cumprod(1 + np.array(fund_retuns)), 'r', marker='o' \
         , markersize=9)
plt.legend(['Option strategy', '50ETF Fund'], fontsize=16)
plt.xlabel('Years', fontsize=16)
plt.ylabel('Return', fontsize=16)
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.grid()
plt.savefig('p2.svg')
plt.show()

### 四、稳健性检验

#### 作图展示策略每个建仓日的所有期权合约的S/K-1，并计算其绝对值的期望和标准差

option_spread = []
for i in range(len(ETF_start) - 1):
    opt_sell = options[i]
    opt_sell['50price'] = ETF_start['close'][i]
    ##把第i月所有要卖出期权的S/K-1放入列表option_spread中
    option_spread += (opt_sell['50price'] / opt_sell['exercise_price'] - 1).values \
        .tolist()
    ##把第i月所有要买入期权的S/K-1放入列表option_spread中
    opt_buy = options[i + 1]
    opt_buy['50price'] = ETF_start['close'][i]
    option_spread += (opt_buy['50price'] / opt_buy['exercise_price'] - 1).values \
        .tolist()

import seaborn as sns
from scipy.stats import norm

plt.figure(figsize=[16, 8])
sns.distplot(option_spread, fit=norm, color='royalblue')
plt.title('Difference between spot price and strike price', fontsize=20)
plt.grid()
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.savefig('p3.svg')
plt.show()


def ATM(eps):
    returns = []

    for i in range(len(ETF_start) - 1):
        # 第i月第一个交易日的要买入的期权合约
        opt_buy = options[i + 1]
        # 第i月第一个交易日的要卖出的期权合约
        opt_sell = options[i]
        # 第i月第一个交易日的期权价格数据
        price_data = price_start[price_start['Date_True'] == (list(ETF_start['Date'])[i])]
        ##要买入的期权合约在第i月第一个交易日的价格
        opt_buy = pd.merge(opt_buy, price_data, on='ts_code', how='inner')
        # opt_buy['50price']=list(ETF_start['close'])[i]
        opt_buy = opt_buy[abs(opt_buy['50price'] / opt_buy['exercise_price'] - 1) < eps]
        ##要卖出的期权合约在第i月第一个交易日的价格
        opt_sell = pd.merge(opt_sell, price_data, on='ts_code', how='inner')
        # opt_sell['50price']=list(ETF_start['close'])[i+1]
        opt_sell = opt_sell[abs(opt_sell['50price'] / opt_sell['exercise_price'] - 1) < eps]
        #### 找出第i月的到期日时次月到期合约的价格，并计算当月到期合约的收益

        # 第i个月到期日期权价格
        price_data = price_end[price_end['Date_True'] == (list(ETF_end['Date'])[i])]

        # 把到期日表弟资产价格插入DataFrame opt_sell中
        opt_sell['50ETF_price'] = list(ETF_end['close'])[i]

        # 把opt_sell和price_data合并
        opt_buy = pd.merge(opt_buy, price_data, on='ts_code', how='inner')

        # 计算第i月第一个交易日所出售期权在交易日的收益(对多头而言是收益，对我们（空头）而言为损失)
        opt_sell['payoff'] = (opt_sell['call_put'] == 'C') * np.maximum(opt_sell['50ETF_price'] - \
                                                                        opt_sell['exercise_price'], 0) + (
                                     opt_sell['call_put'] == 'P') * np.maximum( \
            opt_sell['exercise_price'] - opt_sell['50ETF_price'], 0)

        #### 计算第i月第一个交易日建仓的成本，到期日平仓的收益，以及最终的收益率

        cost = opt_buy['close_x'].sum() + opt_sell['payoff'].sum()
        payoff = opt_buy['close_y'].sum() + opt_sell['close'].sum()
        returns.append((payoff - cost) / cost)
    return returns


# 非平值期权

def non_ATM(eps):
    returns = []

    for i in range(len(ETF_start) - 1):
        # 第i月第一个交易日的要买入的期权合约
        opt_buy = options[i + 1]
        # 第i月第一个交易日的要卖出的期权合约
        opt_sell = options[i]
        # 第i月第一个交易日的期权价格数据
        price_data = price_start[price_start['Date_True'] == (list(ETF_start['Date'])[i])]
        ##要买入的期权合约在第i月第一个交易日的价格
        opt_buy = pd.merge(opt_buy, price_data, on='ts_code', how='inner')
        opt_buy = opt_buy[abs(opt_buy['50price'] / opt_buy['exercise_price'] - 1) > eps]
        ##要卖出的期权合约在第i月第一个交易日的价格
        opt_sell = pd.merge(opt_sell, price_data, on='ts_code', how='inner')
        opt_sell = opt_sell[abs(opt_sell['50price'] / opt_sell['exercise_price'] - 1) > eps]
        #### 找出第i月的到期日时次月到期合约的价格，并计算当月到期合约的收益

        # 第i个月到期日期权价格
        price_data = price_end[price_end['Date_True'] == (list(ETF_end['Date'])[i])]

        # 把到期日表弟资产价格插入DataFrame opt_sell中
        opt_sell['50ETF_price'] = list(ETF_end['close'])[i]

        # 把opt_sell和price_data合并
        opt_buy = pd.merge(opt_buy, price_data, on='ts_code', how='inner')

        # 计算第i月第一个交易日所出售期权在交易日的收益(对多头而言是收益，对我们（空头）而言为损失)
        opt_sell['payoff'] = (opt_sell['call_put'] == 'C') * np.maximum(opt_sell['50ETF_price'] - \
                                                                        opt_sell['exercise_price'], 0) + (
                                     opt_sell['call_put'] == 'P') * np.maximum( \
            opt_sell['exercise_price'] - opt_sell['50ETF_price'], 0)

        #### 计算第i月第一个交易日建仓的成本，到期日平仓的收益，以及最终的收益率

        cost = opt_buy['close_x'].sum() + opt_sell['payoff'].sum()
        payoff = opt_buy['close_y'].sum() + opt_sell['close'].sum()
        returns.append((payoff - cost) / cost)
    return returns


eps = np.arange(0.1, 0.01, -0.01)
atm = []
non_atm = []
for i in eps:
    atm.append(ATM(i))
    non_atm.append(non_ATM(i))

plt.figure(figsize=(20, 15))
for i in range(1, 10):
    plt.subplot(3, 3, i)
    plt.plot(maturity_date_cleaned[:-1], np.cumprod(1 + np.array(atm[i - 1])), color='royalblue', \
             linewidth=2)
    plt.plot(maturity_date_cleaned, np.cumprod(1 + np.array(fund_retuns)), 'r', \
             linewidth=2)
    plt.legend(['Option strategy', '50ETF Fund'], fontsize=16)
    plt.xlabel('EPS={}'.format(np.round(0.1 - (i - 1) * 0.01, 2)), fontsize=16)
    plt.ylabel('Return', fontsize=16)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.grid()
plt.savefig('p4.svg')
plt.show()
plt.figure(figsize=(20, 15))
for j in range(1, 10):
    plt.subplot(3, 3, j)
    plt.plot(maturity_date_cleaned[:-1], np.cumprod(1 + np.array(non_atm[j - 1])), color='royalblue', \
             linewidth=2)
    plt.plot(maturity_date_cleaned, np.cumprod(1 + np.array(fund_retuns)), 'r', \
             linewidth=2)
    plt.legend(['Option strategy', '50ETF Fund'], fontsize=16)

    plt.xlabel('EPS={}'.format(np.round(0.1 - (j - 1) * 0.01, 2)), fontsize=16)
    plt.ylabel('Return', fontsize=16)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.grid()
plt.savefig('p5.svg')
plt.show()
