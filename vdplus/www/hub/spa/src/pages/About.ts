import m from "mithril";

export default class implements m.ClassComponent {
  constructor() {}

  view() {
    return [m("h1", "All about the VisiData Demo"), m("p", "details...")];
  }
}
