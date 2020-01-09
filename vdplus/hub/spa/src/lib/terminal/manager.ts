import Connection from "lib/terminal/websocket";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import UTF8Decoder from "lib/utf8_decode";

import Utils from "Utils";
import api from "api";
import user from "user";

class Manager {
  term!: Terminal;
  is_logged_in: boolean;
  private message!: HTMLElement;
  private PROMPT: string;
  private elem!: HTMLElement;
  private fitAddon!: FitAddon;
  private decoder: UTF8Decoder;
  private connection!: Connection;
  private messageTimeout!: number;
  private messageTimer!: number;

  constructor() {
    this.PROMPT = "$ ";
    this.decoder = new UTF8Decoder();
    this.is_logged_in = false;
  }

  start() {
    this.getElementRoot();
    this.setupMessenger();
    this.term = new Terminal();
    this.fitAddon = new FitAddon();
    this.term.loadAddon(this.fitAddon);
    this.term.open(this.elem!);
    this.term.setOption("fontSize", "18");
    this.term.focus();
    this.resizeHandler();
    this.welcomeMessage();
    this.startListeners();
  }

  private getElementRoot() {
    this.elem = document.getElementById("terminal")!;
  }

  private welcomeMessage() {
    if (window.location.pathname.includes("magic/") || user.is_logged_in) {
      return;
    }
    this.term.writeln("Welcome to VisiData online");
    this.term.writeln(
      "Please enter an email address to login or 'guest' for a guest account"
    );
    this.term.write(this.PROMPT);
    this.term.onKey(this.naiveInteraction.bind(this));
  }

  // This is only for simple tasks like logging in. For normal TTY interaction
  // all input is piped over a websocket for the backend to handle.
  private naiveInteraction(e: { key: string; domEvent: KeyboardEvent }) {
    const ev = e.domEvent;
    const printable = !ev.altKey && !ev.ctrlKey && !ev.metaKey;
    if (ev.keyCode === 13) {
      this.term.writeln("");
      this.term.writeln("Loading...");
      const line = this.term.buffer.getLine(2)!.translateToString();
      const email = line.replace(this.PROMPT, "").trim();
      this.sendMagicLink(email);
    } else if (ev.keyCode === 8) {
      // Do not delete the prompt
      if (this.term.buffer.cursorX > this.PROMPT.length) {
        this.term.write("\b \b");
      }
    } else if (printable) {
      this.term.write(e.key);
    }
  }

  async sendMagicLink(email: string) {
    email = email.trim();
    const response = await api.request("auth?email=" + email);
    if (response.status == 200) {
      if (email == "guest") {
        window.location.href = "/magic/" + response.body.token;
      } else {
        this.term.writeln(
          "A Magic Login Link has been sent to your email address."
        );
      }
    }
    if (window.location.host.includes("localhost")) {
      this.term.writeln("");
      this.term.writeln(
        "'localhost' detected. Auto redirecting to Magic Link..."
      );
      this.term.writeln(response.body.token);
      this.redirectToMagicLink(response.body.token);
    }
  }

  private redirectToMagicLink(magic_link: string) {
    const link = new URL(magic_link);
    const delay = ENV.mode == "development" ? 3000 : 0;
    setTimeout(() => {
      window.location.href = link.pathname;
    }, delay);
  }

  login() {
    this.term.clear();
    this.connect();
    // TODO: Better detection of having logged in
    this.is_logged_in = true;
  }

  logout() {
    this.connection.close();
    this.term.clear();
    this.is_logged_in = false;
    this.term.writeln("Your VisiData session has ended due to inactivity.");
    this.term.writeln("Please reload the page to start a new session.");
  }

  private setupMessenger() {
    this.message = this.elem!.ownerDocument!.createElement("div");
    this.message.className = "xterm-overlay";
    this.messageTimeout = 2000;
  }

  private resizeHandler() {
    this.fitAddon.fit();
    this.term.scrollToBottom();
    this.showMessage(
      String(this.term.cols) + "x" + String(this.term.rows),
      this.messageTimeout
    );
  }

  private startListeners() {
    window.addEventListener("resize", () => {
      this.resizeHandler();
    });
    window.addEventListener("unload", () => {
      if (this.connection) {
        this.connection.close();
      }
      this.close();
    });
  }

  connect() {
    this.connection = new Connection();
  }

  info(): { columns: number; rows: number } {
    return { columns: this.term.cols, rows: this.term.rows };
  }

  output(data: string) {
    this.term.write(this.decoder.decode(data));
    if (Utils.isTesting()) {
      setTimeout(() => {
        this.dumpBuffer();
      }, 100);
    }
  }

  private dumpBuffer() {
    let buffer = "";
    for (let i = 0; i < this.term.rows; i++) {
      buffer += this.term.buffer.getLine(i)!.translateToString() + "\n";
    }
    document.getElementById("dev-terminal-text")!.innerHTML = buffer;
  }

  showMessage(message: string, timeout: number) {
    this.message.textContent = message;
    this.elem.appendChild(this.message);

    if (this.messageTimer) {
      clearTimeout(this.messageTimer);
    }
    if (timeout > 0) {
      this.messageTimer = window.setTimeout(() => {
        this.elem.removeChild(this.message);
      }, timeout);
    }
  }

  removeMessage() {
    if (this.message.parentNode == this.elem) {
      this.elem.removeChild(this.message);
    }
  }

  setWindowTitle(_title: string) {
    // Noop for now
  }

  onInput(callback: (input: string) => void) {
    this.term.onKey(data => {
      user.resetTimer();
      callback(data.key);
    });
  }

  onResize(callback: (colmuns: number, rows: number) => void) {
    this.term.onResize(data => {
      callback(data.cols, data.rows);
    });
  }

  setPreferences(option: { key: string; value: string }) {
    this.term.setOption(option.key, option.value);
  }

  deactivate() {
    // TODO: Stop listening to resize and data?
    this.term.blur();
  }

  reset() {
    this.removeMessage();
    this.term.clear();
  }

  close() {
    window.removeEventListener("resize", this.resizeHandler);
    this.term.dispose();
    this.is_logged_in = false;
  }

  hide() {
    if (!this.elem) {
      this.getElementRoot();
    }
    this.elem.style.display = "none";
  }

  show() {
    if (!this.elem) {
      this.getElementRoot();
    }
    this.elem.style.display = "block";
  }
}

export default new Manager();
