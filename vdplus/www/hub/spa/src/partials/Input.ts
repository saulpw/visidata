import m from "mithril";

import { MDCTextField } from "@material/textfield";
import { MDCTextFieldHelperText } from "@material/textfield/helper-text";

export default class implements m.ClassComponent<InputAttrs> {
  attrs: InputAttrs;
  is_valid!: boolean;
  mdc_field!: MDCTextField;
  mdc_helper_text!: MDCTextFieldHelperText;

  constructor({ attrs }: m.CVnode<InputAttrs>) {
    this.attrs = attrs;
  }

  view() {
    return [
      m(".mdc-text-field", [
        m("input.mdc-text-field__input", {
          "aria-controls": this.attrs.id,
          "aria-describedby": this.attrs.id,
          type: this.attrs.kind,
          id: this.attrs.id,
          ...this.attrs.mattrs
        }),
        m("label.mdc-floating-label", { for: this.attrs.id }, this.attrs.label)
      ]),
      m(
        ".mdc-text-field-helper-line",
        m(
          ".mdc-text-field-helper-text mdc-text-field-helper-text--validation-msg",
          { id: this.attrs.id, "aria-hidden": "true" },
          this.attrs.helper_text
        )
      )
    ];
  }

  oncreate(vnode: m.VnodeDOM<InputAttrs>) {
    this.mdc_field = new MDCTextField(vnode.dom);
    this.mdc_helper_text = new MDCTextFieldHelperText(vnode.dom);
    if (this.is_valid != undefined) {
      this.mdc_field.useNativeValidation = false;
    }
  }
}
