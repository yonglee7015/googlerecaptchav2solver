# Google reCAPTCHA Audio Bypass with Playwright

This project is inspired by [GoogleRecaptchaBypass](https://github.com/sarperavci/GoogleRecaptchaBypass), but instead of using traditional tools like Selenium or Puppeteer, I used **[Playwright](https://playwright.dev/)** for browser automation and implemented a method to handle **Google reCAPTCHA audio challenges** by **recording and processing the audio files**.

> ⚠️ This project is intended for educational and research purposes only. Please use it responsibly and in compliance with applicable laws and service terms.

## 🧠 Overview

This script automates the process of interacting with Google reCAPTCHA by:

1. Launching a browser via **Playwright**
2. Navigating to a target page with reCAPTCHA
3. Detecting when an audio CAPTCHA appears
4. Automatically clicking the audio challenge button
5. Recording the audio file provided by reCAPTCHA
6. (Optional) Processing the audio file (e.g., speech-to-text)

## 🔧 Requirements

Make sure you have the following installed:

- Python 3.x
- Playwright (`pip install playwright`)
- PyAudio (`pip install pyaudio`)
- SpeechRecognition (`pip install SpeechRecognition`)
- FFmpeg (optional, for audio conversion)

Install dependencies:
```bash
pip install playwright pyaudio SpeechRecognition
playwright install
