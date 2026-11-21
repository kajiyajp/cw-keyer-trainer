// 作成：2026-11-21
// 目的：USB 複合デバイスの実装（Adafruit TinyUSB）
#include "hw_usb.h"
#include <Adafruit_TinyUSB.h>
#include <string.h>

namespace {
uint8_t const reportDesc[] = {TUD_HID_REPORT_DESC_KEYBOARD()};
Adafruit_USBD_HID usbHid;
bool wantDown = false;  // 送りたい状態
bool sentDown = false;  // 送った状態
char lineBuf[64];
size_t lineLen = 0;
bool lineOverflow = false;
}  // namespace

// HID キーボードを登録し、CDC を開く
void usbBegin() {
  if (!TinyUSBDevice.isInitialized()) TinyUSBDevice.begin(0);
  usbHid.setBootProtocol(HID_ITF_PROTOCOL_KEYBOARD);
  usbHid.setPollInterval(1);
  usbHid.setReportDescriptor(reportDesc, sizeof(reportDesc));
  usbHid.setStringDescriptor("CW Keyer Trainer");
  usbHid.begin();
  Serial.begin(115200);
  // コアは setup 前に CDC だけで USB を始めているので、接続状態に関係なく付け直して HID を認識させる
  TinyUSBDevice.detach();
  delay(10);
  TinyUSBDevice.attach();
}

// HID の状態が送った状態と違えば送る
void usbService() {
#ifdef TINYUSB_NEED_POLLING_TASK
  TinyUSBDevice.task();
#endif
  if (wantDown == sentDown || !usbHid.ready()) return;
  if (wantDown) {
    uint8_t keys[6] = {HID_KEYCODE, 0, 0, 0, 0, 0};
    usbHid.keyboardReport(0, 0, keys);
  } else {
    usbHid.keyboardRelease(0);
  }
  sentDown = wantDown;
}

void usbKey(bool down) {
  wantDown = down;
  usbService();
}

// 1行を組み立てる。長すぎる行は捨てる
bool usbReadLine(char* buf, size_t n) {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      bool ok = !lineOverflow;
      lineBuf[lineLen] = '\0';
      lineLen = 0;
      lineOverflow = false;
      if (ok) {
        strncpy(buf, lineBuf, n - 1);
        buf[n - 1] = '\0';
        return true;
      }
      continue;
    }
    // 印字できない文字は捨てる（PC 側のポート探索ツールが 0xC0 などを送ってくることがある）
    if ((uint8_t)c < 0x20 || (uint8_t)c > 0x7E) continue;
    if (lineLen < sizeof(lineBuf) - 1) lineBuf[lineLen++] = c;
    else lineOverflow = true;
  }
  return false;
}

void usbPrintLine(const char* s) {
  if (!Serial) return;  // PC 側でポートが開かれていない
  if ((size_t)Serial.availableForWrite() < strlen(s) + 2) return;
  Serial.println(s);
}
