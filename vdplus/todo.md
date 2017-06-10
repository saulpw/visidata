# TODO
- [ ] BUG: Owned planet [lacked information](bugImg/ships_absent.png) in the `P`lanet sheet. Still behaved like an owned planet (e.g. ships could be deployed form it.
- [ ] BUG: Occasionally, the opponent's colors will not show for [one of the players](bugImg/colors.png)
- [ ] FEATURE: Indicate the number of turns remaining until deployed ships arrive to a planet. Example: a `turns_till_marked` column on the queued orders sheet.
- [ ] BUG: In the starting player sheet, player presses `Enter` and the `ready` column remains `False`.
- [ ] BUG: `ratio = defend_stretch / attack_strength` can triggr a float division by zero error.
