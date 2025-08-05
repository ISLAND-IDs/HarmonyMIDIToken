from music21 import converter, note, chord, tempo, stream, midi
import numpy as np
import os
import math

class HarmonyMIDIToken:
    def __init__(self):
        self.bpm = 128 # 기본값
        self.melody = []
        self.chords = []

    @property
    def token_id(self):
        """vocab = {
            "note_C4": 10,
            "note_E4": 11,
            "note_-": 12,
            "duration_8th": 20,
            "duration_4th": 21,
            "chord_Cmaj7/C": 30,
            "chord_-": 31,
            "BPM_128": 40
        }

        output_token_ids = [40, 10, 20, 12, 20, 11, 21, 30, 21, 31, 21]"""
        #idea = [self.bpm, self.melody.t, self.chords.t]
        return 'HarmonyMIDIToken' # 숫자로 이루어진 ID로 변경 가능
    
    def set_id(self, token_id):
        """Set the token ID for the HarmonyMIDIToken."""

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

        for e in midi_data.flat.notesAndRests: # 모든 음표와 쉼표 가져옴
            if isinstance(e, note.Rest):
                pass
            

        