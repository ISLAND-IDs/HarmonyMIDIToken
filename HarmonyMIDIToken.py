from music21 import converter, note, chord, tempo, stream, midi
import math

class HarmonyMIDIToken:
    def __init__(self):
        self.bpm = 128 # 기본값
        self.melody = {}
        self.chords = {}

    def to_json(self):
        return {
            'BPM': self.bpm,
            'Melody': self.melody,
            'Chord': self.chords
        }
    
    def to_midi(self):
        return
    
    def set_midi(self, midi_file):
        midi_data = converter.parse(midi_file)
        if midi_data.metronomeMarkBoundaries(): # 메트로놈 마크가 있는 경우 첫 번째 마크의 BPM을 사용
            self.bpm = midi_data.metronomeMarkBoundaries()[0][2].number
        
        