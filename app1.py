from flask import Flask, render_template, request, jsonify
import speech_recognition as spr
from googletrans import Translator
from gtts import gTTS
import os

app = Flask(__name__)

# Create Recognizer and Microphone objects
recog1 = spr.Recognizer()
mc = spr.Microphone()

# Language mapping
def get_language_map():
    return {
        'Hindi': 'hi',
        'Telugu': 'te',
        'Kannada': 'kn',
        'Tamil': 'ta',
        'Malayalam': 'ml',
        'Bengali': 'bn',
        'English': 'en'
    }

# Speech recognition function
def recognize_speech():
    try:
        with mc as source:
            recog1.adjust_for_ambient_noise(source, duration=0.2)
            audio = recog1.listen(source)
            recognized_text = recog1.recognize_google(audio)
            return recognized_text
    except spr.UnknownValueError:
        return "Google Speech Recognition could not understand the audio."
    except spr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"

@app.route('/')
def home():
    languages = get_language_map().keys()
    return render_template('index.html', languages=languages)

@app.route('/translate', methods=['POST'])
def translate():
    # Get the selected target language
    target_language = request.form['language']
    language_map = get_language_map()

    if target_language not in language_map:
        return jsonify({"error": "Invalid language selected."}), 400

    target_language_code = language_map[target_language]

    # Recognize speech
    recognized_text = recognize_speech()

    if "could not understand" in recognized_text.lower() or "could not request" in recognized_text.lower():
        return jsonify({"error": recognized_text}), 400

    # Translate the recognized text
    translator = Translator()
    detected_language = translator.detect(recognized_text).lang
    translated_text = translator.translate(recognized_text, src=detected_language, dest=target_language_code).text

    # Generate audio for the translated text
    try:
        if not os.path.exists('static/audio'):
            os.makedirs('static/audio')

        audio_file = f"static/audio/captured_voice_{target_language}.mp3"
        speak = gTTS(text=translated_text, lang=target_language_code, slow=False)
        speak.save(audio_file)

        return jsonify({
            "recognized_text": recognized_text,
            "detected_language": detected_language,
            "translated_text": translated_text,
            "audio_file": audio_file
        })
    except Exception as e:
        return jsonify({"error": f"An error occurred during audio generation: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
