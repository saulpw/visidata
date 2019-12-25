import m from "mithril";

import Terminal from "lib/terminal/manager";

export default class implements m.ClassComponent {
  constructor() {}

  view() {
    return [m("#terminal")];
  }

  oncreate() {
    new Terminal();
  }
}
