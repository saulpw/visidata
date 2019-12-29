import m from "mithril";

import user from "user";

export default class implements m.ClassComponent {
  view() {
    return [
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
    ];
  }
}
