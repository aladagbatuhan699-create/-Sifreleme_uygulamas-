import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from customtkinter import CTkImage
import keyring
import os
import threading
import time
from LocalAuthentication import LAContext

# ----------------------------
# Güvenlik Mantığı
# ----------------------------
def authenticate():
    context = LAContext.alloc().init()
    auth_result = {"success": False, "finished": False}

    def callback(success, error):
        auth_result["success"] = success
        auth_result["finished"] = True

    context.evaluatePolicy_localizedReason_reply_(
        2, "İşlem onayı için Touch ID gereklidir.", callback
    )

    while not auth_result["finished"]:
        time.sleep(0.1)

    return auth_result["success"]

# ----------------------------
# Ana Uygulama
# ----------------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bakırçay Güvenli Şifreleyici")
        self.geometry("500x550")
        self.configure(fg_color="#800000")

        # -------- LOGO --------
        try:
            self.logo_image = CTkImage(
                light_image=Image.open("logo.png"),
                dark_image=Image.open("logo.png"),
                size=(120, 120)
            )
            ctk.CTkLabel(self, image=self.logo_image, text="").pack(pady=10)
        except Exception as e:
            print("Logo yüklenemedi:", e)

        # Başlık
        ctk.CTkLabel(
            self,
            text="Bakırçay Dosya Şifreleme",
            font=("Helvetica", 20, "bold"),
            text_color="white"
        ).pack(pady=10)

        # İlerleme Çubuğu
        self.progress_bar = ctk.CTkProgressBar(
            self, width=300, progress_color="#2D5A27"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=20)

        # Durum Yazısı
        self.status_label = ctk.CTkLabel(
            self, text="Dosya Seçiniz", text_color="white"
        )
        self.status_label.pack(pady=5)

        # Butonlar
        ctk.CTkButton(
            self, text="Şifrele",
            fg_color="#1B4D3E",
            command=self.encrypt_action
        ).pack(pady=10)

        ctk.CTkButton(
            self, text="Çöz",
            fg_color="#1B4D3E",
            command=self.decrypt_action
        ).pack(pady=10)

        # Anahtar yoksa oluştur
        if not keyring.get_password("SifrelemeSistemi", "BatuKey"):
            keyring.set_password(
                "SifrelemeSistemi",
                "BatuKey",
                "Bakircay2026!"
            )

    def encrypt_action(self):
        path = filedialog.askopenfilename()
        if path:
            threading.Thread(
                target=self.run_process,
                args=(path, "enc"),
                daemon=True
            ).start()

    def decrypt_action(self):
        path = filedialog.askopenfilename(
            filetypes=[("Batu Dosyası", "*.batu")]
        )
        if path:
            threading.Thread(
                target=self.run_process,
                args=(path, "dec"),
                daemon=True
            ).start()

    def run_process(self, file_path, mode):
        if not authenticate():
            messagebox.showwarning("Hata", "Kimlik doğrulanamadı!")
            return

        try:
            key = keyring.get_password(
                "SifrelemeSistemi", "BatuKey"
            ).encode()

            file_size = os.path.getsize(file_path)

            if mode == "enc":
                out_path = file_path + ".batu"
            else:
                out_path = file_path.replace(".batu", "_cozulmus")
                if "." not in os.path.basename(out_path):
                    out_path += ".txt"

            with open(file_path, "rb") as f_in, open(out_path, "wb") as f_out:
                processed = 0

                while True:
                    chunk = f_in.read(1024 * 64)
                    if not chunk:
                        break

                    data = bytearray()
                    for i, b in enumerate(chunk):
                        shift = key[(processed + i) % len(key)]
                        val = (b + shift) % 256 if mode == "enc" else (b - shift) % 256
                        data.append(val)

                    f_out.write(data)
                    processed += len(chunk)

                    self.progress_bar.set(processed / file_size)
                    self.status_label.configure(
                        text=f"%{int((processed / file_size) * 100)} işlendi..."
                    )

            messagebox.showinfo("Başarılı", "İşlem tamamlandı!")
            self.progress_bar.set(0)
            self.status_label.configure(text="Hazır")

        except Exception as e:
            messagebox.showerror("Hata", str(e))

# ----------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()