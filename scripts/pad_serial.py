#
#
from tkinter import *
import tkinter.ttk as ttk
import serial
from serial.tools import list_ports

from pynput import mouse
from pynput import keyboard

import time


E2J = {'"': '@', '&': '^', '\'' : '&', '(' : '*', ')' : '(', 
      '=' : '_', '^' : '=', '~' : '+', '@' : '[', '`' : '{' , '[' : ']' , '{' : '}', 
      '+' : ':', ':' : '\'', '*' : '"', ']' : '\\',  '}' : '|' , 
      '\\' : 0x89, '|' : 0x88, '_' : 0x87}

FuncKeys = {
    33: b'\x1b\x5b\x34\x7e',    # PageUp
    34: b'\x1b\x5b\x35\x7e',    # PageDown
    35: b'\x1b\x5b\x33\x7e',    # End
    36: b'\x1b\x5b\x31\x7e',    # Home

    37: b'\x1b\x5b\x44',        # Left
    38: b'\x1b\x5b\x41',        # Up
    39: b'\x1b\x5b\x43',        # Right
    40: b'\x1b\x5b\x42',        # Down

    45: b'\x1b\x5b\x32\x7e',    # Insert
    46: b'\x7f',                # Del

    ### F1 - F9
    112: b'\x1b\x5b\x31\x31\x7e',
    113: b'\x1b\x5b\x31\x32\x7e',
    114: b'\x1b\x5b\x31\x33\x7e',
    115: b'\x1b\x5b\x31\x34\x7e',
    116: b'\x1b\x5b\x31\x35\x7e',
    117: b'\x1b\x5b\x31\x36\x7e',
    118: b'\x1b\x5b\x31\x37\x7e',
    119: b'\x1b\x5b\x31\x38\x7e',
    120: b'\x1b\x5b\x32\x30\x7e'
}


def find_serial_keyboard():
  ports = list_ports.comports()
  for p in ports:
    if 'CP210' in p.description:
      return p.device
  return None


class TouchPad(ttk.Frame):
    def __init__(self, master, port=None, mode=True):
        super().__init__(master, width=300, height=300)
        self.start_xy = None
        self.root=master
        self.capture_mouse=False
        self.mouse_listener=None
        self.keyboard_listener = None
        self.pressed_key = None
        self.keyin=False
        self.pressBtn=None
        self.enable_jis=mode
        self.mouse_speed = 5

        # create panel
        self.create_pane()
        self.propagate(False)
        self.pack()

        # open serial port
        if port is None: port = find_serial_keyboard()
        self.serial=serial.Serial(port, 38400)

    #
    # create panel
    def create_pane(self):
        self.pane=ttk.Frame(self, width=300, height=300, relief="groove")
        self.pane.bind("<Button-1>",self.move_start)
        self.pane.bind("<B1-Motion>",self.move_now)
        self.pane.bind("<ButtonRelease-1>",self.move_end)
        self.pane.place(x=0,y=0)

        self.root.bind("<Double-1>",self.toggle_mouse_listener)

        self.root.bind("<Enter>",self.enter_widget)
        self.root.bind("<Leave>",self.leave_widget)
        self.in_widget=False

        self.buttonL = ttk.Button(self,text = "L", width=10, takefocus=0)
        self.buttonL.place(x=0,y=0)
        self.buttonL.bind("<Button-1>",self.move_start)
        self.buttonL.bind("<B1-Motion>",self.move_now)
        self.buttonL.bind("<ButtonRelease-1>",self.move_end)

        self.buttonR = ttk.Button(self,text = "R", width=10, takefocus=0)
        self.buttonR.place(x=230,y=0)
        self.buttonR.bind("<Button-1>",self.move_start)
        self.buttonR.bind("<B1-Motion>",self.move_now)
        self.buttonR.bind("<ButtonRelease-1>",self.move_end)

        s_r=ttk.Style()
        s_r.configure('Key.TButton', background="red")
        s_b=ttk.Style()

        s_b.map("KeyB.TButton",
             foreground=[('pressed','red'), ('active', 'blue')],
             background=[('pressed', '!disabled', 'black'), ('active', 'green')]
        )
        self.keylabel=StringVar()
        self.keylabel.set("keyIn")
        self.buttonKey = ttk.Button(self,textvariable=self.keylabel, style='KeyB.TButton')
        self.buttonKey.place(x=110,y=0)
        self.buttonKey.bind("<Button-1>", self.keyin_set)

        self.root.bind("<KeyPress>", self.key_in)
        return

    def enter_widget(self,event):
        self.in_widget=True
        return
    def leave_widget(self, event):
        self.in_widget=False
        return
    #
    #
    def send_command(self, msg):
        self.serial.write(msg)
        return
    #
    # Keyboard event
    def keyin_set(self, event):
        if self.keyin :
            self.keyin = False
            self.keylabel.set("KeyIn")
        else:
            self.keyin = True
            self.keylabel.set("Key active")
        return
        
    def send_keycode(self, ch):
        if type(ch) is int:
            self.send_command(ch.to_bytes(1, 'big'))
        else:
            self.send_command(bytes(ch, 'UTF-8'))
        return

    def key_in(self, event):
        if not self.keyin: return
        if event.char:
            if event.state == 0 or event.state == 1:
                if self.enable_jis and event.char in E2J:
                    ch = E2J[event.char]
                    self.send_keycode(ch)
                else:
                    self.send_keycode(event.char)
                    #self.send_command(bytes(event.char, 'UTF-8'))
            elif event.state == 4:
                self.send_keycode(event.char)
                #self.send_command(bytes(event.char, 'UTF-8'))
            else:
                print(event.char, event.state)
            return
        
        if event.keycode in (16, 17, 18): return   ## Shift, Ctrl, Alt

        self.function_key(event)
        return

    def function_key(self, event):
        if event.keycode in FuncKeys:
            #print("==>",FuncKeys[event.keycode])
            self.send_command(FuncKeys[event.keycode])
        else:
            print(event.keycode)
        return
    #
    #  Mouse event
    def mouse_move_cmd(self, x, y, w=0):
        data = b'\x1b\x5b\x6d'
        if self.pressBtn == 'L':
            data += b'\x01'
        elif self.pressBtn == 'R':
            data += b'\x02'
        else:
            data += b'\x00'

        if x < -128 or y < -128 or w < -128:
            data += b'\x00\x00\x00\x7e'
        else:
            x = min(max(x + 128, 1), 255)
            y = min(max(y + 128, 1), 255)
            w = min(max(w + 128, 1), 255)
            data += x.to_bytes(1, 'big')
            data += y.to_bytes(1, 'big')
            data += w.to_bytes(1, 'big')
            data += b'\x7e'
        return data

    def send_mouse_event(self, x, y, w):
        data = self.mouse_move_cmd(x, y, w)
        self.send_command(data)
        time.sleep(0.01)
        return

    def move_start(self,event):
        # マウスカーソルの座標取得
        self.start_xy = (event.x_root,event.y_root)
        # 位置情報取得
        try:
            place_info = event.widget.place_info()
            x = int(place_info['x'])
            y = int(place_info['y'])
        except:
            return

        if event.type is EventType.ButtonPress: 
            try:
                print("Push", event.widget.cget('text'))
                self.pressBtn = event.widget.cget('text')
                self.mouse_click(event)
            except:
                self.pressBtn=None
        return

    def move_now(self, event):
        if self.start_xy is None:   return
        # 移動距離を調べる
        #distance = (event.x_root-self.start_xy[0], event.y_root-self.start_xy[1])
        x=(event.x_root-self.start_xy[0]) * self.mouse_speed
        y=(event.y_root-self.start_xy[1]) * self.mouse_speed

        self.send_mouse_event(x, y, 0)
        self.start_xy = (event.x_root, event.y_root)
        return

    def move_end(self,event):
        self.start_xy = None
        self.pressBtn=None
        self.mouse_click(event)
        return

    def mouse_click(self, event=None):
        self.send_mouse_event(-255, 0, 0)
        return

    ##########################################
    # Keyboard and mouse listener
    def toggle_mouse_listener(self, event=None):
        if self.capture_mouse or event is None:
            self.mouse_listener.stop()
            self.keyboard_listener.stop()
            self.capture_mouse = False
            self.mouse_listener = None
            self.keyboard_listener = None
            print("capture terminated")
        else:
            self.mouse_listener = mouse.Listener(
                on_move=self.on_mouse_move,
                on_click=self.on_mouse_click,
                on_scroll=self.on_mouse_scroll)
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_keyboard_press,
                on_release=self.on_keyboard_release)
            self.mouse_listener.start()
            self.keyboard_listener.start()
            self.capture_mouse = True
            print("capture start")
        return

    def on_mouse_move(self, x, y):
        if not self.start_xy is None:
            dx=(x-self.start_xy[0]) * self.mouse_speed
            dy=(y-self.start_xy[1]) * self.mouse_speed

            #if self.pressed_key is None:
            if self.pressed_key is keyboard.Key.shift:
                self.send_mouse_event(dx, dy, 0)
        self.start_xy = (x, y)
        return

    def on_mouse_click(self, x, y, button, pressed):
        if not self.in_widget : return
        if pressed:
            if button is mouse.Button.right:
                self.pressBtn = 'R'
            elif button is mouse.Button.left:
                self.pressBtn = 'L'
        else:
            self.pressBtn = None

        #if self.pressed_key is None:
        #self.send_mouse_event(x, y, 0)
        self.mouse_click()
        return

    def on_mouse_scroll(self, x, y, dx, dy):
        if not self.in_widget : return
        self.send_mouse_event(0, 0, dy)
        return

    def on_keyboard_press(self,key):
        self.pressed_key=key
        if self.pressed_key is keyboard.Key.esc:
            self.toggle_mouse_listener()
            self.on_keyboard_release(key)
        return

    def on_keyboard_release(self,key):
        self.pressed_key = None
        return

#
#  M A I N 
if __name__ == '__main__':
    port = find_serial_keyboard()
    mode=False
    if len(sys.argv) > 1:
        mode=(sys.argv[1] == 'JP')

    if port is None: exit()

    master = Tk()
    master.title("TouchPad")
    master.geometry("300x300")
    TouchPad(master, port, mode)
    master.mainloop()
    