'''
v 0.1.5 KEYBOARD_PS2

Full library for PS/2 keyboard.

Controllers: Esp8266, Esp32, RP2
Connection:
    PS/2  | USB | Controller
    -------------------------
    Pin 3 | GND | GND
    Pin 5 | D+  | CLOCK
    Pin 1 | D-  | DATA 
    Pin 4 | VCC | 5V    

PS/2 Male   USB Female
 5 *|* 6    [ [] [] ]
3 *   * 4   G D+ D- V
 1 * * 2
 
Project path: https://github.com/r2d2-arduino/micropython-keyboard-ps2
MIT License

Author: Arthur Derkach
'''
from machine import Pin
from time import sleep_us, sleep_ms

KEYS = ('', 'f9', '', 'f5', 'f3', 'f1', 'f2', 'f12', '', 'f10', # 0-9
        'f8', 'f6', 'f4', 'tab', '`', '', '', 'alt', 'lshift', '', # 10-19
        'ctrl', 'q', '1', '', '', '', 'z', 's', 'a', 'w', # 20-29
        '2', 'lwin', '', 'c', 'x', 'd', 'e', '4', '3', 'rwin', # 30-39
        '', 'space', 'v', 'f', 't', 'r', '5', 'menu', '', 'n', # 40-49
        'b', 'h', 'g', 'y', '6', '', '', '', 'm', 'j', # 50-59
        'u', '7', '8', '', '', ',', 'k', 'i', 'o', '0', # 60-69
        '9', '', '', '.', '/', 'l', ';', 'p', '-', '', # 70-79
        '', '', '\'', '', '[', '=', '', '', 'capslock', 'rshift', # 80-89
        'enter', ']', '', '\\', '', '', '', '', '', '', # 90-99
        '', '', 'backspace', '', '', 'end', '', 'left', 'home', '', # 100-109
        '', '', 'insert', 'delete', 'down', 'center', 'right', 'up', 'esc', 'numlock', # 110-119
        'f11', '+', 'pagedown', '-', '*', 'pageup', 'scroll', '', '', '', # 120-129
        '', 'f7') # 130-131
 
SHIFTED_KEYS = ('', 'f9', '', 'f5', 'f3', 'f1', 'f2', 'f12', '', 'f10', # 0-9
        'f8', 'f6', 'f4', 'tab', '`', '', '', 'alt', 'lshift', '', # 10-19
        'ctrl', 'Q', '!', '', '', '', 'Z', 'S', 'A', 'W', # 20-29
        '@', 'lwin', '', 'C', 'X', 'D', 'E', '$', '#', 'rwin', # 30-39
        '', 'space', 'V', 'F', 'T', 'R', '%', 'menu', '', 'N', # 40-49
        'B', 'H', 'G', 'Y', '^', '', '', '', 'M', 'J', # 50-59
        'U', '&', '*', '', '', '<', 'K', 'I', 'O', ')', # 60-69
        '(', '', '', '>', '?', 'L', ':', 'P', '_', '', # 70-79
        '', '', '"', '', '{', '+', '', '', 'capslock', 'rshift', # 80-89
        'enter', '}', '', '|', '', '', '', '', '', '', # 90-99
        '', '', 'backspace', '', '', 'end', '', 'left', 'home', '', # 100-109
        '', '', 'insert', 'delete', 'down', 'center', 'right', 'up', 'esc', 'numlock', # 110-119
        'f11', '+', 'pagedown', '-', '*', 'pageup', 'scroll', '', '', '', # 120-129
        '', 'f7') # 130-131

NUM_KEYS = {'end':'1', 'left':'4', 'home':'7', 'insert':'0', 'delete':'.', 'down':'2',
            'center':'5', 'right':'6', 'up':'8', 'pagedown':'3', 'pageup':'9'}

CTRL   = KEYS.index('ctrl')
ALT    = KEYS.index('alt')
LSHIFT = KEYS.index('lshift')
RSHIFT = KEYS.index('rshift')
LWIN   = KEYS.index('lwin')
RWIN   = KEYS.index('rwin')

EXTENDED_KEYS = ( CTRL, ALT, LSHIFT, RSHIFT, LWIN, RWIN )

DELAY = 10
DELAY_LONG = 100

class KEYBOARD_PS2():
    def __init__( self, clock_pin, data_pin ):
        ''' Main constructor
        Args:
        clock_pin (int): Number of Clock Pin (D+)
        data_pin  (int): Number of Data  Pin (D-)
        '''
        self.clock = Pin( clock_pin, Pin.IN, Pin.PULL_UP )
        self.data  = Pin( data_pin,  Pin.IN, Pin.PULL_UP )
        
        self.clock.on()
        self.data.on()

        self.key_queue = []

        self.key_unpressed = False
        self.key_pause = False
        self.key_extended = False
        
        self.scroll_lock = False
        self.num_lock = False
        self.caps_lock = False
        
        sleep_us(DELAY_LONG)
        
    def reset( self ):
        ''' Reset stored data and Leds '''
        self.key_queue = []

        self.key_unpressed = False
        self.key_pause = False
        self.key_extended = False
        
        self.scroll_lock = False
        self.num_lock = False
        self.caps_lock = False
        
        self.send_led_commands()

    def read_data( self ):
        ''' Read one byte of data from PS/2 keyboard
        Return (byte): the byte read, or None if error.
        '''
        clock = self.clock
        data  = self.data
        
        clock.init(Pin.IN, Pin.PULL_UP)
        data.init( Pin.IN, Pin.PULL_UP)        
        #clock.on() # Allow to send data

        sleep_us(DELAY)
        
        # Waiting for data transfer to start
        while clock.value() == 1:  
            pass

        #sleep_us(DELAY) 

        byte = 0
        parity = 0

        # Read 8 bit of data
        for i in range(8):
            while clock.value() == 0:
                pass
            while clock.value() == 1:
                pass 

            bit = data.value()
            byte |= (bit << i)
            parity ^= bit

        # Read parity bit
        while clock.value() == 0:
            pass
        while clock.value() == 1:
            pass 
        
        parity_bit = data.value()

        # Read Stop bit
        while clock.value() == 0:
            pass
        while clock.value() == 1:
            pass 

        stop_bit = data.value()

        #clock.off() # Not allow to send data
        
        # Checking parity and stop bit
        if parity ^ 1 != parity_bit or stop_bit != 1:
            #print('error')
            return None  # Sending error
        
        return byte
    
    def send_command( self, command ):
        ''' Send one byte of command to PS/2 keyboard
        Return (bool): Acknowledge from PS/2 keyboard
        '''
        clock = self.clock
        data  = self.data
        
        data.init(Pin.OUT)
        clock.init(Pin.OUT)
        
        clock.value(0)
        sleep_us(DELAY_LONG)
        data.value(0)
        
        clock.init(Pin.IN, Pin.PULL_UP)
        
        # Set data bits
        parity = 1
        for i in range(8):
            while clock.value() == 0:
                pass
            while clock.value() == 1:
                pass
            bit = (command >> i) & 1
            data.value(bit)
            parity ^= bit
        
        # Set parity bit
        while clock.value() == 0:
            pass
        while clock.value() == 1:
            pass    
        data.value(parity)
        #print('Parity', parity)
        
        # Stop bit
        while clock.value() == 0:
            pass
        while clock.value() == 1:
            pass     
        data.value(1)
        
        data.init(Pin.IN, Pin.PULL_UP)
        
        # Wait for acknowledge from ps/2 keyboard
        ack = False
        for i in range(100):  
            if data.value() == 0:
                ack = True
                break
            sleep_us(DELAY)

        if not ack:
            print("Error: Keyboard did not acknowledge the command.")
        return ack   
    
    def check_led_keys( self, curr_key ):
        ''' Check of Lock keys
        curr_key (byte): Current key
        '''
        if curr_key == 'scroll':
            self.scroll_lock = not self.scroll_lock
            self.send_led_commands()
            
        if curr_key == 'numlock':
            self.num_lock = not self.num_lock
            self.send_led_commands()
            
        if curr_key == 'capslock':
            self.caps_lock = not self.caps_lock
            self.send_led_commands()
    
    def send_led_commands( self ):
        ''' Send commands to Ligth On/Off LEDs on PS/2 keyboard '''
        led_command  = self.scroll_lock << 0 
        led_command += self.num_lock    << 1 
        led_command += self.caps_lock   << 2 

        result1 = self.send_command(0xED)
        #print('cmd1:', result1)
        result2 = self.send_command(led_command)
        #print('cmd2:', result2)
        
    def shifting( self, data ):
        ''' Shift chars
        Return (list): Shifted list
        '''
        data_len = len(data)
        shifted_data = []
        
        shift_pressed = False
        capslock = self.caps_lock
        numlock = self.num_lock
        
        for i in range(data_len):
            if ( data[i] == 'lshift' ) or ( data[i] == 'rshift' ):
                shift_pressed = True
            else:                    
                if shift_pressed:
                    key_index = KEYS.index(data[i])
                    new_key = SHIFTED_KEYS[key_index]
                    if capslock and ( len(new_key) == 1 ):
                        new_key = new_key.lower()
                else:
                    new_key = data[i]
                    if numlock and ( new_key in NUM_KEYS ):
                        new_key = NUM_KEYS[new_key]
                        
                    if capslock and len(new_key) == 1:
                        new_key = new_key.upper()
                    
                shifted_data.append(new_key)
        
        return shifted_data

    def listening( self ):
        ''' Listening for new keys pressed
        Return (list): List of pressed keys
        '''
        while True:
            data_byte = self.read_data()
            #print(data_byte)
            
            if data_byte is not None:
                if data_byte == 240:
                    self.key_unpressed = True
                elif data_byte == 224:
                    self.key_extended = True
                elif data_byte == 225:
                    self.key_pause = True
                    if 'pause' not in self.key_queue:
                        self.key_queue.append('pause')
                elif data_byte == 170:
                    print('Keyboard ready')
                elif data_byte == 250:
                    print('Acknowledge')
                elif data_byte < 132:
                    curr_key = KEYS[data_byte]
                    #print(data_byte)
                    if curr_key == '':
                        print('?', data_byte, '?')
                    else:
                        if self.key_unpressed: # key up
                            if curr_key in self.key_queue:
                                self.key_queue.remove(curr_key) # remove from array

                                if self.key_pause and (curr_key == 'numlock'):
                                    self.key_pause = False
                                    self.key_queue.remove('pause')
                                else:
                                    self.check_led_keys(curr_key)
                            else:
                                print('Key not in queue', data_byte)
                                self.key_queue.clear()
                                
                            self.key_unpressed = False
                            self.key_extended = False
                            
                        else: # key down
                            if curr_key not in self.key_queue:
                                self.key_queue.append(curr_key)
                                self.key_extended = False                              
                            
                            if data_byte not in EXTENDED_KEYS:
                                return self.shifting( self.key_queue )
                else:
                    print('Unknown key:', data_byte)

'''
keyboard = KEYBOARD_PS2( clock_pin = 17, data_pin = 16 )

while True:
    keys = keyboard.listening()   
    print( keys )
'''
