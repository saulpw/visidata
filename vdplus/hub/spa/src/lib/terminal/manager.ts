import Connection from "lib/terminal/websocket";
import { Terminal, IDisposable } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import UTF8Decoder from "lib/utf8_decode";

import Utils from "Utils";
import api from "api";
import user from "user";

export default class {
  PROMPT: string;
  elem!: HTMLElement;
  term!: Terminal;
  fitAddon!: FitAddon;
  decoder: UTF8Decoder;
  connection!: Connection;
  message!: HTMLElement;
  messageTimeout!: number;
  messageTimer!: number;
  naiveInteractionListener!: IDisposable;

  constructor() {
    this.PROMPT = "$ ";
    this.decoder = new UTF8Decoder();
    this.elem = document.getElementById("terminal")!;
    this.setupMessenger();
    this.startTerminal();
    this.startListeners();
  }

  startTerminal() {
    this.term = new Terminal();
    this.fitAddon = new FitAddon();
    this.term.loadAddon(this.fitAddon);
    this.term.open(this.elem!);
    this.term.setOption("fontSize", "18");
    this.term.focus();
    this.resizeHandler();
    this.welcomeMessage();
  }

  welcomeMessage() {
    this.term.writeln("Welcome to VisiData online");
    this.term.writeln(
      "Please enter an email address to login or 'guest' for a guest account"
    );
    this.term.write(this.PROMPT);
    this.naiveInteractionListener = this.term.onKey(
      this.naiveInteraction.bind(this)
    );
  }

  // This is only for simple tasks like logging in. For normal TTY interaction
  // all input is piped over a websocket for the backend to handle.
  naiveInteraction(e: { key: string; domEvent: KeyboardEvent }) {
    const ev = e.domEvent;
    const printable = !ev.altKey && !ev.ctrlKey && !ev.metaKey;
    if (ev.keyCode === 13) {
      this.term.writeln("");
      this.term.writeln("Loading...");
      const line = this.term.buffer.getLine(2)!.translateToString();
      const user = line.replace(this.PROMPT, "");
      this.login(user);
    } else if (ev.keyCode === 8) {
      // Do not delete the prompt
      if (this.term.buffer.cursorX > this.PROMPT.length) {
        this.term.write("\b \b");
      }
    } else if (printable) {
      this.term.write(e.key);
    }
  }

  async login(username: string) {
    const response = await api.request("auth?username=" + username);
    if (response.status == 200) {
      user.login(response.body.token, response.body.username);
      this.naiveInteractionListener.dispose();
      this.term.clear();
      this.connect();
    }
  }

  setupMessenger() {
    this.message = this.elem!.ownerDocument!.createElement("div");
    this.message.className = "xterm-overlay";
    this.messageTimeout = 2000;
  }

  resizeHandler() {
    this.fitAddon.fit();
    this.term.scrollToBottom();
    this.showMessage(
      String(this.term.cols) + "x" + String(this.term.rows),
      this.messageTimeout
    );
  }

  startListeners() {
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
    this.connection = new Connection(this);
  }

  info(): { columns: number; rows: number } {
    return { columns: this.term.cols, rows: this.term.rows };
  }

  output(data: string) {
    this.term.write(this.decoder.decode(data));
    if (Utils.isTesting()) {
      this.dumpBuffer();
    }
  }

  dumpBuffer() {
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

  removeMessage(): void {
    if (this.message.parentNode == this.elem) {
      this.elem.removeChild(this.message);
    }
  }

  setWindowTitle(_title: string) {
    // Noop for now
  }

  onInput(callback: (input: string) => void) {
    this.term.onKey(data => {
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

  deactivate(): void {
    // TODO: Stop listening to resize and data?
    this.term.blur();
  }

  reset(): void {
    this.removeMessage();
    this.term.clear();
  }

  close(): void {
    window.removeEventListener("resize", this.resizeHandler);
    this.term.dispose();
  }
}
