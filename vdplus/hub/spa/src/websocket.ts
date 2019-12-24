import Manager from "manager";

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

export default class {
  socket: WebSocket;
  manager: Manager;
  reconnect: number;
  ping_timer!: number;
  reconnect_timeout!: number;

  constructor(manager: Manager) {
    this.manager = manager;
    this.socket = new WebSocket(this.url());
    this.reconnect = -1;
    this.setup();
  }

  url() {
    let domain: string;
    const httpsEnabled = window.location.protocol == "https:";
    if (ENV.API_SERVER == "/") {
      domain = window.location.hostname;
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

  onOpen() {
    this.socket.onopen = _event => {
      const termInfo = this.manager.info();

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

      this.manager.onResize(resizeHandler);
      resizeHandler(termInfo.columns, termInfo.rows);

      this.manager.onInput((input: string) => {
        this.socket.send(msgInput + input);
      });

      this.ping_timer = window.setInterval(() => {
        this.socket.send(msgPing);
      }, 30 * 1000);
    };
  }

  onReceive() {
    this.socket.onmessage = event => {
      const data = event.data;
      const payload = data.slice(1);
      switch (data[0]) {
        case msgOutput:
          this.manager.output(atob(payload));
          break;
        case msgPong:
          break;
        case msgSetWindowTitle:
          this.manager.setWindowTitle(payload);
          break;
        case msgSetPreferences:
          const preferences = JSON.parse(payload);
          this.manager.setPreferences(preferences);
          break;
        case msgSetReconnect:
          const autoReconnect = JSON.parse(payload);
          console.log("Enabling reconnect: " + autoReconnect + " seconds");
          this.reconnect = autoReconnect;
          break;
      }
    };
  }

  onClose() {
    this.socket.onclose = _event => {
      clearInterval(this.ping_timer);
      this.manager.deactivate();
      this.manager.showMessage("Connection Closed", 0);
      if (this.reconnect > 0) {
        this.reconnect_timeout = window.setTimeout(() => {
          this.manager.reset();
          this.setup();
        }, this.reconnect * 1000);
      }
    };
  }
}
