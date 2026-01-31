import pyttsx3
import speech_recognition as sr
import datetime
import tkinter as tk
import threading
from tkinter.scrolledtext import ScrolledText

# Import the external logic file
import processOrder 

assistant_running = True
no_input = False
lang = 'en-US'

# State control variables
is_muted = False
input_event = threading.Event() # Used to synchronize text input
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
    title_frame, text="Emma - Your personal Assistant", bg="#8425f7", fg="#ECF0F1", font=("Helvetica", 18, "bold")
)
title_label.pack(pady=10)

# --- RESTART FUNCTION ---
def restart_assistant():
    global assistant_running
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
        update_gui_output("System: Muted. Type your commands below.", "System")
    else:
        mute_button.config(text="🔊", bg="#1cb0ff")
        input_entry.config(state=tk.DISABLED)
        send_btn.config(state=tk.DISABLED)
        update_gui_output("System: Unmuted. Listening to microphone...", "System")
        # If we were waiting for text, release the wait so it can check loop again
        input_event.set() 

mute_button = tk.Button(
    title_frame, text="🔊", bg="#1cb0ff", fg="#ECF0F1", font=("Helvetica", 14, "bold"), command=toggle_mute, width=3,
)
mute_button.place(x=60, y=5)

# Output Frame
output_frame = tk.Frame(root, bg="#1cb0ff", bd=2, relief=tk.RIDGE)
output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

output_text = ScrolledText(output_frame, wrap=tk.WORD, font=("Helvetica", 12), bg="#160840", fg="#ECF0F1", bd=0)
output_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# --- INPUT FRAME (For Text Mode) ---
input_frame = tk.Frame(root, bg="#160840", height=50)
input_frame.pack(fill=tk.X, padx=10, pady=5)

def submit_text(event=None):
    global user_text_input
    text = input_entry.get()
    if text.strip() != "":
        user_text_input = text
        input_entry.delete(0, tk.END)
        input_event.set() # Signal the main thread that input is ready

input_entry = tk.Entry(input_frame, font=("Helvetica", 14), bg="#2c3e50", fg="white", state=tk.DISABLED)
input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
input_entry.bind("<Return>", submit_text)

send_btn = tk.Button(input_frame, text="Send", font=("Helvetica", 12, "bold"), bg="#1cb0ff", fg="white", 
                     command=submit_text, state=tk.DISABLED)
send_btn.pack(side=tk.RIGHT)


def update_gui_output(text, who_responding="Emma"):
    output_text.insert(tk.END, text + "\n", ('user' if who_responding != "Emma" else 'emma'))
    output_text.tag_config('emma', foreground='#b3ff00')
    output_text.tag_config('user', foreground='#00ff9d')
    output_text.tag_config('system', foreground='#ff6b6b')
    output_text.see(tk.END)


def speak(audio):
    update_gui_output("Emma: " + audio, "Emma")
    
    # Only speak voice if NOT muted
    if not is_muted:
        # Initialize engine LOCALLY to prevent Windows 10 Threading/COM errors
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        
        # Safe voice selection
        try:
            engine.setProperty('voice', voices[2].id)
        except IndexError:
            try:
                engine.setProperty('voice', voices[1].id)
            except IndexError:
                engine.setProperty('voice', voices[0].id)

        engine.say(audio)
        engine.runAndWait()


def takeCommand():
    global lang
    global no_input
    global user_text_input

    # --- MODE 1: TEXT INPUT (MUTED) ---
    if is_muted:
        update_gui_output("Waiting for text...", "System")
        
        while is_muted: 
            is_set = input_event.wait(timeout=0.5)
            if is_set:
                input_event.clear()
                if user_text_input:
                    update_gui_output(f"User typed: {user_text_input}", "User")
                    return user_text_input
        return "None"

    # --- MODE 2: VOICE INPUT (UNMUTED) ---
    else:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            update_gui_output("Listening...", "User")
            r.pause_threshold = 1
            try:
                if is_muted: return "None"
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                if is_muted: return "None"

                update_gui_output("Processing...", "User")
                query = r.recognize_google(audio, language=lang)
                update_gui_output(f"User said: {query}", "User")
                no_input = False 
                return query
            
            except Exception as e:
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
            
        # Passing 'speak' and 'ADDR' to the external logic
        # Expecting process_order to return False if the user wants to exit
        should_continue = processOrder.process_order(order.lower(), speak, ADDR)
        
        if should_continue is False:
            assistant_running = False


# Run the assistant in a separate thread
assistant_thread = threading.Thread(target=main, daemon=True)
assistant_thread.start()

root.mainloop()