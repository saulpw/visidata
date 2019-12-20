import m from "mithril";

import mdc_top_app_bar from "@material/top-app-bar/mdc-top-app-bar.scss";
import mdc_linear_progress from "@material/linear-progress/mdc-linear-progress.scss";
import mdc_snackbar from "@material/snackbar/mdc-snackbar.scss";
import mdc_icon_button from "@material/icon-button/mdc-icon-button.scss";
import mdc_text_field from "@material/textfield/mdc-text-field.scss";
import mdc_text_field_helper from "@material/textfield/helper-text/mdc-text-field-helper-text.scss";
import mdc_button from "@material/button/mdc-button.scss";
import mdc_ripple from "@material/ripple/mdc-ripple.scss";

// When not using CSS modules production builds strip as much as they can. For some reason
// these need to be declared as variables in order to be included in the production CSS assets.
// @ts-ignore
const trigger_global_style_hack = [
  mdc_snackbar,
  mdc_linear_progress,
  mdc_top_app_bar,
  mdc_icon_button,
  mdc_text_field,
  mdc_text_field_helper,
  mdc_button,
  mdc_ripple
];

import "assets/main.scss";
import "xterm/css/xterm.css";

import Layout from "Layout";
import Home from "pages/Home";
import About from "pages/About";

function layout(component: any, classes = "") {
  return {
    render: function() {
      return m(Layout, { classes: classes }, m(component));
    }
  };
}

m.route.prefix = ""; // Prevents the use of hashbangs
m.route(document.body, "/", {
  "/": layout(Home),
  "/about": layout(About)
});
