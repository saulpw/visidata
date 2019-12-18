import Connection from "websocket";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import UTF8Decoder from "lib/utf8_decode";

export default class {
  elem: HTMLElement;
  term: Terminal;
  resizeListener: () => void;
  decoder: UTF8Decoder;

  message: HTMLElement;
  messageTimeout: number;
  messageTimer!: number;

  constructor() {
    this.decoder = new UTF8Decoder();
    const elem = document.getElementById("terminal");
    const connection = new Connection(this);

    window.addEventListener("unload", () => {
      connection.close();
      this.close();
    });

    this.elem = elem!;
    this.term = new Terminal();
    const fitAddon = new FitAddon();
    this.term.loadAddon(fitAddon);

    this.message = elem!.ownerDocument!.createElement("div");
    this.message.className = "xterm-overlay";
    this.messageTimeout = 2000;

    this.resizeListener = () => {
      fitAddon.fit();
      this.term.scrollToBottom();
      this.showMessage(
        String(this.term.cols) + "x" + String(this.term.rows),
        this.messageTimeout
      );
    };

    this.term.open(elem!);
    this.term.setOption("fontSize", "18");
    this.term.focus();
    this.resizeListener();
    window.addEventListener("resize", () => {
      this.resizeListener();
    });
  }

  info(): { columns: number; rows: number } {
    return { columns: this.term.cols, rows: this.term.rows };
  }

  output(data: string) {
    this.term.write(this.decoder.decode(data));
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

  setWindowTitle(title: string) {
    document.title = title;
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
    window.removeEventListener("resize", this.resizeListener);
    this.term.dispose();
  }
}
