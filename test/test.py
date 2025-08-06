from HarmonyMIDIToken import HarmonyMIDIToken as Tokenizer
import json

MIDI = Tokenizer()
MIDI.set_midi('test/test.mid')

MIDI._midi = None  # Reset MIDI to None to test the generation of MIDI from stored values

with open('test/test.json', 'w') as f:
    dic = json.loads(MIDI.to_json())

    dic["Melody"] = dic["Melody"][:3]
    dic["Chord"] = dic["Chord"][:3]
    dic["Bass"] = dic["Bass"][:3] # 예시용 json이라 대충 자름

    f.write(json.dumps(dic))

midi= MIDI.to_midi() # This should generate MIDI from the stored melody and chords
midi.write('midi', fp='test/test_output.mid')  # Save the generated MIDI to a file