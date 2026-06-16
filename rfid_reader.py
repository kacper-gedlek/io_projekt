#!/usr/bin/env python3
import sys
import signal
import time
import requests

sys.path.insert(0, "/home/admin/MFRC522-python-master")

from mfrc522 import MFRC522


API_URL = "http://localhost:8000/api/rfid"
SCAN_DELAY_SECONDS = 2

kontynuuj = True
ostatni_uid = None
ostatni_czas = 0


def koniec(sygnal, ramka):
    global kontynuuj
    kontynuuj = False


def normalize_uid(uid):
    """
    Zamienia UID z listy bajtów na format zgodny z Moodle idnumber.
    Przykład:
    [111, 222, 333, 444] -> "111222333444"
    """
    return "".join(str(b) for b in uid)


signal.signal(signal.SIGINT, koniec)

czytnik = MFRC522()

print("Przyłóż kartę lub brelok RFID... (Ctrl+C aby zakończyć)")

while kontynuuj:
    status, dane = czytnik.MFRC522_Request(czytnik.PICC_REQIDL)

    if status == czytnik.MI_OK:
        print("Wykryto kartę!")

        status, uid = czytnik.MFRC522_Anticoll()

        if status == czytnik.MI_OK:
            uid_str = normalize_uid(uid)
            teraz = time.time()

            if uid_str != ostatni_uid or teraz - ostatni_czas > SCAN_DELAY_SECONDS:
                ostatni_uid = uid_str
                ostatni_czas = teraz

                print(f"UID karty: {uid_str}")

                try:
                    response = requests.post(f"{API_URL}/{uid_str}", timeout=5)
                    print("Odpowiedź backendu:", response.json())
                except Exception as e:
                    print("Błąd wysyłania UID do backendu:", e)

    time.sleep(0.1)

print("\nZatrzymano.")