from HarmonyMIDIToken import HarmonyMIDIToken as Tokenizer
import json

MIDI = Tokenizer()
MIDI.set_midi('test/test.mid')

MIDI._midi = None  # Reset MIDI to None to test the generation of MIDI from stored values

with open('test/test.json', 'w') as f:
    f.write(MIDI.to_json())

midi= MIDI.to_midi() # This should generate MIDI from the stored melody and chords
midi.write('midi', fp='test/test_output.mid')  # Save the generated MIDI to a file