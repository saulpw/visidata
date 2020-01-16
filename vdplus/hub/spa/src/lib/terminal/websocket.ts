import terminal from "lib/terminal/manager";
import api from "api";
import user from "user";

// These enumerations are specific to gotty's protocol:
// https://github.com/yudai/gotty
//
//const msgInputUnknown = "0";
//const msgUnknownOutput = "0";
const msgInput = "1";
const msgPing = "2";
const msgResizeTerminal = "3";
const msgOutput = "1";
const msgPong = "2";
const msgSetWindowTitle = "3";
const msgSetPreferences = "4";
//const msgSetReconnect = "5";
// This is specific to VisiData authentication
const msgAuth = "6";

export default class {
  socket!: WebSocket;
  ping_timer!: number;

  constructor() {
    this.setup();
  }

  private url() {
    let domain: string;
    const httpsEnabled = window.location.protocol == "https:";
    if (ENV.API_SERVER == "/") {
      domain = window.location.host;
    } else {
      domain = ENV.API_SERVER;
    }
    const url = (httpsEnabled ? "wss://" : "ws://") + domain + "/ws";
    return url;
  }

  setup() {
    this.socket = new WebSocket(this.url());
    this.onOpen();
    this.onReceive();
    this.onClose();
  }

  close() {
    this.socket.close();
  }

  isOpen(): boolean {
    return (
      this.socket.readyState == WebSocket.CONNECTING ||
      this.socket.readyState == WebSocket.OPEN
    );
  }

  private onOpen() {
    this.socket.onopen = _event => {
      terminal.removeMessage()

      const termInfo = terminal.info();

      this.socket.send(api.token || "");

      this.socket.send(
        // JSON specific to gotty's protocol
        JSON.stringify({
          Arguments: window.location.search,
          AuthToken: ""
        })
      );

      const resizeHandler = (colmuns: number, rows: number) => {
        this.socket.send(
          msgResizeTerminal +
            JSON.stringify({
              columns: colmuns,
              rows: rows
            })
        );
      };

      terminal.onResize(resizeHandler);
      resizeHandler(termInfo.columns, termInfo.rows);

      terminal.onInput((input: string) => {
        this.socket.send(msgInput + input);
      });

      this.ping_timer = window.setInterval(() => {
        this.socket.send(msgPing);
      }, 30 * 1000);
    };
  }

  private onReceive() {
    this.socket.onmessage = event => {
      const data = event.data;
      const payload = data.slice(1);
      switch (data[0]) {
        case msgOutput:
          terminal.output(atob(payload));
          break;
        case msgPong:
          break;
        case msgSetWindowTitle:
          terminal.setWindowTitle(payload);
          break;
        case msgSetPreferences:
          const preferences = JSON.parse(payload);
          terminal.setPreferences(preferences);
          break;
        case msgAuth:
          if (payload == "auth FAIL") {
            user.notify("Couldn't authenticate to VisiData backend instance");
            this.close();
          }
          break;
      }
    };
  }

  private onClose() {
    this.socket.onclose = _event => {
      if (user.is_logged_in && user.time_remaining > 0) {
        this.autoReconnect();
      }
      else {
        this.realClose();
      }
    };
  }

  autoReconnect(retry_time = 1000) {
    terminal.showMessage("Reconnecting...", 0);
    this.setup();
    setTimeout(() => {
      if (!this.isOpen()) {
        this.autoReconnect(retry_time);
      }
    }, retry_time)
  }

  realClose () {
    clearInterval(this.ping_timer);
    user.idle_timeout = 0;
    terminal.deactivate();
    terminal.showMessage("Connection closed, please reload page", 0);
  }
}
