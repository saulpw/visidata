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
      this.getUserData();
    }
  }

  getUserData() {
    this.getUser();
  }

  login(token: string, username: string) {
    this.setToken(token);
    this.username = username;
    this.is_logged_in = true;
    this.getUser();
    m.route.set("/");
  }

  logout = (redirect = "/") => {
    this.removeToken();
    window.location.href = redirect;
  };

  setToken(token: string) {
    localStorage.setItem("api_token", token);
    api.token = token;
    this.getUserData();
  }

  removeToken() {
    localStorage.removeItem("api_token");
    api.token = null;
  }

  notify(message: string) {
    this.notification = message;
    this.snackbar.open();
    m.redraw();
  }

  async getUser() {
    const response = await api.request("account");
    if (response.status == 401) {
      this.notify("Couldn't login. Please login again.");
      this.logout(m.route.get());
    }
    if (response.status == 200) {
      this.username = response.body.username;
    }
  }
}

export default new User();
