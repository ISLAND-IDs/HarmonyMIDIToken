from music21 import converter, note, chord, tempo, stream, midi
import numpy as np
import os
import math

class HarmonyMIDIToken:
    def __init__(self):
        self.bpm = 128 # 기본값
        self.melody = []
        self.chords = []

    def _duration_to_note_length(self, dur_quarter_length):
        mapping = {
            4.0: "1bar",
            2.0: "half",
            1.0: "4th",
            0.5: "8th",
            0.25: "16th"
        }
        closest = min(mapping.keys(), key=lambda x: abs(x - dur_quarter_length))
        return mapping[closest]

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
            self.bpm = int(midi_data.metronomeMarkBoundaries()[0][2].number)

        for e in midi_data.flat.notesAndRests: # 모든 음표와 쉼표 가져옴
            if isinstance(e, note.Rest):
                self.melody.append({'note': '', 'duration': self._duration_to_note_length(e.quarterLength)})
                self.chords.append({'chord': '', 'duration': self._duration_to_note_length(e.quarterLength)})
            elif isinstance(e, chord.Chord):
                # 첫 번째 노트만 남기고 나머지 제거(예시)
                if len(e.pitches) > 1:
                    e.pitches = [e.pitches[0]]
            print(f"Processing element: {e}, offset: {e.offset}, duration: {e.quarterLength}")
            #TODO: 베이스 싱글 노트를 생각 못함 아마 '공백/베이스노트'로 처리할 것같음, 코드에서 높은 음은 멜로디로 처리하고, 높은 음이 없다면 멜로디에 rest를 추가할 것 멜로디도 같은 방식으로