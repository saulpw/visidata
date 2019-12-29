import m from "mithril";

import { MDCTopAppBar } from "@material/top-app-bar";
import { MDCLinearProgress } from "@material/linear-progress";
import { MDCSnackbar } from "@material/snackbar";

import Utils from "Utils";
import bust from "material-design-icons-svg/paths/account.json";
import info from "material-design-icons-svg/paths/information.json";
import Icon from "partials/Icon";
import api from "api";
import user from "user";

import logo from "assets/images/vdlogo.png";

interface Attrs {
  classes: string;
}

export default class {
  progress_bar!: MDCLinearProgress;
  classes: string;

  constructor({ attrs }: m.CVnode<Attrs>) {
    this.classes = attrs.classes;
  }

  view(vnode: m.CVnode<Attrs>) {
    return [
      this.progressBar(),
      this.topBar(),
      this.accountMenu(),
      m(".layout", { className: this.classes }, [
        this.terminal(),
        vnode.children
      ]),
      this.notification(),
      this.footer(),
      this.terminalTextMirror()
    ];
  }

  oncreate() {
    const topAppBarElement = document.querySelector(".mdc-top-app-bar")!;
    this.progress_bar = new MDCLinearProgress(
      document.querySelector(".mdc-linear-progress")!
    );
    new MDCTopAppBar(topAppBarElement);
    user.snackbar = new MDCSnackbar(document.querySelector(".mdc-snackbar")!);
  }

  onupdate(vnode: m.CVnode<Attrs>) {
    if (this.classes != vnode.attrs.classes) {
      this.classes = vnode.attrs.classes;
      m.redraw();
    }
  }

  private topBar() {
    return m(
      "header.mdc-top-app-bar mdc-top-app-bar--fixed mdc-top-app-bar--dense",
      m(".mdc-top-app-bar__row", [this.topBarLeft(), this.topBarRight()])
    );
  }

  private topBarLeft() {
    return m(
      "section.mdc-top-app-bar__section.mdc-top-app-bar__section--align-start",
      [
        m(
          m.route.Link,
          {
            selector: "span",
            style: "cursor: pointer",
            className: "mdc-top-app-bar__title",
            href: "/"
          },
          [m("img#site-logo", { src: logo, width: 150 })]
        )
      ]
    );
  }

  private topBarRight() {
    let account_classes = "";
    let about_classes = "";
    if (m.route.get().includes("/account")) {
      account_classes = "account-page-is-active";
    }
    if (m.route.get().includes("/about")) {
      about_classes = "about-page-is-active";
    }
    return m(
      "section.mdc-top-app-bar__section.mdc-top-app-bar__section--align-end",
      [
        this.userOverview(),
        m(
          m.route.Link,
          {
            selector: "a",
            id: "account-button",
            className:
              "material-icons mdc-top-app-bar__action-item mdc-icon-button " +
              account_classes,
            href: user.is_logged_in ? "/account" : "/account/login"
          },
          m(Icon, { paths: bust })
        ),
        m(
          m.route.Link,
          {
            selector: "a",
            id: "about-page-button",
            className:
              "material-icons mdc-top-app-bar__action-item mdc-icon-button " +
              about_classes,
            href: "/about"
          },
          m(Icon, { paths: info })
        )
      ]
    );
  }

  private userOverview() {
    if (user.is_logged_in) {
      return m(
        "#user-overview",
        { "data-username": user.username },
        user.username
      );
    }
  }

  private accountMenu() {
    if (m.route.get().includes("/account") && !user.is_logged_in) {
      return m("#account", "Account DIV");
    }
  }

  private progressBar() {
    if (this.progress_bar) {
      if (api.is_active) {
        this.progress_bar.open();
        this.progress_bar.determinate = false;
      } else {
        this.progress_bar.close();
        this.progress_bar.determinate = true;
      }
    }
    return m(
      ".mdc-linear-progress mdc-linear-progress--closed",
      { role: "progressbar" },
      [
        m(".mdc-linear-progress__buffer"),
        m(
          ".mdc-linear-progress__bar mdc-linear-progress__primary-bar",
          m("span.mdc-linear-progress__bar-inner")
        ),
        m(
          ".mdc-linear-progress__bar mdc-linear-progress__secondary-bar",
          m("span.mdc-linear-progress__bar-inner")
        )
      ]
    );
  }

  private notification() {
    return m(
      ".mdc-snackbar",
      m(".mdc-snackbar__surface", [
        m(
          ".mdc-snackbar__label[role='status'][aria-live='polite']",
          user.notification
        )
      ])
    );
  }

  private footer() {
    return m("footer", [
      "Find out more on the ",
      m(m.route.Link, { href: "/about" }, "about"),
      " page"
    ]);
  }

  private terminal() {
    return [m("#terminal")];
  }

  // A placeholder to mirror the contents of the terminal so that tests can string match
  // on the contents of the terminal.
  private terminalTextMirror() {
    if (Utils.isTesting()) {
      return m("#dev-terminal-text.hidden");
    }
  }
}
