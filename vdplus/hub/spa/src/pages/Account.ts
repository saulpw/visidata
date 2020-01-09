import m from "mithril";

import user from "user";
import api from "api";

export default class implements m.ClassComponent {
  view() {
    const magic_link =
      window.location.protocol +
      "//" +
      window.location.host +
      "/magic/" +
      api.token;
    return [
      m("div", [
        "Logged in as ",
        m("strong", user.username),
        " | ",
        m(
          "a",
          {
            href: "/",
            onclick: user.logout
          },
          "Logout"
        )
      ]),
      m("div", [
        "Share your session: ",
        m(
          "a",
          {
            href: magic_link
          },
          magic_link
        )
      ])
    ];
  }
}
