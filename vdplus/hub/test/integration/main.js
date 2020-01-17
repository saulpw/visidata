import { Selector } from "testcafe";

import Helper from "./Helper";

fixture("General tests")
  .page(Helper.DOMAIN())
  .beforeEach(async t => {
    await Helper.loginUser(t, "qwe1");
    await Helper.waitForAPI(t);
  });

test("Displays the terminal canvas", async t => {
  await t.expect(Selector("canvas.xterm-text-layer").exists).ok();
});

test("VisiData starts up", async t => {
  await t
    .wait(1000)
    .expect(Selector("#dev-terminal-text").textContent)
    .contains("VisiData");
});
