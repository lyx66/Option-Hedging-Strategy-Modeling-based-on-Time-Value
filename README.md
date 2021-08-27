## Option-Hedging-Strategy-Modeling-based-on-Time-Value
by ***Yingxin LIN***
### Introduce
- Python code for a trading strategy based on ***time value***, which is performed in the *SSE 50ETF* option market of China.
### Strategy
- I apply the time value of options as an indicator, to build a hedging strategy. 
- Specifically, I buy option contracts with large time value and sell option contracts with small time value.
- Every month, I construct portfolios on the first trading day, and then I close portfolios on the last trading day.
### Returns of the strategy
***Fig.1 Cumulative returns of the strategy (compared with SSE 50ETF)***

![p2](https://raw.githubusercontent.com/lyx66/limyingxin/5855d78f084d01df16617639ea49371b6b0273ed/p2.svg)
### Robust Test & Attribution of Strategy
- I divide options into fair value options and imaginary value options, and back-test the strategy on both of them respectively.
- The division is based on `S/K - 1` value (*i.g.* EPS) of each option.

***Fig.2 Price status of options in the sample period***

![p3](https://raw.githubusercontent.com/lyx66/limyingxin/5855d78f084d01df16617639ea49371b6b0273ed/p3.svg)
- Comparing *Fig.3* and *Fig.4* below, I find that the return of the strategy mainly comes from virtual options.

***Fig.3 Cumulative returns of strategy applied on the imaginary value options (with different EPS)***

![p4](https://raw.githubusercontent.com/lyx66/limyingxin/5855d78f084d01df16617639ea49371b6b0273ed/p4.svg)
***Fig.4 Cumulative returns of strategy applied on the imaginary virtual options (with different EPS)***

![p5](https://raw.githubusercontent.com/lyx66/limyingxin/5855d78f084d01df16617639ea49371b6b0273ed/p5.svg)
### Copyright notice
- AUTHOR: __*Yingxin LIN*__
- Company: *School of Finance, Central University of Finance and Economics* (CUFE)
- Contact: lyxurthebest@163.com or lyxurthebest@outlook.com
- The copyright belongs to __*Yingxin LIN*__ , 2021/08/22.
#### *Enjoy*（。＾▽＾) *! (...and extend/modify)* 😊
