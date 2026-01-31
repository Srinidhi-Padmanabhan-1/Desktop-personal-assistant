def process_order(order, speak, addr):
    """
    Processes the user's command.
    
    Args:
        order (str): The text command from the user.
        speak (function): The speak function from main.py.
        addr (str): The user's address (e.g., 'sir', 'mam').
        
    Returns:
        bool: True if the assistant should keep running, False if it should exit.
    """
    
    if 'hello' in order:
        speak(f"Hello! How may I help you")
        return True
 
    elif 'how are you' in order or 'how r u' in order:
        speak("I am fine, thank you.")
        speak(f"How are you {addr}?")
        return True

    elif 'fine' in order or 'good' in order:
        speak(f"It's good to know that you are fine.")
        return True

    elif 'who are you' in order or 'who r u' in order:
        speak(f"I am your personal assistant Emma.")
        speak(f"I am here to help you with your tasks")
        return True
        
    elif 'exit' in order:
        speak(f"Thank you so much for using me {addr}! have a nice day")
        return False # This signals main.py to stop the loop

    return True