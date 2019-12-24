import { Selector } from "testcafe";
import crypto from "crypto";

export default class {
  static DOMAIN() {
    const port = process.env.VD_PORT || "8000";
    return "http://localhost:" + port;
  }

  static uuid() {
    return crypto.randomBytes(10).toString("hex");
  }

  static async clickWithText(t, selector, text) {
    const element = await Selector(selector).withText(text);
    await t.click(element);
  }

  static async registerUser(t, username = "user") {}

  static async loginUser(t, username) {
    await t.typeText(".terminal", username).pressKey("enter");
    await this.waitForAPI(t);
    const data_username = await Selector("#user-overview").getAttribute(
      "data-username"
    );
    await t.expect(data_username).eql(username);
  }

  static async logout(t) {}

  static async waitForAPI() {
    await Selector(".mdc-linear-progress--closed")();
    await Selector(".mdc-linear-progress--closed")();
    await Selector(".mdc-linear-progress--closed")();
  }
}
