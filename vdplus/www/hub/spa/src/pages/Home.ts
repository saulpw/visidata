import m from "mithril";

import terminal from "lib/terminal/manager";
import user from "user";

export default class implements m.ClassComponent {
  view() {}

  oncreate() {
    terminal.show();

    if (!terminal.term) {
      terminal.start();
    }

    if (user.is_logged_in && !terminal.is_logged_in) {
      terminal.login();
    }
  }

  onremove() {
    terminal.hide();
  }
}
