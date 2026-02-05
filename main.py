import pyttsx3
import speech_recognition as sr
import datetime
import tkinter as tk
import threading
from tkinter.scrolledtext import ScrolledText
import os
import time
import random

# Import the external logic file
import processOrder 

# --- Light Mode Configuration ---
THEME_BG = "#F0F2F5"       # Light Grey (Window Background)
THEME_ACCENT = "#0084FF"   # Blue
THEME_TEXT = "#050505"     # Dark Text

# Chat Text Colors
USER_COLOR = "#0084FF"     # Blue (User)
EMMA_COLOR = "#D35400"     # Orange (Emma)
SYSTEM_COLOR = "#E74C3C"   # Red (System)
TEMP_STATUS_COLOR = "#555555" # Grey

# Component Colors
HEADER_BG = "#FFFFFF"      
CHAT_BG = "#FFFFFF"        
INPUT_BG = "#FFFFFF"       
BUTTON_BG = "#E4E6EB"      
BUTTON_FG = "#050505"      

FONT_MAIN = ("Segoe UI", 14)
FONT_BOLD = ("Segoe UI", 14, "bold")
FONT_STATUS = ("Segoe UI", 12, "italic")

assistant_running = True
no_input = False
lang = 'en-US'

# State control variables
is_muted = False
input_event = threading.Event() 
user_text_input = ""

ADDR = None
Wish = None
hour = int(datetime.datetime.now().hour)
if 0 <= hour < 12:
    Wish = "Morning"
elif 12 <= hour < 18:
    Wish = "Afternoon"
else:
    Wish = "Evening"

# --- GUI Setup ---
root = tk.Tk()
root.title("Emma AI")
root.state("zoomed")
root.configure(bg=THEME_BG)

# 1. Header Frame
header_frame = tk.Frame(root, bg=HEADER_BG, height=70)
header_frame.pack(fill=tk.X, side=tk.TOP)
header_frame.pack_propagate(False) 

# Title
title_label = tk.Label(
    header_frame, 
    text="🤖 Emma AI Assistant", 
    bg=HEADER_BG, 
    fg="#6C5CE7", 
    font=("Segoe UI", 22, "bold")
)
title_label.pack(side=tk.LEFT, padx=20)

# 2. Chat Area
chat_frame = tk.Frame(root, bg=THEME_BG)
chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

output_text = ScrolledText(
    chat_frame, 
    wrap=tk.WORD, 
    font=FONT_MAIN, 
    bg=CHAT_BG, 
    fg=THEME_TEXT, 
    bd=0, 
    padx=15, 
    pady=15
)
output_text.pack(expand=True, fill=tk.BOTH)

# Configure Tags for Alignment and Color
output_text.tag_config('emma', foreground=EMMA_COLOR, lmargin1=10, lmargin2=10, spacing1=5)
output_text.tag_config('user', foreground=USER_COLOR, justify='right', rmargin=10, spacing1=5)
output_text.tag_config('system', foreground=SYSTEM_COLOR, justify='center', font=("Segoe UI", 12, "italic"), spacing1=5)
output_text.tag_config('temp_status', foreground=TEMP_STATUS_COLOR, justify='center', font=FONT_STATUS)


# --- Helper Functions ---

def update_gui_output(text, who_responding="Emma"):
    """
    Inserts PERMANENT text into the chat window with Icons.
    """
    if who_responding == "Emma":
        formatted_text = f"🤖 {text}\n"
        output_text.insert(tk.END, formatted_text, 'emma')
    elif who_responding == "User":
        formatted_text = f"{text} 👤\n"
        output_text.insert(tk.END, formatted_text, 'user')
    else:
        output_text.insert(tk.END, f"--- {text} ---\n", 'system')
    output_text.see(tk.END)

def set_status(text):
    """ Sets a TEMPORARY grey message. """
    clear_status()
    output_text.insert(tk.END, f"\n( {text} )\n", 'temp_status')
    output_text.see(tk.END)

def clear_status():
    """ Removes the grey message. """
    try:
        ranges = output_text.tag_ranges('temp_status')
        for i in range(0, len(ranges), 2):
            output_text.delete(ranges[i], ranges[i+1])
    except Exception:
        pass


# --- Button Functions ---

def restart_assistant():
    global assistant_running
    output_text.delete('1.0', tk.END)
    set_status("System Restarting...")
    assistant_running = True
    assistant_thread = threading.Thread(target=main, daemon=True)
    assistant_thread.start()

def toggle_mute():
    global is_muted
    is_muted = not is_muted
    
    if is_muted:
        # --- Active Text Mode ---
        mute_button.config(text="🔇", bg="#FFCDD2", fg="#C62828") # Red Alert
        
        # Turn Textbox White and Border Blue
        input_entry.config(state=tk.NORMAL, bg="#FFFFFF", fg="#000000") 
        entry_border.config(bg=THEME_ACCENT) 
        
        # Enable Send Button (Blue)
        send_btn.config(state=tk.NORMAL, bg=THEME_ACCENT, fg="white") 
        
        set_status("Muted. Type command below.")
    else:
        # --- Active Voice Mode ---
        mute_button.config(text="🎙️", bg=BUTTON_BG, fg=BUTTON_FG) 
        
        # Grey out Textbox and Border
        input_entry.config(state=tk.DISABLED, bg="#F0F2F5", fg="#666666") 
        entry_border.config(bg="#CCCCCC") 
        
        # Disable Send Button
        send_btn.config(state=tk.DISABLED, bg=BUTTON_BG, fg="#999999") 
        
        input_event.set()
        set_status("Microphone Active")

def save_chat_history():
    folder_name = "saved_chats"
    if not os.path.exists(folder_name): os.makedirs(folder_name)
    i = 1
    while True:
        filename = os.path.join(folder_name, f"chat_{i}.txt")
        if not os.path.exists(filename): break
        i += 1
    clear_status()
    chat_content = output_text.get("1.0", "end-1c")
    if chat_content.strip() == "": return
    try:
        with open(filename, "w", encoding="utf-8") as f: f.write(chat_content)
        update_gui_output(f"Chat saved to {filename}", "System")
    except Exception as e: update_gui_output(f"Error: {str(e)}", "System")

# --- Control Buttons (Header) ---
btn_frame = tk.Frame(header_frame, bg=HEADER_BG)
btn_frame.pack(side=tk.RIGHT, padx=20)

save_button = tk.Button(btn_frame, text="💾", font=("Segoe UI Emoji", 16), bg=BUTTON_BG, fg=BUTTON_FG, bd=0, command=save_chat_history, width=4)
save_button.pack(side=tk.RIGHT, padx=5)

mute_button = tk.Button(btn_frame, text="🎙️", font=("Segoe UI Emoji", 16), bg=BUTTON_BG, fg=BUTTON_FG, bd=0, command=toggle_mute, width=4)
mute_button.pack(side=tk.RIGHT, padx=5)

restart_button = tk.Button(btn_frame, text="↻", font=("Segoe UI Emoji", 16), bg=BUTTON_BG, fg=BUTTON_FG, bd=0, command=restart_assistant, width=4)
restart_button.pack(side=tk.RIGHT, padx=5)

# --- Bottom Input ---
# --- Bottom Input Area ---
input_frame = tk.Frame(root, bg=THEME_BG, height=60)
input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

def submit_text(event=None):
    global user_text_input
    text = input_entry.get()
    if text.strip() != "":
        user_text_input = text
        input_entry.delete(0, tk.END)
        input_event.set() 

# 1. THE BORDER FRAME (Acts as the colored outline)
entry_border = tk.Frame(input_frame, bg="#CCCCCC", bd=0)
entry_border.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

# 2. THE TEXTBOX (Inside the border frame)
input_entry = tk.Entry(
    entry_border, 
    font=("Segoe UI", 14), 
    bg="#F0F2F5", # Starts Grey (Voice Mode)
    fg=THEME_TEXT,
    insertbackground="black", 
    relief=tk.FLAT
)
# The padx=1, pady=1 here creates the 1px border thickness by showing the frame behind it
input_entry.pack(fill=tk.BOTH, expand=True, ipady=8, padx=1, pady=1) 
input_entry.bind("<Return>", submit_text)

# 3. THE SEND BUTTON
send_btn = tk.Button(
    input_frame, 
    text="➤", 
    font=("Segoe UI", 16, "bold"), 
    bg=BUTTON_BG, 
    fg="#999999", # Starts Grey (Disabled)
    bd=0, 
    command=submit_text, 
    state=tk.DISABLED, 
    width=4,
    cursor="hand2"
)
send_btn.pack(side=tk.RIGHT, ipady=2)

# --- CORE LOGIC ---

def speak(audio, output_voice=True):
    """ Displays text in chat. If output_voice is True, plays robotic audio. """
    update_gui_output(audio, "Emma")
    if not is_muted and output_voice:
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        try: engine.setProperty('voice', voices[2].id)
        except IndexError:
            try: engine.setProperty('voice', voices[1].id)
            except IndexError: engine.setProperty('voice', voices[0].id)
        engine.say(audio)
        engine.runAndWait()

def takeCommand(language_code=None):
    """ Listens via mic or waits for text. Switches language for translation. """
    global lang, no_input, user_text_input
    active_lang = language_code if language_code else lang
    if is_muted:
        set_status("Waiting for text...")
        while is_muted: 
            is_set = input_event.wait(timeout=0.5)
            if is_set:
                input_event.clear()
                if user_text_input:
                    update_gui_output(user_text_input, "User")
                    set_status("Processing...")
                    time.sleep(random.uniform(0.5, 1.0))
                    clear_status()
                    return user_text_input
        return "None"
    else:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            set_status("Listening...")
            r.pause_threshold = 1
            try:
                if is_muted: return "None"
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                clear_status() 
                set_status("Processing...")
                query = r.recognize_google(audio, language=active_lang)
                clear_status()
                update_gui_output(query, "User")
                no_input = False 
                return query
            except Exception:
                clear_status()
                no_input = True
                return "None"

def greet(addr, uname):
    global ADDR
    if addr=="sir": speak("Welcome Mister " + uname)
    elif addr=="mam": speak("Welcome Miss " + uname)
    speak(f"How can I help you, {addr}?")
    ADDR = addr

def username(addr):
    speak(f"What should I call you, {addr}?")
    uname = takeCommand()
    if uname == "None" or uname is None:
        username(addr)
    else:
        with open("name.txt", "w") as file: file.write(uname)
        greet(addr,uname)

# --- PRESERVED ORIGINAL WISHME LOGIC (POPUP) ---
def wishMe():
    global Wish, ADDR
    speak(f"Good {Wish}")    
    speak("I am your virtual assistant Emma.")
    speak("How should I address you? sir, or mam")

    addr_window = tk.Tk() # Original Logic
    addr_window.title("Address Selection")
    addr_window.geometry(f"300x150")
    addr_window.attributes("-topmost", True)

    def on_button_click(choice):
        global ADDR
        ADDR = choice
        with open("address.txt", "w") as file: file.write(choice)
        addr_window.destroy()
        username(ADDR)

    btn_sir = tk.Button(addr_window, text="sir", font=("Arial", 14), command=lambda: on_button_click("sir"))
    btn_mam = tk.Button(addr_window, text="mam", font=("Arial", 14), command=lambda: on_button_click("mam"))
    btn_sir.pack(side="left", expand=True, fill="both", padx=20, pady=20)
    btn_mam.pack(side="right", expand=True, fill="both", padx=20, pady=20)
    addr_window.mainloop()

def main():
    global assistant_running
    try:
        addr, name = "", ""
        if os.path.exists("address.txt"):
            with open("address.txt","r") as f: addr = f.read()
        if os.path.exists("name.txt"):
            with open("name.txt","r") as f: name = f.read()
        if not addr or not name: wishMe()
        else: greet(addr,name)

        while assistant_running:
            order = takeCommand()
            if order is None or order == "None": continue
            should_continue = processOrder.process_order(order.lower(), speak, takeCommand, ADDR)
            if should_continue is False: assistant_running = False
    except Exception: pass

# Background Thread
assistant_thread = threading.Thread(target=main, daemon=True)
assistant_thread.start()
root.mainloop()