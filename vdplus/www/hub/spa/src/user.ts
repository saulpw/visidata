import m from "mithril";
import { MDCSnackbar } from "@material/snackbar";
import terminal from "lib/terminal/manager";

import api from "api";

class User {
  is_logged_in: boolean;
  username!: string;
  idle_timeout!: number;
  time_remaining!: number;
  notification!: string;
  snackbar!: MDCSnackbar;

  constructor() {
    api.token = localStorage.getItem("api_token");
    this.is_logged_in = !!api.token;
    if (this.is_logged_in) {
      this.getUser();
    }
  }

  login(token: string) {
    m.route.set("/");
    this.setToken(token);
    this.is_logged_in = true;
    this.getUser();
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

  private postLogin() {
    this.notify("Logged in as " + this.username);
    this.startIdleTimer();
  }

  private startIdleTimer() {
    this.time_remaining = this.idle_timeout;
    setInterval(() => {
      m.redraw();
      if (this.idle_timeout != 0) {
        this.time_remaining -= 1;
      }
      if (this.time_remaining == 0) {
        terminal.logout();
        this.idle_timeout = 0;
      }
    }, 1000);
  }

  resetTimer() {
    this.time_remaining = this.idle_timeout + 1;
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
      this.idle_timeout = response.body.idle_timeout;
      if (is_just_logged_in) {
        this.postLogin();
      }
    }
  }
}

export default new User();
