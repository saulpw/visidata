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
const msgSetReconnect = "5";
// This is specific to VisiData authentication
const msgAuth = "6";

export default class {
  socket: WebSocket;
  reconnect: number;
  ping_timer!: number;
  reconnect_timeout!: number;

  constructor() {
    this.socket = new WebSocket(this.url());
    this.reconnect = -1;
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
    this.onOpen();
    this.onReceive();
    this.onClose();
  }

  close() {
    clearTimeout(this.reconnect_timeout);
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
        case msgSetReconnect:
          const autoReconnect = JSON.parse(payload);
          console.log("Enabling reconnect: " + autoReconnect + " seconds");
          this.reconnect = autoReconnect;
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
      clearInterval(this.ping_timer);
      terminal.deactivate();
      terminal.showMessage("Connection Closed", 0);
      if (this.reconnect > 0) {
        this.reconnect_timeout = window.setTimeout(() => {
          terminal.reset();
          this.setup();
        }, this.reconnect * 1000);
      }
    };
  }
}
