import m from "mithril";
import { MDCSnackbar } from "@material/snackbar";

import api from "api";

class User {
  is_logged_in: boolean;
  username!: string;
  notification!: string;
  snackbar!: MDCSnackbar;

  constructor() {
    api.token = localStorage.getItem("api_token");
    this.is_logged_in = !!api.token;
    if (this.is_logged_in) {
      this.getUser();
    }
  }

  login(token: string, username: string) {
    m.route.set("/");
    this.setToken(token);
    this.username = username;
    this.is_logged_in = true;
    this.postLogin();
  }

  logout = (redirect = "/") => {
    this.removeToken();
    window.location.href = redirect;
  };

  setToken(token: string) {
    localStorage.setItem("api_token", token);
    api.token = token;
    this.getUser();
  }

  removeToken() {
    localStorage.removeItem("api_token");
    api.token = null;
  }

  notify(message: string) {
    if (this.snackbar) {
      this.notification = message;
      this.snackbar.open();
      m.redraw();
    } else {
      // Hack to get around that fact that the Snackbar might not yet be rendered
      setTimeout(() => {
        this.notify(message);
      }, 100);
    }
  }

  postLogin() {
    this.notify("Logged in as " + this.username);
  }

  async getUser() {
    const response = await api.request("account");
    if (response.status == 401) {
      this.notify("Couldn't login. Please login again.");
      this.logout(m.route.get());
    }
    if (response.status == 200) {
      const is_just_logged_in = !this.username;
      this.username = response.body.username;
      if (is_just_logged_in) {
        this.postLogin();
      }
    }
  }
}

export default new User();
