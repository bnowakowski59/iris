# !/usr/bin/env python3

from pihat import *
from config import *
from mpu import checkMPU
from mongoDB import mongoDB
from time import sleep

from format_date import formatDate

import serial

nr_seq = 1

if __name__ == "__main__":

    #  Ustawienie numeru sekwencji.
    nr_seq = 1
    
    #  Otwarcie portu szeregowego do urzadzenia.
    try:
        serial_port = SerialPort().open()
    except OSError:
        GPRS().closeConnection()
        sleep(1)
        serial_port = SerialPort().open()

    #  Sprawdz czy moduł jest włączony.
    while True:
        check_board_power = Power(serial_port).check_power()

        if check_board_power is False:
            print(f'Zasilanie modułu: {check_board_power}\n'
                  f'Włączenie modułu ... ')
            Power(serial_port).power_up()
            Power(serial_port).show_information()

            if SMS_BOOT:
                csq = GSM(serial_port).read_signal_strength()
                sms = f'Sila sygnalu: {csq}'
                print(sms)
                GSM(serial_port).send_sms(PHONE_NUMBER, sms)
            break
            
        else:
            print(f'Zasilanie modułu: {check_board_power}\n')
            break

    #  Glowna petla
    while True:
        
        #  Zamknij poloaczenie GPRS
        GPRS().closeConnection()

        #  Otwarcie portu szeregowego do urzadznia.
        serial_port = SerialPort().open()

        #  Stworz pusta liste predkosci.
        speed_list = []

        #  Uzyskaj pozycje GNSS.
        for i in range(NUMBER_OF_GNSS_READS):
            latitude, longitude, date, speed = GPS(serial_port).get_gps_position()

            print(f'szerokosc geograficzna: {latitude}\n'
                  f'dlugosc geograficzna: {longitude}\n'
                  f'data/czas: {date}\n'
                  f'predkosc: {speed:.2f}')
            
            #  Jeżeli pozycje są większe od 0, zapisz je do plików.
            if (latitude and longitude) > 0:
                if date > '19000000000000':
                    date = formatDate(date)
                    gnss_coordinates = f'{nr_seq},{date},{latitude},{longitude}'
                    nr_seq += 1

                #  Plik tymczasowy do agregacji danych.
                with open(TEMPORARY_COORDINATES_FILE, 'a') as f:
                    f.write(gnss_coordinates)
                    f.write("\n")
                    f.close()

                #  Plik testowy do pużniejszego usunięcia.
                with open(TEST_COORDINATES_FILE, 'a') as f:
                    f.write(gnss_coordinates)
                    f.write("\n")
                    f.close()

            speed_list.append(speed)

            # W przypadku otryzmania sms - napisz sms na wskazanych PHONE_NUMBER.
            if SMS_SENDER:
                sms_flag = False
                sms_message = ''
                sms = GSM(serial_port).read_sms()

            #  Sprawdz frazy w otrzymanych wiadomosciach sms.
                if 'Pozycja' in sms:
                    sms_flag = True
                    if (latitude and longitude) > 0:
                        sms_message = f"http://maps.google.com/?q={latitude},{longitude}"
                    else:

                        sms_message = f"Brak pozycji GNSS."

                if 'Sygnal' in sms:
                    sms_flag = True
                    csq = GSM(serial_port).read_signal_strength()
                    sms_message = f'Sila sygnalu GSM: {csq}'

                if sms_flag is True:
                    GSM(serial_port).send_sms(PHONE_NUMBER, sms_message)

            sleep(SECONDS_BETWEEN_READS)

        #  Oblicz srednia predkosc urzadzenia.
        average_speed = sum(speed_list) / NUMBER_OF_GNSS_READS
        print(f"\nPredkosc: srednia: {average_speed:.2f}")

        #  Wyslanie pozycji z pliku tymczasowego do bazdy danych.
        if GPRS().openConnection():
            print(f"Sprawdzam polaczenie do bazy danych ...")
            mongoDB(TASK_NAME, TEMPORARY_COORDINATES_FILE, DEVICE_ID)
            print(f"Polaczenie zakonczono.")
            GPRS().closeConnection()
            sleep(0.1)
            serial_port.close()

        #  Jezeli ustawiono MPU_BOARD na True to aktywuj Multi Processing Unit.
        if not MPU_BOARD:
            continue
        #  Jezeli srednia predkosc jest mniejsza niz average_speed - uruchom MPU.
        if average_speed > 3.0:
            print("Pojazd w ruchu. Kontynuuje prace urzadzenia.")
            continue
        else:
            Power(serial_port).power_down()
            mpu = checkMPU() # (wiadomosc_sms, bool)
            sms = mpu[0] # wiadomosc_sms

            if mpu[1]:
                serial_port = SerialPort().open()
                Power(serial_port).power_up()

                if sms == 'Wykryto rotacje Iris':
                    GSM(serial_port).send_sms(PHONE_NUMBER, sms)
                    
                if SMS_MPU:
                    GSM(serial_port).send_sms(PHONE_NUMBER, sms)

                continue
