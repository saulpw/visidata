import m from "mithril";

import Manager from "manager";

export default class implements m.ClassComponent {
  constructor() {}

  view() {
    return [m("#terminal")];
  }

  oncreate() {
    new Manager();
  }
}
