# print("Hello, Louisa")

# name = input("What's your name? ")
# age = input("How old are you? ")

# print(f"Nice to meet you, {name}! You are {age} years old.")

import tkinter as tk

def save_data():
    name = name_entry.get()
    age = age_entry.get()

    with open("gui_users.txt", "a") as file:
        file.write(f"{name}, {age} years old\n")

    status_label.config(text="Data saved successfully!", fg="green")
    name_entry.delete(0, tk.END)
    age_entry.delete(0, tk.END)


# Create main window
root = tk.Tk()
root.title("User Info Form")
root.geometry("300x200")

# Name input
tk.Label(root, text="Name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()

# Age input
tk.Label(root, text="Age:").pack()
age_entry = tk.Entry(root)
age_entry.pack()

# Submit button
submit_btn = tk.Button(root, text="Submit", command=save_data)
submit_btn.pack(pady=10)

# Status label
status_label = tk.Label(root, text="")
status_label.pack()

# Run the app
root.mainloop()
