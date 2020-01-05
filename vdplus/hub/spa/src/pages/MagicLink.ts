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
    api.token = token;
    const response = await api.request("account");
    user.login(token, response.body.username);
  }
}

export default new MagicLink();
