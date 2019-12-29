import { Selector } from "testcafe";

import Helper from "./Helper";

fixture("Auth").page(Helper.DOMAIN());

test("Logs a user in and out", async t => {
  await Helper.loginUser(t, "test-login-out");
  await Helper.waitForAPI(t);
  await t.navigateTo(Helper.DOMAIN() + "/account");
  await Helper.clickWithText(t, "a", "Logout");
  await t.expect(Selector("#user-overview").exists).notOk();
  await t
    .expect(Selector("#dev-terminal-text").textContent)
    .notContains("saul.pw/VisiData");
});
