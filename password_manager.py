import base64
import json
import os
import random
import string
import time
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configurazione tema moderno
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def derive_key(master_password: str, salt: bytes) -> bytes:
  kdf = PBKDF2HMAC(
      algorithm=hashes.SHA512(),
      length=32,
      salt=salt,
      iterations=600000,
  )
  return kdf.derive(master_password.encode())


class AegisUltimateApp(ctk.CTk):

  def __init__(self):
    super().__init__()

    self.title("AegisVault Ultimate - Secure Core")
    self.geometry("800x550")
    self.minsize(700, 500)

    self.key = None
    self.vault = {}
    self.current_user = None
    self.data_file = None
    self.key_file = None

    # Timer di inattività per l'auto-lock (5 minuti)
    self.last_activity_time = time.time()
    self.auto_lock_limit = 300

    self.show_profile_selector()
    self.check_inactivity()

  def reset_activity_timer(self, event=None):
    self.last_activity_time = time.time()

  def check_inactivity(self):
    if self.key and self.current_user:
      if time.time() - self.last_activity_time > self.auto_lock_limit:
        self.key = None
        self.vault = {}
        self.current_user = None
        messagebox.showwarning(
            "Auto-Lock",
            "Vault bloccato automaticamente per inattività prolungata.",
        )
        self.show_profile_selector()
    self.after(10000, self.check_inactivity)

  def clear_window(self):
    for widget in self.winfo_children():
      widget.destroy()

  def get_existing_profiles(self):
    profiles = []
    if os.path.exists("."):
      for f in os.listdir("."):
        if f.endswith(".aegis"):
          profiles.append(f[6:-6])
    return profiles

  def show_profile_selector(self):
    self.clear_window()

    container = ctk.CTkFrame(self, fg_color="transparent")
    container.pack(expand=True, fill="both", padx=40, pady=40)

    # Frame con dimensioni passate direttamente nel costruttore (corretto)
    card = ctk.CTkFrame(
        container,
        width=480,
        height=420,
        corner_radius=16,
        fg_color=("#2b2b36", "#1a1a24"),
    )
    card.place(relx=0.5, rely=0.5, anchor="center")

    title = ctk.CTkLabel(
        card,
        text="🛡️ AEGIS VAULT ULTIMATE",
        font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
    )
    title.pack(pady=(30, 5))

    subtitle = ctk.CTkLabel(
        card,
        text="Next-Gen Cybersecurity & AES-GCM Encryption",
        text_color="#888899",
        font=ctk.CTkFont(family="Segoe UI", size=11),
    )
    subtitle.pack(pady=(0, 25))

    lbl_user = ctk.CTkLabel(
        card,
        text="Seleziona o digita il Profilo:",
        font=ctk.CTkFont(size=12, weight="bold"),
        anchor="w",
    )
    lbl_user.pack(fill="x", padx=40, pady=(0, 5))

    profiles = self.get_existing_profiles()
    self.profile_combo = ctk.CTkComboBox(
        card, values=profiles, width=400, height=38
    )
    self.profile_combo.pack(padx=40, pady=(0, 15))
    if profiles:
      self.profile_combo.set(profiles[0])

    lbl_pass = ctk.CTkLabel(
        card,
        text="Master Password:",
        font=ctk.CTkFont(size=12, weight="bold"),
        anchor="w",
    )
    lbl_pass.pack(fill="x", padx=40, pady=(0, 5))

    self.pass_entry = ctk.CTkEntry(
        card, show="•", width=400, height=38, placeholder_text="••••••••••••"
    )
    self.pass_entry.pack(padx=40, pady=(0, 25))
    self.pass_entry.focus()
    self.pass_entry.bind("<Return>", lambda e: self.load_profile())

    btn_login = ctk.CTkButton(
        card,
        text="Sblocca / Crea Database",
        height=40,
        font=ctk.CTkFont(weight="bold"),
        command=self.load_profile,
    )
    btn_login.pack(padx=40, fill="x", pady=(0, 20))

  def load_profile(self):
    username = self.profile_combo.get().strip()
    master_pass = self.pass_entry.get()

    if not username or not master_pass:
      messagebox.showerror("Errore", "Compila tutti i campi per procedere.")
      return

    clean_user = "".join(
        c for c in username if c.isalnum() or c in ("_", "-")
    ).lower()
    self.current_user = clean_user
    self.data_file = f"vault_{clean_user}.aegis"
    self.key_file = f"key_{clean_user}.key"

    is_new = not os.path.exists(self.key_file) or not os.path.exists(
        self.data_file
    )
    self.authenticate(is_new, master_pass)

  def authenticate(self, is_new, master_pass):
    if is_new:
      salt = os.urandom(32)
      self.key = derive_key(master_pass, salt)
      with open(self.key_file, "wb") as f:
        f.write(salt)
      self.vault = {}
      self.save_vault_file()
      messagebox.showinfo(
          "Successo", f"Nuovo database '.aegis' creato per '{self.current_user}'."
      )
      self.show_main_screen()
    else:
      try:
        with open(self.key_file, "rb") as f:
          salt = f.read()
        self.key = derive_key(master_pass, salt)
        aesgcm = AESGCM(self.key)

        with open(self.data_file, "rb") as f:
          content = f.read()

        nonce = content[:12]
        encrypted_data = content[12:]
        decrypted = aesgcm.decrypt(nonce, encrypted_data, None)
        self.vault = json.loads(decrypted.decode())
        self.show_main_screen()
      except Exception:
        messagebox.showerror(
            "Accesso Negato", "Master Password errata o file compromesso."
        )

  def save_vault_file(self):
    aesgcm = AESGCM(self.key)
    nonce = os.urandom(12)
    encrypted = aesgcm.encrypt(nonce, json.dumps(self.vault).encode(), None)
    with open(self.data_file, "wb") as f:
      f.write(nonce + encrypted)

  def show_main_screen(self):
    self.clear_window()
    self.bind("<Motion>", self.reset_activity_timer)
    self.bind("<Key>", self.reset_activity_timer)

    top_bar = ctk.CTkFrame(self, height=70, fg_color=("#2b2b36", "#1a1a24"))
    top_bar.pack(fill="x", padx=20, pady=20)

    title = ctk.CTkLabel(
        top_bar,
        text=f"🔒 Database Attivo: {self.current_user}.aegis",
        font=ctk.CTkFont(size=15, weight="bold"),
    )
    title.pack(side="left", padx=20)

    btn_switch = ctk.CTkButton(
        top_bar,
        text="Cambia Profilo",
        fg_color="#333344",
        hover_color="#444455",
        command=self.show_profile_selector,
    )
    btn_switch.pack(side="right", padx=15)

    btn_add = ctk.CTkButton(
        top_bar,
        text="+ Nuova Credenziale",
        command=self.add_password_popup,
    )
    btn_add.pack(side="right")

    main_frame = ctk.CTkFrame(self, fg_color=("#2b2b36", "#1a1a24"))
    main_frame.pack(expand=True, fill="both", padx=20, pady=(0, 20))

    self.scrollable_frame = ctk.CTkScrollableFrame(
        main_frame, fg_color="transparent"
    )
    self.scrollable_frame.pack(expand=True, fill="both", padx=10, pady=10)

    self.refresh_vault_list()

  def refresh_vault_list(self):
    for widget in self.scrollable_frame.winfo_children():
      widget.destroy()

    if not self.vault:
      lbl_empty = ctk.CTkLabel(
          self.scrollable_frame,
          text="Nessuna credenziale salvata in questo database.",
          text_color="#888899",
      )
      lbl_empty.pack(pady=40)
      return

    for site, pwd in self.vault.items():
      row = ctk.CTkFrame(
          self.scrollable_frame, height=50, fg_color=("#363646", "#222230")
      )
      row.pack(fill="x", pady=5, padx=5)

      lbl_site = ctk.CTkLabel(
          row,
          text=site,
          font=ctk.CTkFont(size=13, weight="bold"),
          anchor="w",
      )
      lbl_site.pack(side="left", padx=15)

      lbl_mask = ctk.CTkLabel(
          row, text="••••••••••••••••", text_color="#888899", anchor="w"
      )
      lbl_mask.pack(side="left", padx=20)

      btn_del = ctk.CTkButton(
          row,
          text="Elimina",
          width=80,
          fg_color="#aa3333",
          hover_color="#cc4444",
          command=lambda s=site: self.delete_entry(s),
      )
      btn_del.pack(side="right", padx=10)

      btn_copy = ctk.CTkButton(
          row,
          text="Copia Password",
          width=120,
          command=lambda p=pwd, s=site: self.copy_to_clipboard(p, s),
      )
      btn_copy.pack(side="right")

  def copy_to_clipboard(self, pwd, site):
    self.clipboard_clear()
    self.clipboard_append(pwd)
    messagebox.showinfo(
        "Copiato",
        f"La chiave di accesso per '{site}' è stata copiata negli appunti.",
    )

  def delete_entry(self, site):
    if messagebox.askyesno(
        "Conferma", f"Eliminare definitivamente la voce per '{site}'?"
    ):
      del self.vault[site]
      self.save_vault_file()
      self.refresh_vault_list()

  def add_password_popup(self):
    popup = ctk.CTkToplevel(self)
    popup.title("Aggiungi Credenziale")
    popup.geometry("400x380")
    popup.grab_set()

    lbl_s = ctk.CTkLabel(
        popup, text="Servizio / Piattaforma:", font=ctk.CTkFont(weight="bold")
    )
    lbl_s.pack(anchor="w", padx=30, pady=(25, 5))
    ent_site = ctk.CTkEntry(popup, width=340, height=35)
    ent_site.pack(padx=30, pady=(0, 15))
    ent_site.focus()

    lbl_p = ctk.CTkLabel(
        popup, text="Password / Chiave:", font=ctk.CTkFont(weight="bold")
    )
    lbl_p.pack(anchor="w", padx=30, pady=(0, 5))
    ent_pwd = ctk.CTkEntry(popup, width=340, height=35)
    ent_pwd.pack(padx=30, pady=(0, 15))

    def generate_random():
      chars = string.ascii_letters + string.digits + string.punctuation
      strong_pwd = "".join(
          random.SystemRandom().choice(chars) for _ in range(24)
      )
      ent_pwd.delete(0, "end")
      ent_pwd.insert(0, strong_pwd)

    btn_gen = ctk.CTkButton(
        popup,
        text="⚡ Genera Password Blindata (24 char)",
        fg_color="#444455",
        hover_color="#555566",
        command=generate_random,
    )
    btn_gen.pack(padx=30, fill="x", pady=(0, 15))

    def save_item():
      s = ent_site.get().strip()
      p = ent_pwd.get().strip()
      if not s or not p:
        messagebox.showerror(
            "Errore", "Tutti i campi sono obbligatori.", parent=popup
        )
        return

      self.vault[s] = p
      self.save_vault_file()
      self.refresh_vault_list()
      popup.destroy()
      messagebox.showinfo("Successo", f"Credenziale per '{s}' protetta.")

    btn_save = ctk.CTkButton(
        popup, text="Salva nel Database", height=38, command=save_item
    )
    btn_save.pack(padx=30, fill="x")


if __name__ == "__main__":
  app = AegisUltimateApp()
  app.mainloop()
