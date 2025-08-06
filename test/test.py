from HarmonyMIDIToken import HarmonyMIDIToken as Tokenizer
from pychord import find_chords_from_notes, Chord as pychord_chord
import json

MIDI = Tokenizer()
MIDI.set_id([128, 100, 10, 78, 2, 10, -1, 2, 10, 78, 1, 10, 78, 1, 10, 78, 1, 10, 85, 2, 10, -1, 3, 10, 80, 2, 10, 78, 2, 10, 78, 2, 10, -1, 2, 10, 78, 1, 10, 78, 1, 10, 78, 1, 10, 77, 2, 10, -1, 3, 10, 78, 2, 10, 77, 2, 10, 75, 4, 10, 73, 1, 10, 75, 1, 10, -1, 1, 10, 75, 1, 10, -1, 1, 10, 75, 1, 10, 75, 1, 10, -1, 1, 10, 75, 4, 10, 77, 4, 10, 75, 1, 10, 77, 1, 10, -1, 1, 10, 77, 1, 10, -1, 1, 10, 77, 1, 10, 75, 1, 10, -1, 1, 10, 77, 2, 10, 78, 2, 200, 20, 63, 2, 2, 20, -1, 20, 63, 2, 1, 20, 63, 2, 1, 20, 63, 2, 1, 20, 63, 2, 2, 20, -1, 20, 63, 2, 2, 20, 63, 2, 2, 20, 66, 1, 2, 20, -1, 20, 66, 1, 1, 20, 66, 1, 1, 20, 66, 1, 1, 20, 66, 1, 2, 20, -1, 20, 66, 1, 2, 20, 66, 1, 2, 20, 71, 1, 4, 20, 71, 1, 1, 20, 71, 1, 1, 20, -1, 20, 71, 1, 1, 20, -1, 20, 71, 1, 1, 20, 71, 1, 1, 20, -1, 20, 71, 1, 4, 20, 61, 1, 4, 20, 61, 1, 1, 20, 61, 1, 1, 20, -1, 20, 61, 1, 1, 20, -1, 20, 61, 1, 1, 20, 61, 1, 1, 20, -1, 20, 61, 1, 2, 20, 61, 1, 2, 300, 10, 51, 2, 10, -1, 2, 10, 51, 1, 10, -1, 1, 10, -1, 1, 10, 51, 2, 10, -1, 3, 10, 51, 2, 10, 51, 2, 10, 54, 2, 10, -1, 2, 10, 54, 1, 10, -1, 1, 10, -1, 1, 10, 54, 2, 10, -1, 3, 10, 54, 2, 10, 54, 2, 10, 47, 4, 10, 47, 1, 10, 47, 1, 10, -1, 1, 10, 47, 1, 10, -1, 1, 10, 47, 1, 10, 47, 1, 10, -1, 1, 10, 47, 4, 10, 49, 4, 10, 49, 1, 10, 49, 1, 10, -1, 1, 10, 49, 1, 10, -1, 1, 10, 49, 1, 10, 49, 1, 10, -1, 1, 10, 49, 2, 10, 49, 2])
# MIDI.set_midi('test/test.mid')

# MIDI._midi = None  # Reset MIDI to None to test the generation of MIDI from stored values

print(MIDI.to_json())
with open('test/test.json', 'w') as f:
    dic = json.loads(MIDI.to_json())

    dic["Melody"] = dic["Melody"][:3]
    dic["Chord"] = dic["Chord"][:3]
    dic["Bass"] = dic["Bass"][:3] # 예시용 json이라 대충 자름

    f.write(json.dumps(dic))

midi= MIDI.to_midi() # This should generate MIDI from the stored melody and chords
midi.write('midi', fp='test/test_output.mid')  # Save the generated MIDI to a file

#print(MIDI.token_id)  # Print the token ID to verify the output