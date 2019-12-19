import user from "user";

export default class {
  /**
   * limits your function to be called at most every W milliseconds, where W is wait.
   * Calls over W get dropped.
   * Thanks to Pat Migliaccio.
   * see https://medium.com/@pat_migliaccio/rate-limiting-throttling-consecutive-function-calls-with-queues-4c9de7106acc
   * @param fn
   * @param wait
   * @example let throttledFunc = throttle(myFunc,500);
   */
  static throttle(fn: Function, wait: number) {
    let isCalled = false;

    return function(...args: any[]) {
      if (!isCalled) {
        fn(...args);
        isCalled = true;
        setTimeout(function() {
          isCalled = false;
        }, wait);
      }
    };
  }

  static uuid() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(c) {
      var r = (Math.random() * 16) | 0,
        v = c == "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  static deeplyGet(obj: any, ...rest: string[]): any {
    if (obj === undefined) return false;
    const level = rest[0];
    if (rest.length == 1 && obj.hasOwnProperty(level)) return obj[level];
    rest.shift();
    return this.deeplyGet(obj[level], ...rest);
  }
}
