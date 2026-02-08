import time
import psutil
import pyautogui
import pyjokes
import datetime
import wikipedia
import webbrowser
import threading
import pywhatkit as kit
from playwright.sync_api import sync_playwright
import feedparser
from gtts import gTTS
import os
import requests

# --- Global Dictionaries ---

indian_languages = {
    "english": "en", "assamese": "as", "bengali": "bn", "bodo": "brx", "dogri": "doi",
    "gujarati": "gu", "hindi": "hi", "kannada": "kn", "kashmiri": "ks", "konkani": "kok",
    "maithili": "mai", "malayalam": "ml", "manipuri": "mni", "marathi": "mr", "nepali": "ne",
    "odia": "or", "punjabi": "pa", "sanskrit": "sa", "santali": "sat", "sindhi": "sd",
    "tamil": "ta", "telugu": "te", "tulu": "tcy", "urdu": "ur"
}

gtts_langs = {
    'af': 'Afrikaans', 'ar': 'Arabic', 'bg': 'Bulgarian', 'bn': 'Bengali', 'bs': 'Bosnian',
    'ca': 'Catalan', 'cs': 'Czech', 'cy': 'Welsh', 'da': 'Danish', 'de': 'German', 'el': 'Greek',
    'en': 'English', 'eo': 'Esperanto', 'es': 'Spanish', 'et': 'Estonian', 'fi': 'Finnish',
    'fr': 'French', 'gu': 'Gujarati', 'hi': 'Hindi', 'hr': 'Croatian', 'hu': 'Hungarian',
    'hy': 'Armenian', 'id': 'Indonesian', 'is': 'Icelandic', 'it': 'Italian', 'iw': 'Hebrew',
    'ja': 'Japanese', 'jw': 'Javanese', 'km': 'Khmer', 'kn': 'Kannada', 'ko': 'Korean',
    'la': 'Latin', 'lv': 'Latvian', 'mk': 'Macedonian', 'ms': 'Malay', 'ml': 'Malayalam',
    'mr': 'Marathi', 'my': 'Myanmar (Burmese)', 'ne': 'Nepali', 'nl': 'Dutch', 'no': 'Norwegian',
    'pl': 'Polish', 'pt': 'Portuguese', 'ro': 'Romanian', 'ru': 'Russian', 'si': 'Sinhala',
    'sk': 'Slovak', 'sq': 'Albanian', 'sr': 'Serbian', 'su': 'Sundanese', 'sv': 'Swedish',
    'sw': 'Swahili', 'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai', 'tl': 'Filipino',
    'tr': 'Turkish', 'uk': 'Ukrainian', 'ur': 'Urdu', 'vi': 'Vietnamese', 'zh-CN': 'Chinese',
    'zh-TW': 'Chinese (Mandarin/Taiwan)', 'zh': 'Chinese (Mandarin)'
}
gtts_langs = {str(key).lower(): str(value).lower() for key, value in gtts_langs.items()}

# Used to track target language for gTTS
to_lang = 'en'
lang = 'en-US' 

# --- Helper Functions ---

def get_lang_code(lang_name):
    for lang_code in gtts_langs:
        v = gtts_langs[lang_code]
        if v == lang_name:
            return lang_code
    return 'en'

def smart_speak(audio, original_speak_func):
    """
    Decides whether to use the main GUI speak function (pyttsx3) 
    or gTTS based on the target language.
    """
    global to_lang
    if to_lang == 'en':
        # Standard English: Use the main speak function normally
        original_speak_func(audio)
    else:
        # Foreign Language:
        # 1. First, show the translated text in the chat window 
        # (We tell main.py NOT to use the robotic voice so they don't overlap)
        original_speak_func(audio, output_voice=False)
        
        # 2. Then play the high-quality gTTS voice
        try:
            tts = gTTS(text=audio, lang=to_lang, slow=False)
            tts.save("temp.mp3")
            os.system("start temp.mp3")
            time.sleep(2.5)                  
            os.remove("temp.mp3")
            os.system("taskkill /f /im wmplayer.exe >nul 2>&1") 
        except Exception as e:
            # Fallback: if gTTS fails, just speak normally
            original_speak_func(audio)

def speak_translated(final_url_tr, original_speak_func):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            page.goto(final_url_tr)
            
            # 10s timeout to prevent crash
            page.wait_for_selector('span[jsname="W297wb"]', timeout=10000, state="visible")
            
            translated_text = page.query_selector('span[jsname="W297wb"]').inner_text()
            
            if translated_text.strip():
                smart_speak(translated_text, original_speak_func)
            else:
                original_speak_func("Sorry, I couldn't fetch the translated text.")
            
            browser.close()
    except Exception as e:
        print("Translation Error: Timeout or Browser issue.")
        original_speak_func("I could not get the translation in time.")

def cpu(speak_func):
    usage = str(psutil.cpu_percent())
    speak_func(f"CPU is at {usage} percent")
    battery = psutil.sensors_battery()
    if battery:
        speak_func(f"Battery is at {battery.percent} percent")

def get_missing_input(speak_func, take_command_func, prompt):
    """
    Helper to ask for input. 
    It asks the prompt once, then listens up to 3 times silently before cancelling.
    """
    speak_func(prompt)
    
    # Try 3 times total
    for _ in range(3):
        response = take_command_func()
        
        # If we got a valid response, return it immediately
        if response and response != "None":
            return response
    
    # If all 3 attempts failed
    speak_func("I didn't hear anything. Cancelling operation.")
    return ""

# --- Main Logic Function ---

def process_order(order, speak_func, take_command_func, addr):
    global to_lang, lang

    # --- Translation Logic ---
    if 'translate' in order:
        query = order.replace("translate", "").strip()
        tr1 = query.split()
        
        # Check if format is roughly "translate [lang1] to [lang2]"
        if len(tr1) < 3 or 'to' not in tr1:
             speak_func("Please say command like: translate Hindi to English")
             return True

        if tr1[0] in indian_languages and tr1[2] in indian_languages:
            from_lang_name = tr1[0]
            to_lang_name = tr1[2]
            
            # Determine input language code
            capture_lang_code = 'en-US'
            if indian_languages[from_lang_name] != 'en':
                capture_lang_code = indian_languages[from_lang_name] + '-IN'
            
            speak_func(f"Say the sentence in {from_lang_name}")
            
            # Pass language code to main.py
            sentence = take_command_func(language_code=capture_lang_code)
            
            if sentence and sentence != "None":
                to_lang = get_lang_code(to_lang_name)
                
                from_code = indian_languages[from_lang_name]
                to_code = indian_languages[to_lang_name]
                
                tr_text = sentence.replace(" ", "%20")
                url_tr = f"https://translate.google.com/?sl={from_code}&tl={to_code}&text={tr_text}%20&op=translate"
                speak_translated(url_tr, speak_func)
            else:
                speak_func("I didn't hear the sentence.")

            # Reset
            to_lang = 'en'
            return True
        else:
            speak_func("Sorry, those languages are not available.")
            return True

    # --- Social Interactions ---
    elif 'how are you' in order or 'how r u' in order:
        speak_func("I am fine, thank you.")
        speak_func(f"How are you {addr}?")
        return True

    elif 'fine' in order or 'good' in order:
        speak_func(f"It's good to know that you are fine.")
        return True

    elif 'who are you' in order or 'who r u' in order or 'hu r u' in order:
        speak_func(f"I am your personal assistant Emma.")
        speak_func(f"I am here to help you with your tasks")
        return True
    
    elif 'hello' in order:
        speak_func(f"Hello! How may I help you {addr}?.")
        return True

    # --- App & Web Controls ---
    elif 'open' in order:
        query = order.replace("open", "").strip()
        
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What application do you want to open?")
            if not query: return True
            
        speak_func("Opening " + query)
        pyautogui.press("super")
        pyautogui.typewrite(query)
        time.sleep(1) 
        pyautogui.press("enter")
        return True

    elif 'wikipedia' in order:
        query = order.replace("wikipedia", "").strip()
        
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What should I search on Wikipedia?")
            if not query: return True

        try:
            speak_func("Searching Wikipedia...")
            results = wikipedia.summary(query, sentences=2)
            speak_func("According to Wikipedia")
            speak_func(results)
        except wikipedia.exceptions.PageError:
            speak_func(f"Sorry, wikipedia page on {query} cannot be found")
        except Exception:
            speak_func("An error occurred while fetching data.")
        return True

    elif 'shop' in order:
        query = order.replace("shop", "").strip()
        
        if not query:
            query = get_missing_input(speak_func, take_command_func, "Where do you want to shop? For example, say 'shop Amazon'.")
            if not query: return True

        shop_websites = {
            "amazon": "https://www.amazon.in", "myntra": "https://www.myntra.com",
            "flipkart": "https://www.flipkart.com", "ebay": "https://www.ebay.com",
            "walmart": "https://www.walmart.com", "etsy": "https://www.etsy.com",
            "snapdeal": "https://www.snapdeal.com", "meesho" : "https://www.meesho.com"
        }
        
        for shop_name, url in shop_websites.items():
            if shop_name in query.lower():
                speak_func(f"Here you go to {shop_name.capitalize()}, {addr}. Happy shopping.")
                webbrowser.open(url)
                break
        else:
            speak_func("Sorry, I couldn't recognize the shopping website.")
        return True

    # --- Search Engines ---
    elif 'amazon' in order:
        query = order.replace("amazon", "").strip()
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What do you want to search on Amazon?")
            if not query: return True
            
        speak_func("Searching Amazon...")
        jo = '+'.join(query.split())
        webbrowser.open("https://www.amazon.in/s?k=" + jo)
        speak_func(f"Searched {query} on Amazon")
        return True
    
    elif 'flipkart' in order:
        query = order.replace("flipkart", "").strip()
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What do you want to search on Flipkart?")
            if not query: return True
            
        speak_func("Searching Flipkart...")
        jo = '%20'.join(query.split())
        webbrowser.open("https://www.flipkart.com/search?q=" + jo)
        speak_func(f"Searched {query} on Flipkart")
        return True

    elif 'myntra' in order:
        query = order.replace("myntra", "").strip()
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What do you want to search on Myntra?")
            if not query: return True
            
        speak_func("Searching Myntra...")
        jo = '-'.join(query.split())
        webbrowser.open("https://www.myntra.com/" + jo)
        speak_func(f"Searched {query} on Myntra")
        return True

    elif 'google' in order:
        query = order.replace("google", "").strip()
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What do you want to search on Google?")
            if not query: return True
            
        speak_func("Searching Google...")
        jo = '+'.join(query.split())
        webbrowser.open("https://google.com/search?q=" + jo)
        speak_func(f"Searched {query} on Google")
        return True

    elif 'youtube' in order:
        query = order.replace("youtube", "").strip()
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What video do you want to search on YouTube?")
            if not query: return True
            
        speak_func("Searching YouTube...")
        jo = '+'.join(query.split())
        webbrowser.open("https://www.youtube.com/results?search_query=" + jo)
        speak_func(f"Searched {query} on YouTube")
        return True

    elif 'where is' in order or 'locate' in order:
        query = order.replace("where is", "").replace("locate", "").strip()
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What location do you want to find?")
            if not query: return True
            
        speak_func(f"Locating {query}")
        webbrowser.open("https://www.google.com/maps/search/" + query.replace(" ", "+"))
        return True

    # --- System Tools ---
    elif 'time' in order:
        now_time = datetime.datetime.now().strftime("%H:%M")
        speak_func("Current time is " + str(now_time))
        return True

    elif 'date' in order:
        now_date = datetime.datetime.now().strftime("%d:%m:%Y")
        speak_func("Current date is " + str(now_date))
        return True

    elif 'note' in order:
        # Create folder if not exists
        folder_name = "saved_notes"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Check if user already specified action in the main command (e.g., "write note")
        if "write" in order:
            action = "write"
        elif "read" in order:
            action = "read"
        else:
            # Only ask if not specified
            action = get_missing_input(speak_func, take_command_func, "Do you want to write a note or read a note?")
        
        if action:
            if 'write' in action.lower():
                filename = get_missing_input(speak_func, take_command_func, "Please tell me the filename.")
                if filename:
                    safe_filename = filename.lower().replace(" ", "_") + ".txt"
                    filepath = os.path.join(folder_name, safe_filename)
                    
                    content = get_missing_input(speak_func, take_command_func, "What should I write?")
                    if content:
                        with open(filepath, 'a') as f:
                            f.write(content + "\n")
                        speak_func(f"Note saved to {safe_filename}")
            
            elif 'read' in action.lower():
                filename = get_missing_input(speak_func, take_command_func, "Please tell me the filename.")
                if filename:
                    safe_filename = filename.lower().replace(" ", "_") + ".txt"
                    filepath = os.path.join(folder_name, safe_filename)
                    
                    if os.path.exists(filepath):
                        speak_func(f"Reading {safe_filename}")
                        with open(filepath, 'r') as f:
                            notes = f.read()
                            speak_func(notes)
                    else:
                        speak_func(f"Sorry, I couldn't find a file named {safe_filename}")
            else:
                speak_func("Invalid option. Please say 'write' or 'read'.")
        return True

    elif 'joke' in order:
        speak_func(pyjokes.get_joke(language="en", category="neutral"))
        return True

    elif 'switch window' in order:
        pyautogui.keyDown('alt')
        pyautogui.press('tab')
        time.sleep(1)
        pyautogui.keyUp('alt')
        return True

    # --- NEW SCREENSHOT FEATURE (Separated Folder) ---
    elif 'screenshot' in order:
        folder_name = "screenshots"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        name = get_missing_input(speak_func, take_command_func, f"{addr}, please tell me the name for this file")
        if name:
            img = pyautogui.screenshot()
            safe_name = name.lower().replace(" ", "_") + ".jpg"
            filepath = os.path.join(folder_name, safe_name)
            
            img.save(filepath)
            speak_func(f"Screenshot saved as {safe_name}")
        return True

    elif 'cpu status' in order:
        cpu(speak_func)
        return True

    # --- News & Weather ---
    elif 'news' in order:
        try:
            url = "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
            news = feedparser.parse(url)
            speak_func("Top 5 headlines from Times of India")
            for entry in news.entries[:5]:
                speak_func(entry.title)
        except Exception:
            speak_func("Could not fetch news.")
        return True

    elif 'weather' in order:
        city = ""
        words = order.split()
        if len(words) > 1 and "weather" in words:
            if "in" in words:
                idx = words.index("in")
                if idx + 1 < len(words):
                    city = " ".join(words[idx+1:])

        if not city:
            city = get_missing_input(speak_func, take_command_func, "For which city do you want the weather?")
        
        if city:
            url = f"https://wttr.in/{city}?format=j1"
            try:
                response = requests.get(url)
                data = response.json()
                weather = data['current_condition'][0]
                temp = weather['temp_C']
                humidity = weather['humidity']
                desc = weather['weatherDesc'][0]['value']

                speak_func(f"Weather in {city}")
                speak_func(desc)
                speak_func(f"Temperature: {temp} degrees Celsius")
                speak_func(f"Humidity: {humidity} percent") 
            except Exception as e:
                speak_func("Unable to fetch weather report.")
        return True

    # --- Communication ---
    elif 'whatsapp' in order:
        number_str = get_missing_input(speak_func, take_command_func, "Please say the contact number")
        if not number_str: return True
        
        number_str = number_str.replace(" ", "")
        
        try:
            num = int(number_str)
            message = get_missing_input(speak_func, take_command_func, "Please say your message")
            
            if message:
                speak_func("Opening WhatsApp Web...")
                encoded_msg = message.replace(' ', '%20')

                webbrowser.open(f"https://web.whatsapp.com/send?phone=+91{num}&text={encoded_msg}")
            else:
                speak_func("No message provided.")
                
        except ValueError:
            speak_func("Invalid contact number format.")
        except Exception as e:
            speak_func("An error occurred while opening WhatsApp")
        return True
    
    # --- CALCULATOR FEATURE ---
    elif any(word in order for word in ['calculate', 'plus', 'minus', 'multiplied', 'divided', '+', '-', 'x ', '/']):
        import re # Import locally to ensure it's available
        
        # Clean the command of conversational filler
        query = order.replace("calculate", "").replace("what is", "").replace("how much is", "").strip()
        
        # If user just said "calculate", ask for numbers
        if not query:
            query = get_missing_input(speak_func, take_command_func, "What would you like me to calculate?")
            if not query: return True

        # 1. Map Spoken Words to Math Symbols
        replacements = [
            ('multiplied by', '*'),
            ('divided by', '/'),
            ('to the power of', '**'),
            ('open bracket', '('),
            ('close bracket', ')'),
            ('open parenthesis', '('),
            ('close parenthesis', ')'),
            ('into', '*'),   # Common in Indian English
            ('times', '*'),
            ('plus', '+'),
            ('minus', '-'),
            ('mod', '%'),
            (' x ', '*'),    # Handle 'x' as multiplication (with spaces to avoid words)
            (' by ', '/')    # Handle 'by' as division
        ]
        
        for phrase, symbol in replacements:
            query = query.replace(phrase, symbol)

        # 2. Sanitize: Remove EVERYTHING that isn't a number or a math operator
        expression = re.sub(r'[^\d\+\-\*\/\.\%\(\)]', '', query)

        if expression:
            try:
                # 3. Calculate
                # eval is safe here because regex ensured only math characters exist
                result = eval(expression)
                
                # Format: Remove .0 if it's a whole number (e.g., 5.0 -> 5)
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                
                speak_func(f"The answer is {result}")
                
            except ZeroDivisionError:
                speak_func("I cannot divide by zero.")
            except SyntaxError:
                speak_func("The math formatting seems incorrect. Please check your brackets.")
            except Exception:
                speak_func("Sorry, I couldn't process that calculation.")
        else:
            speak_func("I didn't catch any numbers to calculate.")
        
        return True

    # --- Exit ---
    elif 'exit' in order:
        speak_func(f"Bye {addr}! Hope you liked my help")
        return False 
    
    return True