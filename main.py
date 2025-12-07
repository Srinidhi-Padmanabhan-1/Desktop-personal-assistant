import pyttsx3
import speech_recognition as sr
import datetime
import tkinter as tk
import threading
from tkinter.scrolledtext import ScrolledText
assistant_running = True
no_input = False
lang = 'en-US'

ADDR = None
Wish = None
hour = int(datetime.datetime.now().hour)
if 0 <= hour < 12:
    Wish = "Morning"
elif 12 <= hour < 18:
    Wish = "Afternoon"
else:
    Wish = "Evening"


# Initialize pyttsx3 engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

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

# Restart Button
def restart_assistant():
    global assistant_running
    assistant_running = True  # Restart the assistant
    assistant_thread = threading.Thread(target=main, daemon=True)
    assistant_thread.start()

restart_button = tk.Button(
    title_frame, text="↻", bg="#1cb0ff", fg="#ECF0F1", font=("Helvetica", 14, "bold"), command=restart_assistant, width=3,
)
restart_button.place(x=10, y=5)

# Output Frame
output_frame = tk.Frame(root, bg="#1cb0ff", bd=2, relief=tk.RIDGE)
output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

output_text = ScrolledText(output_frame, wrap=tk.WORD, font=("Helvetica", 12), bg="#160840", fg="#ECF0F1", bd=0)
output_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)


def update_gui_output(text, who_responding="Emma"):
    output_text.insert(tk.END, text + "\n", ('user' if who_responding != "Emma" else 'emma'))
    output_text.tag_config('emma', foreground='#b3ff00')
    output_text.tag_config('user', foreground='#00ff9d')
    output_text.see(tk.END)  # Scroll to the bottom


def speak(audio):


    engine.say(audio)
    update_gui_output("Emma: " + audio, "Emma")
    engine.runAndWait()

    

def takeCommand():
    global lang
    r = sr.Recognizer()
    with sr.Microphone() as source:
        update_gui_output("Listening...","User")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            update_gui_output("Processing...","User")
            query = r.recognize_google(audio, language=lang)
            update_gui_output(f"User said: {query}","User")
            return query
        
        except Exception as e:
            global no_input
    
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
    if uname == None:
        username()

    else:
        file = open("name.txt", "w")
        file.write(uname)

    greet(addr,uname)


def wishMe():
    global Wish
    global ADDR
    speak(f"Good {Wish}")    
    speak("I am your virtual assistant Emma.")
    speak("How should I address you? sir, or mam")

    # Create a small window for address selection
    addr_window = tk.Tk()
    addr_window.title("Address Selection")

    # Set window size
    window_width = 300
    window_height = 150

    # Get screen dimensions and calculate center position
    screen_width = addr_window.winfo_screenwidth()
    screen_height = addr_window.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    addr_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    addr_window.attributes("-topmost", True)


    def on_button_click(choice):
        global ADDR
        ADDR = choice
        # Save the selected address to a file
        with open("address.txt", "w") as file:
            file.write(choice)
        addr_window.destroy()
        username(ADDR)

    # Create two buttons for "sir" and "mam"
    btn_sir = tk.Button(addr_window, text="sir", font=("Arial", 14),
                        command=lambda: on_button_click("sir"))
    btn_mam = tk.Button(addr_window, text="mam", font=("Arial", 14),
                        command=lambda: on_button_click("mam"))

    # Pack buttons so they appear side by side
    btn_sir.pack(side="left", expand=True, fill="both", padx=20, pady=20)
    btn_mam.pack(side="right", expand=True, fill="both", padx=20, pady=20)

    addr_window.mainloop()


def process_order(order):
    global assistant_running
    global no_input
    
    if 'hello' in order:
        speak(f"Hello! How may I help you")
 
    elif 'how are you' in order or 'how r u' in order:
        speak("I am fine, thank you.")
        speak(f"How are you {ADDR}?")

    elif 'fine' in order or 'good' in order:
        speak(f"It's good to know that you are fine.")

    elif 'who are you' in order or 'who r u' in order:
        speak(f"I am your personal assistant Emma.")
        speak(f"I am here to help you with your tasks")
    elif 'exit' in order:
        speak(f"Thank you so much for using me {ADDR}! have a nice day")
        assistant_running = False

    elif no_input == False:
        speak("Invalid input")
        

def main():
    
    try:
        addr = ""
        with open("address.txt","r") as file:
            addr = file.read()

        name = ""
        with open("name.txt","r") as file:
            name = file.read()
    except FileNotFoundError:
        wishMe()

    else:
        greet(addr,name)

    while assistant_running:
        order = takeCommand().lower()
        if order == "None":
            continue
        process_order(order)


# Run the assistant in a separate thread to keep the GUI responsive
assistant_thread = threading.Thread(target=main, daemon=True)
assistant_thread.start()

root.mainloop()