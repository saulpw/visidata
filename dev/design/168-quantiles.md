# aggregator groups: quantiles

- q3/q4/q5/q10 indicate terciles/quartiles/quintiles/deciles
- q4 (for example) adds a group of aggregators: p25 p50 p75
- individual aggregators are deduped: `q5 q10` only adds 9 aggregators (same as just q10)
- aggregator groups are expanded at time of entry and may be removed individually
- setting `aggregators` via the ColumnsSheet to e.g. `q5` expands the group
- invalid aggregator input shows an error message
