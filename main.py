import mido, hid, time
from math import log2
from sys import argv, exit

class MidiPlayer():
    counter = 0x00

    def __init__(self, filename: str):
        self.mid = mido.MidiFile(filename)
        #self.connect()

        self.joyconL = hid.Device(0x057E, 0x2006)
        self.joyconR = hid.Device(0x057E, 0x2006 + 0x01)

        self.send_cmd(0x48, [0x01])
        self.send_cmd(0x30, [0xFF])
        self.send_cmd(0x38, [0x28, 0x20, 0xF2, 0xF0, 0xF0])

    def connect(self, vid = 0x057E, pid = 0x2006):
        for i in range(0x0004):
            try:
                self.joycon = hid.Device(vid, pid + i)
            except:
                pass
        if not hasattr(self, 'joycon'):
            print('Failed to detect Joycon L, R, PRO or other Device')
            exit()
        else:
            print(f'Device: {self.joycon.product}')

    def play(self):
        self.send_midi()
        self.send_cmd(0x48, [0x00])

    def setfile(self, filename: str):
        self.mid = mido.MidiFile(filename)

    def miditofreq(self, n):
        n = 21 if n < 21 else 108 if n > 108 else n
        return 27.5 * ((2**(1/12))**(n - 21))

    def miditoamp(self, v):
        HA = round(v * (100/127)) * 2
        LA = round(v * (49/127)) + 0x0040 if v % 2 == 0 else round((v - 1) * (49/127)) + 0x8040
        return (HA, LA)

    def freqtorumble(self, f):
        f = 40.875885 if f < 40.875885 else 1252.572266 if f > 1252.572266 else f
        base = round(log2(f/10.0)*32.0)
        HF = (base - 0x60)*4
        LF = base - 0x40
        LF = 0x7F if LF > 0x7F else LF
        HF = 0x00 if HF < 0x00 else HF
        return (HF, LF)

    def miditorumble(self, n, v):
        HA, LA = self.miditoamp(v)
        HA, LA = HA if HA > 0xC8 else (0xC8, LA if LA > 0x0072 else 0x0072)
        HF, LF = self.freqtorumble(self.miditofreq(n))
        return [HF & 0xFF, HA + (HF >> 8), LF + (LA >> 8), LA & 0xFF]

    def send_cmd(self, cmd: int, subcmd: list):
        self.joyconL.write(b''.join([b'\x01', bytes([self.counter]), b'\x00\x01\x40\x40\x00\x01\x40\x40', bytes([cmd]), bytes(subcmd)]))
        self.joyconR.write(b''.join([b'\x01', bytes([self.counter]), b'\x00\x01\x40\x40\x00\x01\x40\x40', bytes([cmd]), bytes(subcmd)]))
        self.counter = (self.counter + 1) & 0xF
        time.sleep(0.1)
    
    def send_midi(self):
        for msg in self.mid:
            time.sleep(msg.time)
            if not msg.is_meta and msg.type == 'note_on':
                if msg.channel % 2 == 0:
                    self.joyconL.write(b''.join([b'\x10', bytes([self.counter]), bytes(self.miditorumble(msg.note, msg.velocity)), bytes(self.miditorumble(msg.note, msg.velocity))]))  
                else:
                    self.joyconR.write(b''.join([b'\x10', bytes([self.counter]), bytes(self.miditorumble(msg.note, msg.velocity)), bytes(self.miditorumble(msg.note, msg.velocity))])) 
                self.counter = (self.counter + 1) & 0xF

    def printchannels(self):
        l = []
        for msg in self.mid:
            if not msg.is_meta and not msg.channel in l:
                l.append(msg.channel)
        print(l)


if __name__ == "__main__":
    for i in range(10):
        print(10 - i)
        time.sleep(1)
    MidiPlayer(argv[1]).play()
