import m from "mithril";

import api from "api";
import user from "user";

class MagicLink implements m.ClassComponent {
  view() {}

  oncreate() {
    this.login();
  }

  async login() {
    const token = m.route.param("token");
    user.login(token);
  }
}

export default new MagicLink();
