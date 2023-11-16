SUMMARY_GOAL_PROMPT = """User:Analyze and summarize the following goals according to the specified format and requirements:

```json
{"name":"净利润达到去年的1.5倍 | Net Profit Reach 1.5 Times of Last Year","metric":"净利润｜Net Profit - Retail","target_value":"$5M","current_value":"$3.74M","sub_goals":[{"name":"提升总销售额 | Increase Total Sales","metric":"总销售额｜Total Sales - Retail","target_value":"$50M","current_value":"$34.67M","sub_goals":[{"name":"提升总交易量 | Increase Total Transactions","metric":"总交易量｜Total Transactions - Retail","target_value":"20K","current_value":"9994","sub_goals":[{"name":"提高连带率 | Improve Average Basket Size","metric":"连带率｜Average Basket Size - Retail","target_value":"3","current_value":"2","sub_goals":[],"historical_data":{"metas":[{"name":"ORDER_DATE","data_type":"DATE"},{"name":"Average Basket Size","data_type":"DOUBLE"}],"datas":[["2018-12-30","2.0"],["2018-12-29","3.25"],["2018-12-28","3.263157894736842"],["2018-12-27","2.5"],["2018-12-26","2.5"],["2018-12-25","3.0"],["2018-12-24","3.1875"]]}}],"historical_data":{"metas":[{"name":"Total Transactions","data_type":"BIGINT"}],"datas":[["9994"]]}}],"historical_data":{"metas":[{"name":"Total Sales","data_type":"DOUBLE"}],"datas":[["3.467849158328247E7"]]}},{"name":"提高净利润率 ｜ Improve Net Profit Margin","metric":"净利润率｜Net Profit Margin - Retail","target_value":"0.2","current_value":"0.15","sub_goals":[{"name":"提高客单利润 | Improve Average Transaction Revenue","metric":"客单利润｜Average Transaction Revenue - Retail","target_value":"400","current_value":"355.31","sub_goals":[],"historical_data":{"metas":[{"name":"ORDER_DATE","data_type":"DATE"},{"name":"Average Transaction Revenue","data_type":"DOUBLE"}],"datas":[["2018-12-30","355.31856427873885"],["2018-12-29","438.21582794189453"],["2018-12-28","370.85315704345703"],["2018-12-27","468.9849967956543"],["2018-12-26","299.8675003051758"],["2018-12-25","295.8552194678265"],["2018-12-24","397.4099998474121"]]}},{"name":"提高件单利润 | Improve Average Unit Revenue","metric":"件单利润｜Average Unit Revenue - Retail","target_value":"400","current_value":"177.65","sub_goals":[],"historical_data":{"metas":[{"name":"ORDER_DATE","data_type":"DATE"},{"name":"Average Unit Revenue","data_type":"DOUBLE"}],"datas":[["2018-12-30","177.65928213936942"],["2018-12-29","134.83563936673679"],["2018-12-28","113.6485481262207"],["2018-12-27","187.59399871826173"],["2018-12-26","119.9470001220703"],["2018-12-25","98.6184064892755"],["2018-12-24","124.67764701095282"]]}}],"historical_data":{"metas":[{"name":"ORDER_DATE","data_type":"DATE"},{"name":"Net Profit Margin","data_type":"DOUBLE"}],"datas":[["2018-12-30","0.15226701257885053"],["2018-12-29","0.12152101624133606"],["2018-12-28","0.1049904901683477"],["2018-12-27","0.14047313069012737"],["2018-12-26","0.12110243293542682"],["2018-12-25","0.08410361004465777"],["2018-12-24","0.09998325263566901"]]}}],"historical_data":{"metas":[{"name":"Net Profit","data_type":"DOUBLE"}],"datas":[["3747121.199651718"]]}}
```

It is necessary to distinguish between positive goals and negative goals in the analysis and summary process!!!

Answer Require:
- FORBIDDEN to modify or falsify any data, and the data provided in Goal json MUST be used for analysis and summary
- Output the report in MARKDOWN format.
- Use chinese answer


Answer Format: 
```markdown 
## 目标总结报告

### 整体进展分析
// Make an overall analysis and summary of goal "净利润达到去年的1.5倍 | Net Profit Reach 1.5 Times of Last Year" and its sub-goals ["提升总销售额 | Increase Total Sales", "提高净利润率 ｜ Improve Net Profit Margin"], and judge the development trend based on historical data
// Mark the goal use `[]` or `「」`, and make it bold with `**`.
// MARK the target and current values of all goals use use `<span style="font-weight: 600;">$VALUE</span>`

### 高风险目标分析
// ["提升总交易量 | Increase Total Transactions", "提高件单利润 | Improve Average Unit Revenue"] is high risk goals, conduct risk attribution analysis and development trend analysis on them.
// Mark the goal use `[]` or `「」`, and make it bold with `**`.
// Mark the target values use `<span style="font-weight: 600;">$VALUE</span>`.
// Mark the current values with `<span style="color: #c32929; font-weight: 600;">$VALUE</span>`.

### 相关建议
// Based on the goal data and the above analysis results, provide effective and executable recommendations to find development opportunities for the team or company.
// 需要基于下面的专家意见
// Expert advice is required based on the following: 
    你的建议需要考虑全面，分成三个方面提出：1.经济方面;2.团队方面;3.成本方面
```

Begin!"""
