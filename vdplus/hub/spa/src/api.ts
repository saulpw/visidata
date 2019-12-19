import m from "mithril";

class API {
  base: string;
  api_stack: number;
  is_active: boolean;
  token!: string | null;

  constructor() {
    switch (ENV.mode) {
      case "production":
        this.base = "/";
        break;
      case "development":
        this.base = "http://localhost:5000/";
        break;
      case "test":
        this.base = "http://localhost:5002/";
        break;
      default:
        this.base = "/";
        break;
    }
    this.base += "api/";
    this.api_stack = 0;
    this.is_active = false;
  }

  async request(url: string, options: m.RequestOptions<any> = {}) {
    let response: Promise<any>;
    url = this.base + url;
    this.handleProgress(1);
    this.addHeaders(options);
    try {
      response = await m.request(url, {
        ...options,
        ...this.extractResponse()
      });
    } catch (e) {
      response = e;
    } finally {
      this.handleProgress(-1);
    }
    return response;
  }

  private extractResponse() {
    let meta: JSON;
    return {
      extract: (xhr: XMLHttpRequest) => {
        let body: JSON | string | null;
        if (xhr.status == 204) {
          body = null;
        } else if (xhr.status > 199 && xhr.status < 500) {
          let parsed = JSON.parse(xhr.responseText);
          if (parsed!.hasOwnProperty("meta")) {
            body = parsed.response;
            meta = parsed.meta;
          } else {
            body = parsed;
          }
        } else {
          body = xhr.responseText;
        }
        return {
          status: xhr.status,
          body: body,
          meta: meta
        };
      }
    };
  }

  private addHeaders(options: m.RequestOptions<any>) {
    options.headers = options.headers || {};
    if (this.token) {
      options.headers["Authorization"] = "Bearer " + this.token;
    }
    return options;
  }

  private handleProgress(direction: number) {
    m.redraw();
    this.api_stack += direction;
    this.is_active = this.api_stack > 0;
  }
}

export default new API();
