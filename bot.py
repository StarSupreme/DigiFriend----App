import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.uix.image import Image

from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from gtts import gTTS
import os
import speech_recognition as sr
import numpy as np
import threading
from demo import perform_real_time_prediction

kivy.require('2.3.0')  # replace with your current kivy version

class ChatApp(App):
    def build(self):
        self.title = "Emotion-based ChatBot"
        self.final_emotion = None
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=(10, 10))
        self.output_label = Label(text="Initializing Emotion Prediction...", size_hint_y=None, height=40)
        self.layout.add_widget(self.output_label)

        self.user_input = TextInput(multiline=False, size_hint_y=None, height=40)
        self.layout.add_widget(self.user_input)

        self.send_button = Button(text="Speak", on_press=self.listen_and_send, size_hint_y=None, height=40)
        self.layout.add_widget(self.send_button)

        # Initialize chatbot and training data
        self.bot = ChatBot('MyBot')
        self.trainer = ListTrainer(self.bot)
        self.load_training_data()

        self.sound = None

        # Schedule the emotion prediction at the start
        Clock.schedule_once(lambda dt: self.predict_emotion_and_display(), 0.1)
        Clock.schedule_once(lambda dt: self.listen_and_send(None), 0.1)

        return self.layout

    def load_training_data(self):
        # Check if final_emotion is available
        if not self.final_emotion:
            return

        corpus_file = get_corpus_file_path(self.final_emotion)
        if not os.path.exists(corpus_file):
            print(f"Training data file not found: {corpus_file}")
            return

        with open(corpus_file, 'r') as file:
            training_data = file.readlines()
        self.trainer.train(training_data)

    def predict_emotion_and_display(self):
        # Predict emotion at the start
        self.final_emotion = perform_real_time_prediction()

        # Display the corresponding emoji
        emoji_url = get_emoji_url(self.final_emotion)
        emoji_image = Image(source=emoji_url, size=(100, 100))
        self.layout.add_widget(emoji_image)

        # Update the output label
        self.output_label.text = f"Bot: Someone seems {self.final_emotion.capitalize()}!"
        t = "Someone seems Happy!"
        self.speak(t)

        # Load training data after predicting the emotion
        self.load_training_data()

        # Automatically trigger microphone listening after displaying the emoji
        Clock.schedule_once(lambda dt: self.listen_and_send(None), 0.1)

    def listen_and_send(self, instance):
        # Check if a listening thread is already running
        if hasattr(self, 'listen_thread') and self.listen_thread.is_alive():
            print("Already listening...")
            return
        # Start a new thread for listening
        self.listen_thread = threading.Thread(target=self.check_microphone)
        self.listen_thread.start()

    def check_microphone(self):
        # Listen to the user's voice input
        user_input = self.listen_to_microphone()

        if user_input.lower() == 'exit':
            self.stop_listening()
            return

        response = self.bot.get_response(user_input).text

        # Schedule the update in the next frame
        Clock.schedule_once(lambda dt: self.update_label(response))

        self.speak(response)

        if user_input.lower() == "yes let's go":
            self.end_chat()

        # Stop listening thread
        self.stop_listening()

    def stop_listening(self):
        if hasattr(self, 'listen_thread') and self.listen_thread.is_alive():
            # Wait for the thread to finish
            self.listen_thread.join()
        
    def update_label(self, response):
        # Update the Kivy label with the new response
        self.layout.remove_widget(self.output_label)
        self.output_label = Label(text=f"Bot: {response}", size_hint_y=None, height=40)
        self.layout.add_widget(self.output_label)

        # Automatically trigger microphone listening after each dialogue
        Clock.schedule_once(lambda dt: self.listen_and_send(None), 0.1)

    def speak(self, text):
        tts = gTTS(text=text, lang='en')
        tts.save('output.mp3')

        # Load and play the audio
        self.sound = SoundLoader.load('output.mp3')
        if self.sound:
            self.sound.play()
    
    def end_chat(self):
        db_file_path = "C:/Users/Aadit/Downloads/materials-chatterbot (2)/materials-chatterbot/source_code_final/db.sqlite3"  # Replace with the actual path
        if os.path.exists(db_file_path):
            os.remove(db_file_path)
            print("db.sqlite file deleted.")
        else:
            print("db.sqlite file not found.")

        # Stop the app
        App.get_running_app().stop()
    
    def listen_to_microphone(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Say something:")
            audio = recognizer.listen(source)

        try:
            user_input = recognizer.recognize_google(audio)
            print(f"User said: {user_input}")
            return user_input
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""


def get_corpus_file_path(emotion):
    base_path = "C:/Users/Aadit/Downloads/materials-chatterbot (2)/materials-chatterbot/source_code_final/chats/"
    if emotion == 'neutral':
        return os.path.join(base_path, "chat.txt")
    else:
        return os.path.join(base_path, f"{emotion}.txt")


# Add a function to get the emoji URL based on the emotion
def get_emoji_url(emotion):
    emoji_urls = {
        'happy': 'C:/Users/Aadit/OneDrive/Pictures/happy.png',
        'sad': 'C:/Users/Aadit/OneDrive/Pictures/sad.png',
        'angry': 'C:/Users/Aadit/OneDrive/Pictures/angry.png',
        'fear': 'C:/Users/Aadit/OneDrive/Pictures/fear.png',
        'disgust':'C:/Users/Aadit/OneDrive/Pictures/disgust.png',
        'surprise': 'C:/Users/Aadit/OneDrive/Pictures/surprise.png',
        'neutral': 'C:/Users/Aadit/OneDrive/Pictures/neutral.png',
    }
    return emoji_urls.get(emotion, '')


if __name__ == '__main__':
    ChatApp().run()

