from music21 import converter, note, chord as music21_chord, pitch, stream, midi
from pychord import find_chords_from_notes, Chord as pychord_chord
from io import BytesIO
import numpy as np
import json
import copy

class HarmonyMIDIToken:
    def __init__(self):
        self.bpm = 128 # 기본값
        self.melody:list[dict] = []
        self.chords:list[dict] = []
        self.bass:list[dict] = []
        self._midi = None # MIDI 파일을 저장할 변수 최적화를 위해서임 진짜로 귀찮아서 날먹하는 거 아님

    def _intpitch_to_note_name(self, pitch_int):
        """MIDI 피치 정수를 음표 이름으로 변환합니다."""
        if pitch_int < 0 or pitch_int > 127:
            raise ValueError("Pitch integer must be between 0 and 127.")
        pitch_class = pitch_int % 12
        octave = pitch_int // 12 - 1
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return f"{note_names[pitch_class]}{octave}"
    
    def _get_midi(self):
        """MIDI 데이터를 생성합니다."""
        s = stream.Score() # type: ignore
        melody_part = stream.Part() # type: ignore
        chord_part = stream.Part() # type: ignore
        bass_part = stream.Part() # type: ignore

        for i in self.melody:
            if i["note"] == '':
                melody_part.append(note.Rest(quarterLength=i["duration"]))
            else:
                melody_part.append(note.Note(i["note"], quarterLength=i["duration"]))

        for token in self.chords:
            if token["chord"] == "":
                chord_part.append(note.Rest(quarterLength=token["duration"]))
            else:
                if token["chord"].split("/")[0] == "":
                    chord_part.append(note.Note(token["chord"].split("/")[1], quarterLength=token["duration"]))
                    continue
                chord = pychord_chord(token["chord"].split("/")[0])
                pitches = chord.components_with_pitch(root_pitch=4)  # C4 기준으로 음표 생성
                # 음표 이름을 Pitch 객체로 변환
                converted_pitches = []
                for p in pitches:
                    pitch_obj = pitch.Pitch(p)
                    # C#5(=midi 73) 이상이면 한 옥타브 내림
                    if pitch_obj.midi >= 73:
                        pitch_obj.midi -= 12
                    converted_pitches.append(pitch_obj)
                
                chord_part.append(music21_chord.Chord(converted_pitches, quarterLength=token["duration"]))

        for i in self.bass:
            if i["note"] == '':
                bass_part.append(note.Rest(quarterLength=i["duration"]))
            else:
                bass_part.append(note.Note(i["note"], quarterLength=i["duration"]))

        s.insert(0, melody_part)
        s.insert(0, chord_part)
        s.insert(0, bass_part)
        return s

    def _note_list_to_chord(self, note_tuple:tuple[pitch.Pitch]):
        """음표 이름 목록을 코드 표현으로 변환합니다."""
        if not note_tuple:
            return ''
        
        note_list = list(set([n.name.replace("-", "b") for n in note_tuple]))  # 중복 제거 및 b 플랫 처리
        note_list.sort()
        chord = find_chords_from_notes(note_list)
        
        chord_name:str = chord[0].chord
        if "/" in chord_name:
            return chord_name.split("/")[0]  # 코드 이름만 반환

        return chord_name  

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
    
    def set_id(self, token_id) -> None:
        """HarmonyMIDIToken에 대한 토큰 ID를 설정한다."""

    def to_json(self):
        return json.dumps({
            'BPM': self.bpm,
            'Melody': self.melody,
            'Chord': self.chords,
            'Bass': self.bass
        })
    
    def to_midi(self):
        if self._midi is None: #TODO: 미디가 없으면 저장된 값으로 미디 생성
            self._midi = self._get_midi()

        return self._midi
    
    def set_midi(self, midi_file) -> None:
        midi_data = converter.parse(midi_file)
        self._midi = copy.deepcopy(midi_data) # MIDI 데이터를 저장

        if midi_data.metronomeMarkBoundaries(): # 메트로놈 마크가 있는 경우 첫 번째 마크의 BPM을 사용
            self.bpm = int(midi_data.metronomeMarkBoundaries()[0][2].number)

        for e in midi_data.flat.notesAndRests: # 모든 음표와 쉼표 가져옴
            if isinstance(e, note.Rest):
                self.melody.append({'note': '', 'duration': e.quarterLength})
                self.chords.append({'chord': '', 'duration': e.quarterLength})
                self.bass.append({'note': '', 'duration': e.quarterLength})
            elif isinstance(e, music21_chord.Chord):
                has_high_pitch = False
                has_low_pitch = False

                for i in e.pitches:
                    if i.midi > 72: # C#5 이상인 음은 멜로디로 처리
                        has_high_pitch = True

                        pitch_list = list(e.pitches)
                        pitch_list.remove(i)  # 높은 음 제거
                        e.pitches = tuple(pitch_list)

                        self.melody.append({
                            'note': self._intpitch_to_note_name(i.midi),
                            'duration': e.quarterLength
                        })
                    if i.midi < 60: # C4 이하인 음은 베이스로 처리
                        has_low_pitch = True

                        pitch_list = list(e.pitches)
                        pitch_list.remove(i)  # 높은 음 제거
                        e.pitches = tuple(pitch_list)

                        self.bass.append({
                            'note': self._intpitch_to_note_name(i.midi),
                            'duration': e.quarterLength
                        })

                self.chords.append({
                    'chord': self._note_list_to_chord(e.pitches), # type: ignore
                    'duration': e.quarterLength
                })

                if not has_high_pitch:  # 높은 음이 없으면 멜로디는 Rest
                    self.melody.append({
                        'note': '',
                        'duration': e.quarterLength
                    })
                if not has_low_pitch:  # 낮은 음이 없으면 베이스는 Rest
                    self.bass.append({
                        'note': '',
                        'duration': e.quarterLength
                    })
            elif isinstance(e, note.Note):
                if e.pitch.midi > 72: # C#5 이상인 음은 멜로디로 처리
                    self.melody.append({
                        'note': self._intpitch_to_note_name(e.pitch.midi),
                        'duration': e.quarterLength
                    })
                    self.chords.append({
                        'chord': '',
                        'duration': e.quarterLength
                    })
                    self.bass.append({
                        'bass': '',
                        'duration': e.quarterLength
                    })
                else: # 분명 노트인데 멜로디가 아닌 경우
                    self.bass.append({
                        'bass': self._intpitch_to_note_name(e.pitch.midi),
                        'duration': e.quarterLength
                    }) # 베이스 노트로 처리
                    self.chords.append({
                        'chord': '',
                        'duration': e.quarterLength
                    })
                    self.melody.append({
                        'note': '',
                        'duration': e.quarterLength
                    })
