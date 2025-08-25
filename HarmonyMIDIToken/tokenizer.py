from music21 import note, chord as music21_chord, pitch, stream
from pychord import find_chords_from_notes, Chord as pychord_chord
from music21.midi import translate
import json
import copy

class HarmonyMIDIToken:
    def __init__(self):
        self.bpm = 128 # 기본값
        self.melody:list[dict] = []
        self.chords:list[dict] = []
        self.bass:list[dict] = []
        self._midi = None # MIDI 파일을 저장할 변수 최적화를 위해서임 진짜로 귀찮아서 날먹하는 거 아님

    def _intpitch_to_note_name(self, pitch_int:int) -> str:
        """MIDI 피치 정수를 음표 이름으로 변환합니다."""
        if pitch_int < 0 or pitch_int > 127:
            return ''  # 유효하지 않은 피치 정수는 빈 문자열로 처리
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
        try:
            note_list = list(set([n.name.replace("-", "b") for n in note_tuple]))  # 중복 제거 및 b 플랫 처리
            note_list.sort()
            chord = find_chords_from_notes(note_list)
        except Exception:
            # pychord가 못 알아보는 조합이면 코드 없음 처리
            return ""
        
        # 화음이 없으면 코드 없음 처리
        if not note_list or not chord:
            return "" 
        
        chord_name:str = chord[0].chord
        if "/" in chord_name:
            return chord_name.split("/")[0]  # 코드 이름만 반환

        return chord_name
    
    def _note_name_to_intpitch(self, note_name:str) -> int:
        """음표 이름을 MIDI 피치 정수로 변환합니다."""
        if note_name == '':
            return -1
        pitch_obj = pitch.Pitch(note_name)
        return pitch_obj.midi
    
    def _tokenize(self, data:list[dict]) -> list[int]:
        """데이터를 토큰화합니다."""
        tokens = []
        quality_map = {
            '':1, 'M': 1, 'm': 2, '7': 3, 'M7': 4, 'm7': 5, 'dim': 6, 'aug': 7,'sus2': 8, 'sus4': 9, "dom7": 10, "half-dim": 11, "dim7": 12, "power": 13,
        }

        for i in data:
            key, value = next(iter(i.items()))

            if key == 'note':
                tokens.append(10)
                tokens.append(self._note_name_to_intpitch(value))
                tokens.append(int(i["duration"]*4)) # 4를 곱해서 양자화
            elif key == 'chord':
                tokens.append(20)
                if value == '':
                    tokens.append(-1)
                else:
                    chord = pychord_chord(value)

                    tokens.append(self._note_name_to_intpitch(chord._root+"4"))
                    try:
                        tokens.append(quality_map[str(chord._quality)])
                    except KeyError:
                        tokens.append(-1)
                    
                    for j in chord._appended:
                        tokens.append(self._note_name_to_intpitch(j+"4"))

                tokens.append(int(i["duration"]*4)) # 4를 곱해서 양자화
        return tokens
    
    def _detokenize_note(self, token:list[int]) -> list[dict]:
        """토큰을 음표로 디토큰화합니다."""

        output = []

        for idx, value in enumerate(token):
            if value == 10:  # Note 시작
                output.append({"note":self._intpitch_to_note_name(token[idx+1]), "duration": token[idx+2]/4})

        return output
    
    def _detokenize_chord(self, token:list[int]) -> list[dict]:
        """토큰을 코드로 디토큰화합니다."""
        output = []
        inverse_quality_map = {
            1: '', 
            2: 'm',
            3: '7',
            4: 'M7',
            5: 'm7',
            6: 'dim',
            7: 'aug',
            8: 'sus2',
            9: 'sus4',
            10: 'dom7',
            11: 'half-dim',
            12: 'dim7',
            13: 'power',
            -1: ''
        }

        list_str:str = "|".join([str(i) for i in token])  # 리스트를 문자열로 변환
        for i in list_str.split("20"):
            if i == '':
                continue

            chord_list = i.split("|")

            if chord_list[1] == '-1':
                output.append({"chord": "", "duration": float(chord_list[-2])/4})
            else:
                output.append({"chord":self._intpitch_to_note_name(int(chord_list[1]))[:-1]+inverse_quality_map[int(chord_list[2])], "duration": float(chord_list[-2])/4})

        return output

    @property
    def token_id(self) -> list[int]:
        """HarmonyMIDIToken에 대한 토큰 ID를 반환한다."""
        melody_tokens = self._tokenize(self.melody)
        chords_tokens = self._tokenize(self.chords)
        bass_tokens = self._tokenize(self.bass)

        token = [self.bpm, 100] + melody_tokens +[200]+ chords_tokens +[300]+ bass_tokens

        return token
    
    def set_id(self, token_id) -> None:
        """HarmonyMIDIToken에 대한 토큰 ID를 설정한다."""
        self.bpm = token_id[0]
        melody_tokens = token_id[2:token_id.index(200)]
        chords_tokens = token_id[token_id.index(200)+1:token_id.index(300)]
        bass_tokens = token_id[token_id.index(300)+1:]

        self.melody = self._detokenize_note(melody_tokens)
        self.chords = self._detokenize_chord(chords_tokens)
        self.bass = self._detokenize_note(bass_tokens)

    def to_json(self):
        return json.dumps({
            'BPM': self.bpm,
            'Melody': self.melody,
            'Chord': self.chords,
            'Bass': self.bass
        })

    def to_midi(self):
        if self._midi is None:
            self._midi = self._get_midi()

        return self._midi

    def set_midi(self, midi_file) -> None:
        midi_data = translate.midiFilePathToStream(midi_file)
        self._midi = copy.deepcopy(midi_data) # MIDI 데이터를 저장

        melody_time = 0.0
        chord_time = 0.0
        bass_time = 0.0

        if midi_data.metronomeMarkBoundaries(): # 메트로놈 마크가 있는 경우 첫 번째 마크의 BPM을 사용
            self.bpm = int(midi_data.metronomeMarkBoundaries()[0][2].number)

        for e in midi_data.flat.notes: # 모든 음표와 쉼표 가져옴
            if isinstance(e, music21_chord.Chord):
                print(e.pitches)
                for i in e.pitches:

                    if i.midi > 72: # C#5 이상인 음은 멜로디로 처리
                        pitch_list = list(e.pitches)
                        pitch_list.remove(i)  # 높은 음 제거
                        e.pitches = tuple(pitch_list)

                        if melody_time != float(e.offset):
                            self.melody.append({
                                'note': "",
                                'duration': float(e.offset) - melody_time
                            })

                            melody_time = float(e.offset)

                        self.melody.append({
                            'note': self._intpitch_to_note_name(i.midi),
                            'duration': float(e.quarterLength)
                        })

                        melody_time += float(e.quarterLength)
                    if i.midi < 60: # C4 이하인 음은 베이스로 처리
                        pitch_list = list(e.pitches)
                        pitch_list.remove(i)  # 낮은 음 제거
                        e.pitches = tuple(pitch_list)

                        if bass_time != float(e.offset):
                            self.bass.append({
                                'note': "",
                                'duration': float(e.offset) - bass_time
                            })

                            bass_time = float(e.offset)

                        self.bass.append({
                            'note': self._intpitch_to_note_name(i.midi),
                            'duration': float(e.quarterLength)
                        })

                        bass_time += float(e.quarterLength)

                print(f"offset: {e.offset} chord time: {chord_time}")
                
                if chord_time != float(e.offset):
                    self.chords.append({
                        'chord': "",
                        'duration': float(e.offset) - chord_time
                    })
                    chord_time = float(e.offset)
                self.chords.append({
                    'chord': self._note_list_to_chord(e.pitches), # type: ignore
                    'duration': float(e.quarterLength)
                })
                chord_time += float(e.quarterLength)
            elif isinstance(e, note.Note):
                if e.pitch.midi > 72: # C#5 이상인 음은 멜로디로 처리
                    if melody_time != float(e.offset):
                        self.melody.append({
                            'note': "",
                            'duration': float(e.offset) - melody_time
                        })

                        melody_time = float(e.offset)

                    self.melody.append({
                        'note': self._intpitch_to_note_name(e.pitch.midi),
                        'duration': float(e.quarterLength)
                    })

                    melody_time += float(e.quarterLength)
                else: # 분명 노트인데 멜로디가 아닌 경우
                    if bass_time != float(e.offset):
                        self.bass.append({
                            'note': "",
                            'duration': float(e.offset) - bass_time
                        })
                        bass_time = float(e.offset)
                    self.bass.append({
                        'note': self._intpitch_to_note_name(e.pitch.midi),
                        'duration': float(e.quarterLength)
                    }) # 베이스 노트로 처리

                    bass_time += float(e.quarterLength)
