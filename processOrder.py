def process_order(order, speak_func, take_command_func, addr):
    
    if 'hello' in order:
        speak_func(f"Hello! How may I help you {addr}?.")
        return True

    elif 'test input' in order:
        speak_func("Testing input loop. Type or say something:")
        response = take_command_func()
        speak_func(f"You responded with: {response}")
        return True
    
    elif 'how are you' in order or 'how r u' in order:
        speak_func("I am fine, thank you.")
        speak_func(f"How are you {addr}?")
        return True

    elif 'fine' in order or 'good' in order:
        speak_func(f"It's good to know that you are fine.")
        return True

    elif 'who are you' in order or 'who r u' in order:
        speak_func(f"I am your personal assistant Emma.")
        speak_func(f"I am here to help you with your tasks")
        return True

    elif 'exit' in order:
        speak_func(f"bye {addr}! Hope you liked my help")
        return False # This stops the assistant
    

    # If command is not found, just return True to keep listening
    return True