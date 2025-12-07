import tkinter as tk
import subprocess


def show_welcome_window():
    root = tk.Tk()
    root.title("Desktop personal assistant")
    root.geometry("1550x800")
    
    # Background color using RGB values
    red, green, blue = 1, 112, 128  
    color_hex = "#{:02x}{:02x}{:02x}".format(red, green, blue)
    root.configure(bg=color_hex)
    
    # Outer frame fills the entire window.
    outer_frame = tk.Frame(root, bg=color_hex)
    outer_frame.pack(expand=True, fill="both")
    
    # Inner frame is placed in the center of the outer frame.
    inner_frame = tk.Frame(outer_frame, bg=color_hex)
    inner_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Created a Text widget for the content.
    # Adjusted width/height as needed for centered layout.
    text_widget = tk.Text(inner_frame, font=("Arial", 18), fg="gold", bg=color_hex,
                          bd=0, highlightthickness=0, wrap="word", width=60, height=15)
    
    # Inserted content with bold headings.
    text_widget.insert(tk.END, "Welcome to Desktop personal assistant\n\n")
    
    # Feature 1 heading in bold
    text_widget.insert(tk.END, "personal Assistant Emma -\n", "heading")
    text_widget.insert(tk.END, "Performs various day to day operations with voice commands on your computer\n\n")
    
    
    text_widget.insert(tk.END, "Press 'Continue' to proceed.")
    
    # Configure the "heading" tag for bold text.
    text_widget.tag_configure("heading", font=("Arial", 18, "bold"))

    # Configure the "center" tag to center text horizontally.
    text_widget.tag_configure("center", justify="center")
    text_widget.tag_add("center", "1.0", "end")
    
    # Make the Text widget read-only.
    text_widget.config(state="disabled")
    text_widget.pack(pady=20)
    
    # Continue button, that starts the assistant
    continue_button = tk.Button(inner_frame, text="Continue", font=("Arial", 16), fg="gold", bg=color_hex , command=lambda : [start_main_app(),root.destroy()])
    continue_button.pack(pady=10)
    
    root.mainloop()

def start_main_app():
    subprocess.Popen(["python", "main.py"])


show_welcome_window()
