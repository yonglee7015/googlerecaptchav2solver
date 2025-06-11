import os
import tempfile
import random
import string
import asyncio
from playwright.async_api import async_playwright, Page
import wave
import json
from vosk import Model, KaldiRecognizer
import soundcard as sc
import pyaudio
import numpy as np  

os.environ["PATH"] += os.pathsep + r"D:\ffmpeg\bin"
model_path = r"vosk_model\vosk-model-small-en-us-0.15"
if not os.path.exists(model_path):
    print("can't find model!")
    exit(1)

model = Model(model_path)

class AsyncRecaptchaSolver:
    """A class to solve reCAPTCHA challenges using audio recognition (async version)."""
    # Constants
    TEMP_DIR = os.getenv("TEMP") if os.name == "nt" else "/tmp"
    TIMEOUT_STANDARD = 7000  # Playwright uses milliseconds
    TIMEOUT_SHORT = 1000
    TIMEOUT_DETECTION = 50

    def __init__(self, page: Page) -> None:
        """Initialize the solver with a Playwright Page instance.

        Args:
            page: Playwright Page instance for browser interaction
        """
        self.page = page
        self.temp_dir = tempfile.mkdtemp()  # Per-instance temp directory
        self.lock = asyncio.Lock()  # Async lock for shared resources
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.user_agent = random.choice(self.user_agents)

    async def solve_captcha(self) -> None:
        """Attempt to solve the reCAPTCHA challenge asynchronously.

        Raises:
            Exception: If captcha solving fails or bot is detected
        """
        try:
            challenge_frame = self.page.frame_locator('//iframe[@title="recaptcha challenge expires in two minutes"]')
            await challenge_frame.locator("#recaptcha-audio-button").wait_for(timeout=self.TIMEOUT_STANDARD)
            await challenge_frame.locator("#recaptcha-audio-button").click(timeout=self.TIMEOUT_SHORT)
            await asyncio.sleep(0.3)

            if await self.is_detected():
                raise Exception("Captcha detected bot behavior")
            
            await challenge_frame.locator("#\\:2").click(timeout=self.TIMEOUT_SHORT)
            await asyncio.sleep(0.5) 

            text_response = await self._process_audio_challenge()
            print(f"audio2text: {text_response}")
            if not text_response:
                raise Exception("No recognized text in audio")

            await challenge_frame.locator("#audio-response").fill(text_response.lower())
            await asyncio.sleep(1)
            
            await challenge_frame.locator("#recaptcha-verify-button").click()
            await asyncio.sleep(random.uniform(0.4, 1.2))
            
            if not await self.is_solved():
                raise Exception("Failed to solve the captcha")

        except Exception as e:
            raise Exception(f"Failed to solve the captcha: {str(e)}")

    async def _record_system_audio(self, duration=5):
        """
        Record system audio.
        :param duration: Recording duration in seconds.
        :return: Recorded audio data.
        """
        try:
            # Get the default speaker device
            loopback = sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True)
            # Start recording, identifying the loopback device
            with loopback.recorder(samplerate=16000, channels=1) as mic:
                audio_data = mic.record(numframes=int(16000 * duration))
            # Convert float32 data to int16 format
            audio_data_int16 = (audio_data * 32767).astype(np.int16)
            return audio_data_int16
        except Exception as e:
            print(f"Recorder audio error Message: {e}")
            return np.array([], dtype=np.int16)

    async def _process_audio_challenge(self) -> str:
        """Process the audio challenge and return the recognized text asynchronously.

        Returns:
            str: Recognized text from the audio file
        """
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        # Save audio file in current directory
        # wav_path = os.path.join(os.getcwd(), f"recaptcha_audio_{random_suffix}.wav")
        wav_path = os.path.join( self.temp_dir, f"recaptcha_audio_{random_suffix}.wav")

        try:
            # Start recording system audio after clicking the Play button
            audio_data = await self._record_system_audio()
            if audio_data.size == 0:
                return ""

            # Save as a WAV file using 16-bit PCM format
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(1)  # Explicitly set the number of channels to 1
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)  # Ensure the sampling rate is 16000Hz
                wf.writeframes(audio_data.tobytes())

            # Perform speech recognition
            with wave.open(wav_path, "rb") as wf:
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                    print("Audio must be 16-bit PCM WAV!")
                    return ""
                # Ensure the correct sampling rate is used during recognition
                rec = KaldiRecognizer(model, 16000)  
                partial_results = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get('text', '').strip()
                        if text:
                            partial_results.append(text)
                combined_text = ' '.join(partial_results).strip()
            async with self.lock:
                return combined_text
        except Exception as e:
            print(f"Audio processing error: {e}")
            return ""
        finally:
            # Uncomment or remove the following code to keep the audio file
            for path in (wav_path,):
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

    async def is_solved(self) -> bool:
        """Check if the captcha has been solved successfully."""
        try:
            checkbox = self.page.frame_locator('//iframe[@title="reCAPTCHA"]').locator(".recaptcha-checkbox-checkmark")
            style = await checkbox.get_attribute("style", timeout=self.TIMEOUT_SHORT)
            return style is not None
        except Exception:
            return False

    async def is_detected(self) -> bool:
        """Check if the bot has been detected."""
        try:
            return await self.page.get_by_text("Try again later").is_visible(timeout=self.TIMEOUT_DETECTION)
        except Exception:
            return False

    async def __aenter__(self):
        """Async context manager support"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary resources when used as async context manager"""
        self.cleanup()

    def cleanup(self):
        """Clean up temporary files"""
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception:
                    pass
        except Exception:
            pass

# Example usage:
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            headless=False, 
            user_data_dir="./user_data",
            args=[
            "--disable-blink-features=AutomationControlled",
            "--lang=en-US,en"
        ]
            )
        page = await browser.new_page()
        await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        await page.add_init_script("""
            delete navigator.__proto__.webdriver;
            window.chrome = {runtime: {}};
        """)
        await page.goto("https://www.google.com/recaptcha/api2/demo")
        
        solver = AsyncRecaptchaSolver(page)
        try:
            recaptcha_frame = page.frame_locator('//iframe[@title="reCAPTCHA"]')
            await recaptcha_frame.locator(".rc-anchor-content").wait_for(timeout=1000)
            await solver.solve_captcha()
        except Exception:
            print("No captcha popup found, skipping captcha solving.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())