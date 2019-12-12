import pyaudio
import numpy as np
import struct
from scipy import signal
import matplotlib.pyplot as plt
#import time

threshold = 10
rate = 16000
input_block_time = 0.128
fft_size = 2048
time_slots = 128
input_frames_per_block = int(rate*input_block_time)

def get_rms(block):
    return np.sqrt(np.mean(np.square(block)))

class AudioHandler(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.threshold = threshold
        self.spec = np.zeros((int(fft_size/2+1), time_slots), dtype=float)
        #self.start = time.time()
        #self.end = 0

    def stop(self):
        self.stream.close()
        
    def find_input_device(self):
        dev_index = None
        for i in range(self.pa.get_device_count()):
            dev_info = self.pa.get_device_info_by_index(i)
            print('Device %{}: %{}'.format(i, dev_info['name']))
            
            for keyword in ['mic', 'input']:
                if keyword in dev_info['name'].lower():
                    print('Found an input device {} - {}'.format(i, dev_info['name']))
                    dev_index = i
                    return dev_index
                
        if dev_index == None:
            print('No preferred input found => using default input')
            
        return dev_index
    
    def open_mic_stream(self):
        dev_index = self.find_input_device()
        stream = self.pa.open(format = pyaudio.paInt16,
                             channels = 1,
                             rate = rate,
                             input = True,
                             input_device_index = dev_index,
                             frames_per_buffer = input_frames_per_block)
        return stream
       
    def fft_process(self, block):
        freq = np.absolute(np.fft.rfft(block, n=fft_size))
        self.spec = np.roll(self.spec, -1, axis=1)
        self.spec[:,-1] = freq
        #self.end = time.time()
        #print(self.end-self.start)
        #self.start = time.time()

        plt.clf()
        plt.pcolormesh(self.spec, cmap='inferno', vmin=0, vmax=70000)
        plt.gcf().tight_layout()
        plt.pause(0.00001)

    def listen(self):
        try:
            raw_block = self.stream.read(input_frames_per_block, exception_on_overflow = False)
            count = len(raw_block)/2
            format = '%dh' % (count)
            block = np.array(struct.unpack(format, raw_block))
        except Exception as e:
            print('Error recording: {}'.format(e))
            return
        
        amplitude = get_rms(block)
        if amplitude > self.threshold:
            self.fft_process(block)
        else:
            pass
        
if __name__ == '__main__':
    audio = AudioHandler()
    try:
        while True:
            audio.listen()
    except KeyboardInterrupt:
        audio.stop()
