// Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

"use strict";

// TODO(davidben): When the string encoding API is implemented,
// replace this with the native in-browser implementation.
//
// https://wiki.whatwg.org/wiki/StringEncoding
// https://encoding.spec.whatwg.org/

/**
 * A stateful UTF-8 decoder.
 */
export default class {
  constructor() {
    // The number of bytes left in the current sequence.
    this.bytesLeft = 0;
    // The in-progress code point being decoded, if bytesLeft > 0.
    this.codePoint = 0;
    // The lower bound on the final code point, if bytesLeft > 0.
    this.lowerBound = 0;
  }

  /**
   * Decodes a some UTF-8 data, taking into account state from previous
   * data streamed through the encoder.
   *
   * @param {String} str data to decode, represented as a JavaScript
   *     String with each code unit representing a byte between 0x00 to
   *     0xFF.
   * @return {String} The data decoded into a JavaScript UTF-16 string.
   */
  decode(str) {
    var ret = "";
    for (var i = 0; i < str.length; i++) {
      var c = str.charCodeAt(i);
      if (this.bytesLeft == 0) {
        if (c <= 0x7f) {
          ret += str.charAt(i);
        } else if (0xc0 <= c && c <= 0xdf) {
          this.codePoint = c - 0xc0;
          this.bytesLeft = 1;
          this.lowerBound = 0x80;
        } else if (0xe0 <= c && c <= 0xef) {
          this.codePoint = c - 0xe0;
          this.bytesLeft = 2;
          this.lowerBound = 0x800;
        } else if (0xf0 <= c && c <= 0xf7) {
          this.codePoint = c - 0xf0;
          this.bytesLeft = 3;
          this.lowerBound = 0x10000;
        } else if (0xf8 <= c && c <= 0xfb) {
          this.codePoint = c - 0xf8;
          this.bytesLeft = 4;
          this.lowerBound = 0x200000;
        } else if (0xfc <= c && c <= 0xfd) {
          this.codePoint = c - 0xfc;
          this.bytesLeft = 5;
          this.lowerBound = 0x4000000;
        } else {
          ret += "\ufffd";
        }
      } else {
        if (0x80 <= c && c <= 0xbf) {
          this.bytesLeft--;
          this.codePoint = (this.codePoint << 6) + (c - 0x80);
          if (this.bytesLeft == 0) {
            // Got a full sequence. Check if it's within bounds and
            // filter out surrogate pairs.
            var codePoint = this.codePoint;
            if (
              codePoint < this.lowerBound ||
              (0xd800 <= codePoint && codePoint <= 0xdfff) ||
              codePoint > 0x10ffff
            ) {
              ret += "\ufffd";
            } else {
              // Encode as UTF-16 in the output.
              if (codePoint < 0x10000) {
                ret += String.fromCharCode(codePoint);
              } else {
                // Surrogate pair.
                codePoint -= 0x10000;
                ret += String.fromCharCode(
                  0xd800 + ((codePoint >>> 10) & 0x3ff),
                  0xdc00 + (codePoint & 0x3ff)
                );
              }
            }
          }
        } else {
          // Too few bytes in multi-byte sequence. Rewind stream so we
          // don't lose the next byte.
          ret += "\ufffd";
          this.bytesLeft = 0;
          i--;
        }
      }
    }
    return ret;
  }
}
