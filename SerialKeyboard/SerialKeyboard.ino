
/*
 * Serial-Keyboard adaptor
 *  Copyright(C) 2021 Isao Hara, all rights reserved.
 *  
 */
 /*
 * Software Serial work 
 * The library has the following known limitations:
 *   - If using multiple software serial ports, only one can receive data at a time.
 *   - Not all pins on the Mega and Mega 2560 support change interrupts, so only the
 *      following can be used for RX: 10, 11, 12, 13, 14, 15, 50, 51, 52, 53, A8 (62),
 *     A9 (63), A10 (64), A11 (65), A12 (66), A13 (67), A14 (68), A15 (69).
 *   - Not all pins on the Leonardo and Micro support change interrupts, so only the 
 *     following can be used for RX: 8, 9, 10, 11, 14 (MISO), 15 (SCK), 16 (MOSI).
 *   - On Arduino or Genuino 101 the current maximum RX speed is 57600bps
 *   - On Arduino or Genuino 101 RX doesn't work on Pin 13
 * If your project requires simultaneous data flows, see Paul Stoffregen's AltSoftSerial library.
 * AltSoftSerial overcomes a number of other issues with the core SoftwareSerial, but has it's own limitations.
 * Refer to the AltSoftSerial site for more information.
 */

#ifdef SOFT_SERIAL
#include <SoftwareSerial.h>

#if 1
#define TX_PORT 9
#define RX_PORT 10
#else
#define TX_PORT 14
#define RX_PORT 15
#endif

SoftwareSerial mySerial = SoftwareSerial(RX_PORT,TX_PORT);

#else

#define mySerial  Serial1
#endif
#define MAX_BUF_SIZE 16
#define BRATE 38400

/*
 * Keyboard and Mouse
 */
#if 1
#define   HID_CUSTOM_LAYOUT
#define   LAYOUT_JAPANESE
#include  "HID-Project.h"
#else
#include <Keyboard.h>
#include <Mouse.h>
#endif

/*
 * Switch
 */
#define UP_PORT 19
#define ENTER_PORT 3
#define DOWN_PORT 9

int delay_val=20;
int lastSwitch = HIGH;
int keyState = 7;

void setup() {

  
  // put your setup code here, to run once:
#ifdef SOFT_SERIAL
  pinMode(RX_PORT, INPUT);
  pinMode(TX_PORT, OUTPUT);
#endif
  mySerial.begin(BRATE);

  // for direct input switch
  //pinMode(REBOOT_PORT, INPUT);
  pinMode(DOWN_PORT, INPUT_PULLUP);
  pinMode(UP_PORT, INPUT_PULLUP);
  pinMode(ENTER_PORT, INPUT_PULLUP);
  lastSwitch = LOW;
  
  delay(100);
  mySerial.println("- Hello, Serial-Keyboard -");
  Serial.begin(9600);

  ///// 
  Keyboard.begin();
  Mouse.begin();
}

void loop() {
  // put your main code here, to run repeatedly:
  char buf[MAX_BUF_SIZE];
#ifdef SOFT_SERIAL
  mySerial.listen();
#endif
  delay(delay_val);
  int size = mySerial.available();

  /// If data comming via serial interface
  if (size > 1){
    int len = mySerial.readBytes(buf, min(size, MAX_BUF_SIZE));

    /// Multi-bytes input data
    if(len >= 3){
      // keyboard input?
      int key_val = CheckFuncKey(buf, len);
      if (key_val > 0){
        KeyPress2(key_val);
        delay_val = 20;
      }else{
        /// Mouse input
        if (CheckMouseVal(buf, len) == 1){
          int x, y, w, b;
          b=buf[3];
          x=(int)buf[4]-128;
          y=(int)buf[5]-128;
          w=(int)buf[6]-128;
          
          if( b == 0 ){ 
           if (x == -128 && y == -128 && w == -128){
             Mouse.release(MOUSE_ALL);
           }else{
             Mouse.move(x, y, w);
           }
          }else{
            int btn = MOUSE_LEFT;
            if (b == 2){  btn = MOUSE_RIGHT; }
            if (x == -128 && y == -128 && w == -128){
              if (Mouse.isPressed(btn) ){
                Mouse.release(btn);
              }else{
                Mouse.press(btn);
              }
            }else{
              Mouse.move(x, y, w);
            }
          }
          delay_val=10;
        }
      }
    }
  } else if (size == 1){
    /// Single data comming
    unsigned char ch=mySerial.read();
    // Functional key
    int res=PressSpecialJpKey(ch);
    if (res == 0){
      KeyPress(ch);
    }
    delay_val=20;
  }

  // Switch
 
  keyState = (digitalRead(ENTER_PORT) << 2) |  (digitalRead(UP_PORT) << 1) | digitalRead(DOWN_PORT);
  if(keyState == 3){
      Keyboard.write(KEY_ENTER);
      //Serial.println("ENTER");
      delay(100);
  }else if (keyState == 6){
      Keyboard.write(KEY_DOWN_ARROW);
      //Serial.println("Down");
      delay(100);
  }else if(keyState == 5){
      Keyboard.write(KEY_UP_ARROW);
      //Serial.println("Up");
      delay(100);
  }else if (keyState == 2){
    Keyboard.press(KEY_LEFT_CTRL);
    Keyboard.press(KEY_LEFT_ALT);
    Keyboard.press(KEY_DELETE);
    delay(100);
    Keyboard.releaseAll();
    delay(500);
  }

  // Check Reboot switch
  /*
  if (lastSwitch == LOW and digitalRead(REBOOT_PORT) == LOW){
    lastSwitch = HIGH;

    Keyboard.press(KEY_LEFT_CTRL);
    Keyboard.press(KEY_LEFT_ALT);
    Keyboard.press(KEY_DELETE);
    delay(100);
    Keyboard.releaseAll();

    Serial.println("Reboot");
  }else if (lastSwitch == HIGH and digitalRead(REBOOT_PORT) == HIGH){
    lastSwitch=LOW;
  }
 */
}

//
// Check Japanese local key-in
int PressSpecialJpKey(unsigned char ch){
    if (ch == 0x89){ // Backslash
      Keyboard.write(KeyboardKeycode(0x89));
    }else if (ch == 0x87 || ch == 0x88 || ch == 0x8b ){
      Keyboard.write(ch);
    }else if (ch == 0x8a){ 
      Keyboard.write(KeyboardKeycode(0x94));
    }else{
      return 0;
    }
    return 1;
}


//
//  Functional key-in
int CheckFuncKey(char *buf, int size){
  if(size < 3)  return -1;
  if (buf[0] != 0x1b or buf[1] != 0x5b) return -1;
  if(size == 3){
    switch(buf[2]){
      case 0x41:  // ^
         return KEY_UP_ARROW;
      case 0x42:  // v
         return KEY_DOWN_ARROW;
      case 0x43: //  ->
         return KEY_RIGHT_ARROW;
      case 0x44:  // <-
         return KEY_LEFT_ARROW;
      default:
         return -1;
    }
  }else if(size == 4){
    if(buf[3] == 0x7e){
      switch(buf[2]){
        case 0x31:  // Home
          return KEY_HOME;
        case 0x32:  // Ins
          return KEY_INSERT;
        case 0x33: //  End
           return KEY_END;
        case 0x34:  // Up
           return KEY_PAGE_UP;
        case 0x35:  // DOWN
           return KEY_PAGE_DOWN;
        default:
           return -1;
      }
    }
  }else{
    if(buf[4] == 0x7e){
      if (buf[2] == 0x31){
        switch(buf[3]){
          case 0x31:
            return KEY_F1;
          case 0x32:
            return KEY_F2;
          case 0x33:
            return KEY_F3;
          case 0x34:
            return KEY_F4;
          case 0x35:
            return KEY_F5;
          case 0x36:
            return KEY_F6;
          case 0x37:
            return KEY_F7;
          case 0x38:
            return KEY_F8;
          default:
            return -1;
        }
      }
      if(buf[2] == 0x32){
        
        switch(buf[3]){
          case 0x30:
            return KEY_F9;
          case 0x31:
            return KEY_F10;
          case 0x32:
            return KEY_F11;
          case 0x33:
            return KEY_F12;
          default:
            return -1;
        }
      }
    }
  }
  return -1;
}

// Keypress
void KeyPress2(int key_val){
  Keyboard.press(KeyboardKeycode(key_val));
  delay(10);
  Keyboard.releaseAll();
}


//// KeyPress
void KeyPress(unsigned char ch){
    switch(ch){
      case '\r':
        Keyboard.write(KEY_RETURN);
        break;
      case 0x09:
        Keyboard.write(KEY_TAB);
        break;    
      case 0x1b:
        Keyboard.write(KEY_ESC);
        break;
      case 0x08:
        Keyboard.write(KEY_BACKSPACE);
        break;
      case 0x7f:
        Keyboard.write(KEY_DELETE);
        break;
      default:
        if (ch > 0 && ch < 0x1b){
          Keyboard.press(KEY_LEFT_CTRL);
          Keyboard.press(ch + 0x60);
          delay(20);
          Keyboard.releaseAll();
        }else{
          Keyboard.write(ch);
        }
        break;
    }
}

//
// check mouse movement
// Mouse data(8byts):  0x1b:0x5b:0x5d:Press:X:Y:Weel:0x7e
int CheckMouseVal(char *buf, int len){
  if (len == 8){
    if (buf[0] == 0x1b && buf[1] == 0x5b && buf[2] == 0x6d && buf[7] == 0x7e){
      return 1; 
    }
  }
  return 0;
}
