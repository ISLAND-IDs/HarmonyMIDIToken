from music21 import note, chord as music21_chord, pitch, stream, tempo
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
    
    def _note_name_to_intpitch(self, note_name:str) -> int:
        """음표 이름을 MIDI 피치 정수로 변환합니다."""
        if note_name == '':
            return -1
        pitch_obj = pitch.Pitch(note_name)
        return pitch_obj.midi
    
    def _note_dict_to_part(self, note_list:list[dict]) -> stream.Part: # type: ignore
        """음표 딕셔너리 리스트를 music21 Part 객체로 변환합니다."""
        part = stream.Part() # type: ignore

        for i in note_list:
            if i["note"] == '':
                part.append(note.Rest(quarterLength=i["duration"]))
            else:
                part.append(note.Note(i["note"], quarterLength=i["duration"]))

        return part
    
    def _chord_dict_to_part(self, chord_list:list[dict]) -> stream.Part: # type: ignore
        """코드 딕셔너리 리스트를 music21 Part 객체로 변환합니다."""
        part = stream.Part() # type: ignore

        for token in chord_list:
            if token["chord"] == "":
                part.append(note.Rest(quarterLength=token["duration"]))
            else:
                chord = pychord_chord(token["chord"])
                pitches = chord.components_with_pitch(root_pitch=4)  # C4 기준으로 음표 생성
                # 음표 이름을 Pitch 객체로 변환
                converted_pitches = []
                for p in pitches:
                    pitch_obj = pitch.Pitch(p)
                    # C#5(=midi 73) 이상이면 한 옥타브 내림
                    if pitch_obj.midi >= 73:
                        pitch_obj.midi -= 12
                    converted_pitches.append(pitch_obj)
                
                part.append(music21_chord.Chord(converted_pitches, quarterLength=token["duration"]))

        return part
    
    def _get_midi(self):
        """MIDI 데이터를 생성합니다."""
        s = stream.Score() # type: ignore
        s.append(tempo.MetronomeMark(number=self.bpm))

        s.insert(0, self._note_dict_to_part(self.melody))
        s.insert(0, self._chord_dict_to_part(self.chords))
        s.insert(0, self._note_dict_to_part(self.bass))
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
    
    @property
    def token_id(self) -> list[list[int]]:
        """
        Melody, Chords, Bass 데이터를 LSTM 학습용 시퀀스로 변환합니다.
        각 타임스텝은 [melody_pitch, melody_dur, chord_root, chord_quality, chord_dur, bass_pitch, bass_dur] 형태.
        """
        quality_map = {
            '': 1, 'M': 1, 'm': 2, '7': 3, 'M7': 4, 'm7': 5,
            'dim': 6, 'aug': 7, 'sus2': 8, 'sus4': 9,
            "dom7": 10, "half-dim": 11, "dim7": 12, "power": 13,
        }

        seq = []
        main_time = 0

        melody_time = 0
        chord_time = 0
        bass_time = 0

        melody_end = False
        chord_end = False
        bass_end = False

        while not (melody_end and chord_end and bass_end):
            if melody_time <= main_time:
                try:
                    m = self.melody.pop(0)
                    m_pitch = self._note_name_to_intpitch(m["note"])
                    m_dur = int(m["duration"]*4)
                except:
                    melody_end = True
            else:
                m_pitch = 0
                m_dur = 0

            if chord_time <= main_time:
                try:
                    c = self.chords.pop(0)
                    chord_obj =  pychord_chord(c["chord"])
                    chord_root = self._note_name_to_intpitch(chord_obj._root+"4")
                    chord_quality = quality_map.get(str(chord_obj._quality), 1)  # 기본은 1
                    c_dur = int(c["duration"]*4)
                except:
                    chord_end = True
            else:
                chord_root = 0
                chord_quality = 1
                c_dur = 0

            if bass_time <= main_time:
                try:
                    b = self.bass.pop(0)
                    b_pitch = self._note_name_to_intpitch(b["note"])
                    b_dur = int(b["duration"]*4)
                except:
                    bass_end = True
                    break
            else:
                b_pitch = 0
                b_dur = 0

            durs = list(set([m_dur, c_dur, b_dur]))
            durs = [item for item in durs if item != 0]

            main_time += min(durs)
            
            melody_time += m_dur
            chord_time += c_dur
            bass_time += b_dur

            seq.append([m_pitch, m_dur, chord_root, chord_quality, c_dur, b_pitch, b_dur])

        self.set_id(seq) # 제거된 딕셔너리들 돌려주기
        return seq  # (T,7)

    def set_id(self, seq: list[list[int]]):
        """
        LSTM 출력 시퀀스(정수 배열)를 Melody, Chords, Bass JSON 형식으로 되돌립니다.
        """
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
            13: 'power'
        }

        for step in seq:
            mel_pitch, mel_dur, root_pitch, quality_id, chord_dur, bass_pitch, bass_dur = step

            # Melody
            if mel_pitch != 0:
                self.melody.append({"note": self._intpitch_to_note_name(mel_pitch), "duration": mel_dur/4})
            else:
                if mel_dur > 0:
                    self.melody.append({"note": "", "duration": mel_dur/4})

            # Chord
            if root_pitch != 0:
                chord_name = self._intpitch_to_note_name(root_pitch)[:-1] + inverse_quality_map.get(quality_id, '')
                self.chords.append({"chord": chord_name, "duration": chord_dur/4})
            else:
                if chord_dur > 0:
                    self.chords.append({"chord": "", "duration": chord_dur/4})

            # Bass
            if bass_pitch != 0:
                self.bass.append({"note": self._intpitch_to_note_name(bass_pitch), "duration": bass_dur/4})
            else:
                if bass_dur > 0:
                    self.bass.append({"note": "", "duration": bass_dur/4})

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
                if e.pitches: # 남은 음이 있으면 코드로 처리
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
