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

# GUI Setup
root = tk.Tk()
root.title("Virtual Assistant - Emma")
root.state("zoomed")
root.configure(bg="#160840")

# Title Frame
title_frame = tk.Frame(root, bg="#8425f7", height=60)
title_frame.pack(fill=tk.X)

title_label = tk.Label(
    title_frame, text="Emma - Your AI Assistant", bg="#8425f7", fg="#ECF0F1", font=("Helvetica", 18, "bold")
)
title_label.pack(pady=10)

# Output Frame
output_frame = tk.Frame(root, bg="#1cb0ff", bd=2, relief=tk.RIDGE)
output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

output_text = ScrolledText(output_frame, wrap=tk.WORD, font=("Helvetica", 12), bg="#160840", fg="#ECF0F1", bd=0)
output_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Configure tags
output_text.tag_config('emma', foreground='#b3ff00')
output_text.tag_config('user', foreground='#00ff9d')
output_text.tag_config('system', foreground='#ff6b6b')
# New tag for temporary status text (Italic and slightly dimmer color)
output_text.tag_config('temp_status', foreground='#aaaaaa', font=("Helvetica", 12, "italic"))


def update_gui_output(text, who_responding="Emma"):
    """
    Inserts PERMANENT text into the chat window.
    """
    output_text.insert(tk.END, text + "\n", ('user' if who_responding != "Emma" else 'emma'))
    output_text.see(tk.END)


def set_status(text):
    """
    Sets a TEMPORARY status message that can be deleted later.
    """
    # First, clear any existing status
    clear_status()
    # Insert new status with the 'temp_status' tag
    output_text.insert(tk.END, text, 'temp_status')
    output_text.see(tk.END)


def clear_status():
    """
    Removes any text marked as 'temp_status'.
    """
    try:
        # tag_ranges returns start, end, start, end... of the tag
        ranges = output_text.tag_ranges('temp_status')
        for i in range(0, len(ranges), 2):
            output_text.delete(ranges[i], ranges[i+1])
    except Exception:
        pass


# --- RESTART FUNCTION ---
def restart_assistant():
    global assistant_running
    
    # Clear the chat window
    output_text.delete('1.0', tk.END)
    # Temporary status
    set_status("System: Restarting...")

    assistant_running = True
    assistant_thread = threading.Thread(target=main, daemon=True)
    assistant_thread.start()

restart_button = tk.Button(
    title_frame, text="↻", bg="#1cb0ff", fg="#ECF0F1", font=("Helvetica", 14, "bold"), command=restart_assistant, width=3,
)
restart_button.place(x=10, y=5)

# --- MUTE/UNMUTE LOGIC ---
def toggle_mute():
    global is_muted
    is_muted = not is_muted
    
    if is_muted:
        mute_button.config(text="🔇", bg="red")
        input_entry.config(state=tk.NORMAL)
        send_btn.config(state=tk.NORMAL)
        # Force a status update immediately for better UX
        set_status("System: Muted. Waiting for text...")
    else:
        mute_button.config(text="🔊", bg="#1cb0ff")
        input_entry.config(state=tk.DISABLED)
        send_btn.config(state=tk.DISABLED)
        # Release the event to unblock text input loop if needed
        input_event.set()
        set_status("System: Unmuted. Switching to voice...")

mute_button = tk.Button(
    title_frame, text="🔊", bg="#1cb0ff", fg="#ECF0F1", font=("Helvetica", 14, "bold"), command=toggle_mute, width=3,
)
mute_button.place(x=60, y=5)

# --- SAVE CHAT LOGIC ---
def save_chat_history():
    folder_name = "saved_chats"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    i = 1
    while True:
        filename = os.path.join(folder_name, f"chat_{i}.txt")
        if not os.path.exists(filename):
            break
        i += 1
    
    # Get all text. This captures visible text.
    clear_status()
    chat_content = output_text.get("1.0", "end-1c")
    
    if chat_content.strip() == "":
        set_status("System: Chat is empty, nothing to save.")
        return

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(chat_content)
        update_gui_output(f"System: Chat saved to {filename}", "System")
    except Exception as e:
        update_gui_output(f"System: Error saving chat - {str(e)}", "System")

save_button = tk.Button(
    title_frame, text="💾", bg="#1cb0ff", fg="#ECF0F1", font=("Helvetica", 14, "bold"), command=save_chat_history, width=3,
)
save_button.place(x=110, y=5)


# --- INPUT FRAME (For Text Mode) ---
input_frame = tk.Frame(root, bg="#160840", height=50)
input_frame.pack(fill=tk.X, padx=10, pady=5)

def submit_text(event=None):
    global user_text_input
    text = input_entry.get()
    if text.strip() != "":
        user_text_input = text
        input_entry.delete(0, tk.END)
        input_event.set() 

input_entry = tk.Entry(input_frame, font=("Helvetica", 14), bg="#2c3e50", fg="white", state=tk.DISABLED)
input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
input_entry.bind("<Return>", submit_text)

send_btn = tk.Button(input_frame, text="Send", font=("Helvetica", 12, "bold"), bg="#1cb0ff", fg="white", 
                     command=submit_text, state=tk.DISABLED)
send_btn.pack(side=tk.RIGHT)


def speak(audio):
    update_gui_output("Emma: " + audio, "Emma")
    
    if not is_muted:
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        
        try:
            engine.setProperty('voice', voices[2].id)
        except IndexError:
            try:
                engine.setProperty('voice', voices[1].id)
            except IndexError:
                engine.setProperty('voice', voices[0].id)

        engine.say(audio)
        engine.runAndWait()


# --- UPDATED takeCommand TO ACCEPT OPTIONAL LANGUAGE ---
def takeCommand(language_code=None):
    """
    Accepts an optional language_code (e.g., 'hi-IN'). 
    If provided, listens in that language. 
    If None, listens in standard English (en-US).
    """
    global lang
    global no_input
    global user_text_input

    # Determine active language
    active_lang = language_code if language_code else lang

    # --- MODE 1: TEXT INPUT (MUTED) ---
    if is_muted:
        set_status("System: Muted. Waiting for text...")
        
        while is_muted: 
            is_set = input_event.wait(timeout=0.5)
            if is_set:
                input_event.clear()
                if user_text_input:
                    # 1. Show user input permanently
                    update_gui_output(f"User typed: {user_text_input}", "User")
                    
                    # 2. Show Processing with Delay
                    set_status("Processing...")
                    # Random delay between 0.75 and 1.25 seconds
                    time.sleep(random.uniform(0.75, 1.25))
                    
                    # 3. Clear status and return
                    clear_status()
                    return user_text_input
        return "None"

    # --- MODE 2: VOICE INPUT (UNMUTED) ---
    else:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            # 1. Show Listening
            set_status(f"Listening...")
            r.pause_threshold = 1
            try:
                if is_muted: 
                    clear_status()
                    return "None"
                
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                
                clear_status() 
                if is_muted: return "None"
                
                set_status("Processing...")
                
                # Use the dynamic language here
                query = r.recognize_google(audio, language=active_lang)
                
                clear_status()
                update_gui_output(f"User said: {query}", "User")
                
                no_input = False 
                return query
            
            except Exception as e:
                # Ensure status is cleared if recognition fails
                clear_status()
                no_input = True
                return "None"


def greet(addr, uname):
    global ADDR
    if addr=="sir":
        speak("Welcome Mister " + uname)
    elif addr=="mam":
        speak("Welcome Miss " + uname)

    speak(f"How can I help you, {addr}?")
    ADDR = addr

def username(addr):
    update_gui_output(f"User clicked: {addr}","User")
    speak(f"What should I call you, {addr}?")
    uname = takeCommand()
    
    if uname == "None" or uname is None:
        username(addr)
    else:
        file = open("name.txt", "w")
        file.write(uname)
        file.close()
        greet(addr,uname)


def wishMe():
    global Wish
    global ADDR
    speak(f"Good {Wish}")    
    speak("I am your virtual assistant Emma.")
    speak("How should I address you? sir, or mam")

    addr_window = tk.Tk()
    addr_window.title("Address Selection")

    window_width = 300
    window_height = 150

    screen_width = addr_window.winfo_screenwidth()
    screen_height = addr_window.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    addr_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    addr_window.attributes("-topmost", True)

    def on_button_click(choice):
        global ADDR
        ADDR = choice
        with open("address.txt", "w") as file:
            file.write(choice)
        addr_window.destroy()
        username(ADDR)

    btn_sir = tk.Button(addr_window, text="sir", font=("Arial", 14),
                        command=lambda: on_button_click("sir"))
    btn_mam = tk.Button(addr_window, text="mam", font=("Arial", 14),
                        command=lambda: on_button_click("mam"))

    btn_sir.pack(side="left", expand=True, fill="both", padx=20, pady=20)
    btn_mam.pack(side="right", expand=True, fill="both", padx=20, pady=20)

    addr_window.mainloop()


def main():
    global assistant_running
    
    try:
        addr = ""
        with open("address.txt","r") as file:
            addr = file.read()

        name = ""
        with open("name.txt","r") as file:
            name = file.read()
            
        if not addr or not name:
            wishMe()
        else:
            greet(addr,name)

    except FileNotFoundError:
        wishMe()

    while assistant_running:
        order = takeCommand()
        
        if order is None or order == "None":
            continue
            
        should_continue = processOrder.process_order(order.lower(), speak, takeCommand, ADDR)
        
        if should_continue is False:
            assistant_running = False


# Run the assistant in a separate thread
assistant_thread = threading.Thread(target=main, daemon=True)
assistant_thread.start()

root.mainloop()