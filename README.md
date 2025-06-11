# Google reCAPTCHA Audio Solver with Playwright (Async)

This project is inspired by [GoogleRecaptchaBypass](https://github.com/sarperavci/GoogleRecaptchaBypass), but uses **Playwright (async version)** for browser automation and leverages **system audio recording + Vosk speech recognition** to solve **Google reCAPTCHA audio challenges**.

> ⚠️ This tool is intended for educational and research purposes only. Please use responsibly and in compliance with applicable laws and service terms.

---

## 🧠 Features

- Asynchronous implementation using `async/await` and Playwright's async API.
- Detects and handles reCAPTCHA checkbox and audio challenge interface.
- Records system audio output during the CAPTCHA playback.
- Uses [Vosk](https://alphacephei.com/vosk/) (offline speech-to-text) to recognize the spoken text from the audio.
- Mimics human behavior using random delays and mouse movement.
- Cleans up temporary files after execution.

---

## 🔧 Requirements

Make sure you have the following installed:

### Python Libraries:
```bash
pip install playwright vosk soundcard pyaudio numpy
