import threading
from pydub import AudioSegment
from pydub.playback import play

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.threads = {}

    def add_sound(self, filename, name: str):
        """Add a sound to the sound manager."""
        sound = AudioSegment.from_file(filename)
        self.sounds[name] = sound

    def _play_sound(self, sound: AudioSegment):
        """Internal method to play sound in a separate thread."""
        play(sound)

    def play_sound(self, name: str):
        """Play a sound."""
        self._play_sound(self.sounds[name])
        return 
    
        if name in self.sounds:
            sound = self.sounds[name]
            thread = threading.Thread(target=self._play_sound, args=(sound,))
            thread.start()
            self.threads[name] = thread

    def stop_sound(self, name: str):
        """Stop a sound."""
        # pydub and simpleaudio do not support stopping a sound directly
        pass
