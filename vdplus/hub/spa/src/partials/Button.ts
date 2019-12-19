import m from "mithril";

import { MDCRipple } from "@material/ripple";

interface Attrs {
  label: string;
  mattrs: m.Attributes;
}

export default class implements m.ClassComponent<Attrs> {
  view({ attrs }: m.Vnode<Attrs>) {
    return m(
      "button.mdc-button mdc-button--raised",
      attrs.mattrs,
      m("span.mdc-button__label", attrs.label)
    );
  }

  oncreate(vnode: m.VnodeDOM<Attrs>) {
    new MDCRipple(vnode.dom);
  }
}
