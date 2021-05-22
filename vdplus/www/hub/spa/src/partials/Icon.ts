import m from "mithril";

interface Attrs {
  paths: string;
}

export default class implements m.ClassComponent<Attrs> {
  paths: string;

  constructor({ attrs }: m.CVnode<Attrs>) {
    this.paths = attrs.paths;
  }

  view() {
    return m("svg", { viewBox: "0 0 22 22" }, m("path", { d: this.paths }));
  }

  onupdate({ attrs }: m.CVnode<Attrs>) {
    if (this.paths != attrs.paths) {
      this.paths = attrs.paths;
      m.redraw();
    }
  }
}
