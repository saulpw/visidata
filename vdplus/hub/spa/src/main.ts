import m from "mithril";

import "@material/top-app-bar/mdc-top-app-bar.scss";
import "@material/linear-progress/mdc-linear-progress.scss";
import "@material/snackbar/mdc-snackbar.scss";
import "@material/icon-button/mdc-icon-button.scss";
import "@material/textfield/mdc-text-field.scss";
import "@material/textfield/helper-text/mdc-text-field-helper-text.scss";
import "@material/button/mdc-button.scss";
import "@material/ripple/mdc-ripple.scss";
import "@material/elevation/mdc-elevation.scss";
import "assets/main.scss";
import "xterm/css/xterm.css";

import Layout from "Layout";
import Home from "pages/Home";
import About from "pages/About";
import Manager from "manager";

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
