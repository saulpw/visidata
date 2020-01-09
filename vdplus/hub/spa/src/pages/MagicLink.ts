import m from "mithril";

import user from "user";
import terminal from "lib/terminal/manager";

class MagicLink implements m.ClassComponent {
  view() {}

  oncreate() {
    this.login();
  }

  async login() {
    const token = m.route.param("token");
    if (token == "guest") {
      terminal.sendMagicLink("guest");
    }
    user.login(token);
  }
}

export default new MagicLink();
