# test_app.py
import customtkinter as ctk


class MinimalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Startup Test")
        self.geometry("300x200")

        print("--- Test App: Initializing... ---")

        # We define the method that the button will call
        # This method belongs to the App instance (self)

        try:
            self.button = ctk.CTkButton(self,
                                        text="Click Me",
                                        command=self.my_test_command)
            self.button.pack(padx=20, pady=20, expand=True)

            print("--- Test App: SUCCESS! The app launched without crashing. ---")

        except Exception as e:
            print(f"--- Test App: FAILED! The app crashed on startup. ---")
            print(f"Error was: {e}")

    def my_test_command(self):
        print("Button click was successful!")


if __name__ == "__main__":
    app = MinimalApp()
    app.mainloop()