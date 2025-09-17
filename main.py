import customtkinter as ctk
from datetime import datetime, date, timedelta
from tkinter import messagebox
import requests
from tkcalendar import DateEntry
import json
import os.path
import base64
import re
import threading
from dateutil.relativedelta import relativedelta

# --- Google API Imports ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
DATA_FILE = "subscriptions.json"
CURRENCY_API_KEY = "fca_live_8IGVH3HZJ1PfyXN3IHzOTGhciNSVkK06rfDMShDr"
CURRENCY_API_URL = f"https://api.freecurrencyapi.com/v1/latest?apikey={CURRENCY_API_KEY}"

# --- Gmail API Configuration ---
# This scope allows the app to read emails but not modify or delete them.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'


# --- Theming (Unchanged) ---
DARK_MODE_COLORS = {
    'background': '#2B2B2B', 'foreground': 'white', 'bordercolor': '#565656',
    'headersbackground': '#1F6AA5', 'headersforeground': 'white',
    'selectbackground': '#3A7EBF', 'selectforeground': 'white',
    'weekendbackground': '#212121', 'weekendforeground': 'white',
    'othermonthbackground': '#212121', 'othermonthforeground': '#888888',
}
LIGHT_MODE_COLORS = {
    'background': '#DBDBDB', 'foreground': 'black', 'bordercolor': '#979797',
    'headersbackground': '#3A7EBF', 'headersforeground': 'white',
    'selectbackground': '#3A7EBF', 'selectforeground': 'white',
    'weekendbackground': 'white', 'weekendforeground': 'black',
    'othermonthbackground': '#F5F5F5', 'othermonthforeground': '#979797',
}


class SubscriptionManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Digital Declutterer")
        self.geometry("900x750")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.subscriptions = []
        self.selected_sub = None
        self.editing_index = -1
        self.exchange_rates = {}

        self.load_subscriptions()
        self.fetch_exchange_rates()

        self.create_widgets()
        self.update_total_spending()
        self.sort_subscriptions()

    def create_subscription_widgets(self, parent_frame):
        input_frame = ctk.CTkFrame(parent_frame)
        input_frame.pack(fill="x", pady=10, padx=10)
        input_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(input_frame, text="Subscription Name:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.name_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., Netflix")
        self.name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text="Monthly Amount:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.amount_entry = ctk.CTkEntry(input_frame, placeholder_text="e.g., 15.99")
        self.amount_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text="Currency:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.currency_entry = ctk.CTkComboBox(input_frame, values=["USD", "EUR", "INR", "GBP", "JPY", "AUD", "CAD"])
        self.currency_entry.set("USD")
        self.currency_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text="Next Renewal:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.date_entry = DateEntry(input_frame, date_pattern='yyyy-mm-dd', locale='en_US')
        self.date_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.gmail_button = ctk.CTkButton(button_frame, text="Scan Gmail", command=self.start_gmail_scan_thread, fg_color="#D35400")
        self.gmail_button.grid(row=0, column=0, padx=5, sticky="ew")

        self.add_button = ctk.CTkButton(button_frame, text="Add/Update", command=self.add_or_update_subscription)
        self.add_button.grid(row=0, column=1, padx=5, sticky="ew")

        remove_button = ctk.CTkButton(button_frame, text="Remove Selected", command=self.remove_subscription, fg_color="#E74C3C")
        remove_button.grid(row=0, column=2, padx=5, sticky="ew")
        
        # --- NEW SWITCH ACCOUNT BUTTON ---
        self.switch_account_button = ctk.CTkButton(button_frame, text="Switch Account", command=self.switch_google_account, fg_color="#566573")
        self.switch_account_button.grid(row=0, column=3, padx=5, sticky="ew")
        # --- END NEW BUTTON ---

        self.status_label = ctk.CTkLabel(input_frame, text="", font=("Arial", 12))
        self.status_label.grid(row=5, column=0, columnspan=2, pady=5)
        
        display_frame = ctk.CTkFrame(parent_frame)
        display_frame.pack(fill="both", expand=True, padx=10, pady=10)
        display_frame.columnconfigure(0, weight=1)

        list_header_frame = ctk.CTkFrame(display_frame, fg_color="transparent")
        list_header_frame.pack(fill="x", pady=5)
        list_header_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(list_header_frame, text="Your Subscriptions", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky="w")

        sorting_options = ["By Renewal Date", "By Name (A-Z)", "By Amount (Low to High)"]
        self.sort_option_menu = ctk.CTkOptionMenu(list_header_frame, values=sorting_options, command=self.sort_subscriptions)
        self.sort_option_menu.set("By Renewal Date")
        self.sort_option_menu.grid(row=0, column=1, padx=5, sticky="e")

        self.base_currency_menu = ctk.CTkComboBox(list_header_frame, values=["USD", "EUR", "INR", "GBP", "JPY", "AUD", "CAD"], command=self.update_total_spending)
        self.base_currency_menu.set("USD")
        self.base_currency_menu.grid(row=0, column=2, padx=5, sticky="e")

        self.subscription_list_frame = ctk.CTkScrollableFrame(display_frame)
        self.subscription_list_frame.pack(fill="both", expand=True)

        total_spending_frame = ctk.CTkFrame(display_frame)
        total_spending_frame.pack(fill="x", pady=10)
        self.total_spending_label = ctk.CTkLabel(total_spending_frame, text="Total Monthly Spending: $0.00", font=("Arial", 14, "bold"))
        self.total_spending_label.pack(anchor="e", padx=10, pady=5)

    def authenticate_gmail(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    self.status_label.configure(text="Error: credentials.json not found.", text_color="red")
                    messagebox.showerror("Authentication Error", f"Cannot find credentials file: {CREDENTIALS_FILE}\nPlease follow the setup instructions.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        try:
            service = build('gmail', 'v1', credentials=creds)
            return service
        except HttpError as error:
            self.status_label.configure(text=f"API Error: {error}", text_color="red")
            return None

    def start_gmail_scan_thread(self):
        self.gmail_button.configure(state="disabled", text="Scanning...")
        self.status_label.configure(text="Authenticating and scanning Gmail...", text_color="gray")
        thread = threading.Thread(target=self.scan_gmail_for_subscriptions)
        thread.daemon = True
        thread.start()

    def scan_gmail_for_subscriptions(self):
        service = self.authenticate_gmail()
        if not service:
            self.gmail_button.configure(state="normal", text="Scan Gmail")
            return

        twelve_months_ago = (date.today() - relativedelta(months=12)).strftime('%Y/%m/%d')
        query = f'("subscription" OR "invoice" OR "receipt" OR "billed") after:{twelve_months_ago}'

        try:
            results = service.users().messages().list(userId='me', q=query, maxResults=50).execute()
            messages = results.get('messages', [])
            found_subs = []

            for i, message in enumerate(messages):
                self.status_label.configure(text=f"Processing email {i+1}/{len(messages)}...")
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                subscription = self.parse_email(msg)
                if subscription:
                    if not any(d['name'].lower() == subscription['name'].lower() for d in found_subs):
                         found_subs.append(subscription)

            self.after(0, self.show_found_subscriptions_dialog, found_subs)

        except HttpError as error:
            self.status_label.configure(text=f"An error occurred: {error}", text_color="red")
        finally:
            self.gmail_button.configure(state="normal", text="Scan Gmail")

    def parse_email(self, msg):
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        email_date_ms = int(msg['internalDate'])
        email_date = datetime.fromtimestamp(email_date_ms / 1000).date()
        service_name = re.match(r'"?([^<"]+)"?', from_header)
        if not service_name: return None
        service_name = service_name.group(1).strip()
        
        body = ""
        if 'parts' in msg['payload']:
            part = msg['payload']['parts'][0]
            if 'data' in part['body']:
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif 'data' in msg['payload']['body']:
            data = msg['payload']['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            return None
            
        price_regex = r'(?:(USD|EUR|INR|GBP|CAD|AUD|JPY|[\$€₹£]))\s*(\d+(?:[.,]\d{2})?)'
        match = re.search(price_regex, body + subject, re.IGNORECASE)
        
        if match:
            currency_symbol_map = {'$': 'USD', '€': 'EUR', '₹': 'INR', '£': 'GBP'}
            currency = match.group(1).upper()
            currency = currency_symbol_map.get(currency, currency)
            amount_str = match.group(2).replace(',', '.')
            amount = float(amount_str)
            renewal_date = email_date + relativedelta(months=1)
            return {"name": service_name, "amount": amount, "currency": currency, "renewal_date": renewal_date}
            
        return None

    def show_found_subscriptions_dialog(self, found_subs):
        if not found_subs:
            self.status_label.configure(text="Scan complete. No new subscriptions found.", text_color="gray")
            return

        self.status_label.configure(text=f"Scan complete. Found {len(found_subs)} potential subscriptions.", text_color="green")
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Found Subscriptions")
        dialog.geometry("500x400")
        dialog.transient(self)
        
        label = ctk.CTkLabel(dialog, text="Select subscriptions to import:")
        label.pack(pady=10)
        
        scrollable_frame = ctk.CTkScrollableFrame(dialog)
        scrollable_frame.pack(fill="both", expand=True, padx=10)
        
        checkboxes = []
        for sub in found_subs:
            existing = any(s['name'].lower() == sub['name'].lower() for s in self.subscriptions)
            text = f"{sub['name']} - {sub['currency']}{sub['amount']:.2f}"
            if existing:
                text += " (Already exists)"
            
            var = ctk.StringVar(value="on")
            cb = ctk.CTkCheckBox(scrollable_frame, text=text, variable=var, onvalue="on", offvalue="off")
            cb.pack(fill="x", padx=10, pady=5)
            if existing:
                cb.configure(state="disabled")
                var.set("off")
            checkboxes.append((var, sub))
            
        def import_selected():
            for var, sub in checkboxes:
                if var.get() == "on":
                    if not any(s['name'].lower() == sub['name'].lower() for s in self.subscriptions):
                        self.subscriptions.append({**sub, "widget": None})
            self.save_and_update()
            dialog.destroy()

        import_button = ctk.CTkButton(dialog, text="Import Selected", command=import_selected)
        import_button.pack(pady=10)

    # --- NEW METHOD TO SWITCH ACCOUNT ---
    def switch_google_account(self):
        """Logs out the current Google user by deleting the token file."""
        if messagebox.askyesno("Confirm Switch Account", 
                               "This will log you out from the current Google Account. "
                               "You will be prompted to log in again on the next scan. Continue?"):
            
            if os.path.exists(TOKEN_FILE):
                try:
                    os.remove(TOKEN_FILE)
                    self.status_label.configure(text="Successfully logged out. Click 'Scan Gmail' to connect a new account.", text_color="green")
                except OSError as e:
                    self.status_label.configure(text=f"Error removing token file: {e}", text_color="red")
            else:
                self.status_label.configure(text="No account is currently connected.", text_color="gray")
    # --- END NEW METHOD ---
        
    def add_or_update_subscription(self):
        if self.selected_sub:
            self.edit_selected_subscription()
        else:
            self.add_subscription()

    def create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 0), padx=20)
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(header_frame, text="Digital Declutterer", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        self.appearance_mode_switch = ctk.CTkSwitch(header_frame, text="Dark Mode", command=self.toggle_mode)
        self.appearance_mode_switch.grid(row=0, column=1, sticky="e")

        if ctk.get_appearance_mode() == "Dark":
            self.appearance_mode_switch.select()

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.create_subscription_widgets(self.main_frame)
        self.update_calendar_colors()

    def update_calendar_colors(self):
        current_mode = ctk.get_appearance_mode()
        colors = DARK_MODE_COLORS if current_mode == "Dark" else LIGHT_MODE_COLORS
        self.date_entry.config(**colors)

    def toggle_mode(self):
        new_mode = "Dark" if self.appearance_mode_switch.get() == 1 else "Light"
        ctk.set_appearance_mode(new_mode)
        self.appearance_mode_switch.configure(text=f"{new_mode} Mode")
        self.update_calendar_colors()

    def fetch_exchange_rates(self):
        # This now correctly checks if the key is the placeholder or empty
        if CURRENCY_API_KEY == "fca_" or not CURRENCY_API_KEY:
            messagebox.showwarning("API Key Missing","Please enter an API key from freecurrencyapi.com to enable live currency conversion.")
            self.exchange_rates = {"USD": 1.0, "EUR": 0.93, "INR": 83.5, "GBP": 0.79, "JPY": 157.0, "AUD": 1.5, "CAD": 1.37}
            return
        try:
            response = requests.get(CURRENCY_API_URL)
            response.raise_for_status()
            self.exchange_rates = response.json().get("data", {})
            if "USD" not in self.exchange_rates:
                self.exchange_rates["USD"] = 1.0

        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", f"Failed to fetch currency rates: {e}\nUsing fallback rates.")
            self.exchange_rates = {"USD": 1.0, "EUR": 0.93, "INR": 83.5, "GBP": 0.79, "JPY": 157.0, "AUD": 1.5, "CAD": 1.37}


    def convert_currency(self, amount, from_currency, to_currency):
        if not self.exchange_rates or from_currency == to_currency: return amount
        try:
            return (amount / self.exchange_rates[from_currency]) * self.exchange_rates[to_currency]
        except KeyError: return amount

    def load_subscriptions(self):
        try:
            with open(DATA_FILE, "r") as f:
                for sub in json.load(f):
                    sub['renewal_date'] = date.fromisoformat(sub['renewal_date'])
                    sub['widget'] = None
                    self.subscriptions.append(sub)
        except (FileNotFoundError, json.JSONDecodeError): pass

    def save_subscriptions(self):
        with open(DATA_FILE, "w") as f:
            json.dump([s for s in self.subscriptions if 'widget' in s and s.pop('widget', None) or True], f, default=lambda o: o.isoformat() if isinstance(o, date) else None, indent=4)

    def sort_subscriptions(self, choice=None):
        choice = choice or self.sort_option_menu.get()
        key_map = {
            "By Name (A-Z)": lambda x: x['name'].lower(),
            "By Amount (Low to High)": lambda x: self.convert_currency(x['amount'], x['currency'], self.base_currency_menu.get()),
            "By Renewal Date": lambda x: x['renewal_date']
        }
        self.subscriptions.sort(key=key_map.get(choice, lambda x: x['renewal_date']))
        self.update_subscription_display()

    def update_subscription_display(self):
        for child in self.subscription_list_frame.winfo_children(): child.destroy()
        today, alert_date = date.today(), date.today() + timedelta(days=7)
        for sub in self.subscriptions:
            fg_color = "#993939" if today <= sub['renewal_date'] <= alert_date else "transparent"
            if sub == self.selected_sub: fg_color = "#3A7EBF"
            label = ctk.CTkLabel(self.subscription_list_frame, text=f"{sub['name']} - {sub['currency']}{sub['amount']:.2f} (Renews: {sub['renewal_date']})",
                                 font=("Arial", 12), padx=10, pady=5, anchor="w", fg_color=fg_color, corner_radius=5)
            label.pack(fill="x", pady=2)
            sub['widget'] = label
            label.bind("<Button-1>", lambda e, s=sub: self.select_subscription(s))

    def update_total_spending(self, base_currency=None):
        base_currency = base_currency or self.base_currency_menu.get()
        total = sum(self.convert_currency(s['amount'], s['currency'], base_currency) for s in self.subscriptions)
        self.total_spending_label.configure(text=f"Total Monthly Spending: {total:.2f} {base_currency}")
        if self.sort_option_menu.get() == "By Amount (Low to High)": self.sort_subscriptions()

    def select_subscription(self, selected_sub):
        self.selected_sub = selected_sub
        self.editing_index = self.subscriptions.index(selected_sub)
        self.populate_fields_for_edit(selected_sub)
        self.add_button.configure(text="Update Selected")
        self.update_subscription_display()

    def populate_fields_for_edit(self, sub):
        for entry, value in [(self.name_entry, sub['name']), (self.amount_entry, str(sub['amount']))]:
            entry.delete(0, ctk.END); entry.insert(0, value)
        self.currency_entry.set(sub['currency'])
        self.date_entry.set_date(sub['renewal_date'])
    
    def _get_and_validate_input(self):
        name, amount_str = self.name_entry.get().strip(), self.amount_entry.get().strip()
        if not all([name, amount_str]):
            messagebox.showerror("Input Error", "Name and Amount are required.")
            return None
        try:
            amount = float(amount_str)
            if amount < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Invalid amount.")
            return None
        return name, amount, self.currency_entry.get(), self.date_entry.get_date()

    def add_subscription(self):
        data = self._get_and_validate_input()
        if data is None: return
        name, amount, currency, renewal_date = data
        self.subscriptions.append({"name": name, "amount": amount, "currency": currency, "renewal_date": renewal_date})
        self.clear_fields()
        self.save_and_update()

    def edit_selected_subscription(self):
        data = self._get_and_validate_input()
        if data is None: return
        self.subscriptions[self.editing_index].update(dict(zip(["name", "amount", "currency", "renewal_date"], data)))
        self.clear_fields()
        self.save_and_update()

    def remove_subscription(self):
        if self.selected_sub is None:
            messagebox.showerror("Selection Error", "Please select a subscription to remove.")
            return
        if messagebox.askyesno("Confirm Removal", f"Remove '{self.selected_sub['name']}'?"):
            self.subscriptions.remove(self.selected_sub)
            self.clear_fields()
            self.save_and_update()

    def clear_fields(self):
        self.name_entry.delete(0, ctk.END)
        self.amount_entry.delete(0, ctk.END)
        self.currency_entry.set("USD")
        self.date_entry.set_date(date.today())
        self.name_entry.focus()
        self.selected_sub = None
        self.editing_index = -1
        self.add_button.configure(text="Add Subscription")
        self.update_subscription_display()

    def save_and_update(self):
        self.save_subscriptions()
        self.sort_subscriptions()
        self.update_total_spending()



if __name__ == "__main__":
    app = SubscriptionManager()
    app.mainloop()