import pyaudio
import numpy as np
import matplotlib.pyplot as plt

import math
import requests


def frequency_to_note(frequency):
    # define constants that control the algorithm
    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] # these are the 12 notes in each octave
    OCTAVE_MULTIPLIER = 2 # going up an octave multiplies by 2
    KNOWN_NOTE_NAME, KNOWN_NOTE_OCTAVE, KNOWN_NOTE_FREQUENCY = ('A', 4, 440) # A4 = 440 Hz

    # calculate the distance to the known note
    # since notes are spread evenly, going up a note will multiply by a constant
    # so we can use log to know how many times a frequency was multiplied to get from the known note to our note
    # this will give a positive integer value for notes higher than the known note, and a negative value for notes lower than it (and zero for the same note)
    note_multiplier = OCTAVE_MULTIPLIER**(1/len(NOTES))
    frequency_relative_to_known_note = frequency / KNOWN_NOTE_FREQUENCY
    distance_from_known_note = math.log(frequency_relative_to_known_note, note_multiplier)

    # round to make up for floating point inaccuracies
    distance_from_known_note = round(distance_from_known_note)

    # using the distance in notes and the octave and name of the known note,
    # we can calculate the octave and name of our note
    # NOTE: the "absolute index" doesn't have any actual meaning, since it doesn't care what its zero point is. it is just useful for calculation
    known_note_index_in_octave = NOTES.index(KNOWN_NOTE_NAME)
    known_note_absolute_index = KNOWN_NOTE_OCTAVE * len(NOTES) + known_note_index_in_octave
    note_absolute_index = known_note_absolute_index + distance_from_known_note
    note_octave, note_index_in_octave = note_absolute_index // len(NOTES), note_absolute_index % len(NOTES)
    note_name = NOTES[note_index_in_octave]
    return (note_name, note_octave,note_index_in_octave)

np.set_printoptions(suppress=True) # don't use scientific notation

CHUNK = int(1024*4) # number of data points to read at a time
RATE = int(44100) # time resolution of the recording device (Hz)
maxValue = 2**32
bars = 35

p=pyaudio.PyAudio() # start the PyAudio class
stream=p.open(format=pyaudio.paInt16,channels=2,rate=RATE,input=True,
              frames_per_buffer=CHUNK) #uses default input device

out_stream = p.open(format=pyaudio.paInt16, channels=2, rate=RATE,output=True)

print(pyaudio.get_portaudio_version_text())

freqs = []

# create a numpy array holding a single read of audio data
for i in range(10000): #to it a few times just to see
    w = stream.read(CHUNK)
    data = np.fromstring(w,dtype=np.int16)
    #out_stream.write(w)
    #continue
    dataL = data[0::2]
    dataR = data[1::2]
    peakL = np.abs(np.max(dataL)-np.min(dataL))/maxValue
    peakR = np.abs(np.max(dataR)-np.min(dataR))/maxValue
    lString = "#"*int(peakL*bars)+"-"*int(bars-peakL*bars)
    rString = "#"*int(peakR*bars)+"-"*int(bars-peakR*bars)
    #print("L=[%s]\tR=[%s] %f"%(lString, rString, peakL))
    

    data = np.fromstring(stream.read(CHUNK),dtype=np.int32)
    data = data * np.hanning(len(data)) # smooth the FFT by windowing data
    fft = abs(np.fft.fft(data).real)
    fft = fft[:int(len(fft)/2)] # keep only first half
    freq = np.fft.fftfreq(CHUNK,1.0/RATE)
    freq = freq[:int(len(freq)/2)] # keep only first half
    freqPeak = freq[np.where(fft==np.max(fft))[0][0]]+1
    print("peak frequency: %d Hz"%freqPeak)
    # print(frequency_to_note(freqPeak))
    if(peakL>0.00000001):
        # print("L=[%s]\tR=[%s] %f %s"%(lString, rString, peakL,frequency_to_note(freqPeak)))
        note,oct,note_index_in_octave = frequency_to_note(freqPeak)
        freqs.append(note_index_in_octave)
        if(len(freqs) < 6):
            continue
        print(freqs)
        print("L=[%s]\tR=[%s] %f %s %d"%(lString, rString, peakL,max(set(freqs), key = freqs.count),oct))
        

        headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'http://192.168.43.252/',
            'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8,fr;q=0.7',
        }

        
        basefreq = freqPeak
        params = (
            ('m', '1'),('h0',max(set(freqs), key = freqs.count)*21)
        )
        ##print("color %s %s" % (ord(note),freqPeak))
        response = requests.get('http://192.168.43.252/', headers=headers, params=params, verify=False)
        freqs = []

    # uncomment this if you want to see what the freq vs FFT looks like
    # plt.plot(freq,fft)
    # plt.axis([0,4000,None,None])
    # plt.show()
    # plt.close()

# close the stream gracefully
stream.stop_stream()
stream.close()
p.terminate()