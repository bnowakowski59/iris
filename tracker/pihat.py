# !/usr/bin/env python3
import subprocess
import serial
import RPi.GPIO as GPIO

from time import sleep
from config import *


class SerialPort:

    @staticmethod
    def open():
        """
        Otwarcie portu szeregowego do modułu Waveshare 13460.
        """
        serial_port = serial.Serial(PORT,
                            baudrate=115200,
                            bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            timeout=1
                            )
        return serial_port

    @staticmethod
    def close(serial_port):
        """
        Zamknięcie portu szeregowego do modułu Waveshare 13460.
        """
        serial_port.close()

class GPRS:
    """
    GPRS module from HAT

    """

    def openConnection(self):
        """
        Connect to pppd network from /etc/ppp/pears/gprs
        """

        print(f"Opening PPPD connection ...")
        #  Check if PPPD is running by looking into syslog output.
        output1 = subprocess.check_output("cat /var/log/syslog | grep pppd | tail -1", shell=True)
        if b"secondary DNS address" not in output1 and b"locked" not in output1:
            while True:
                #  Start GPRS process.
                subprocess.Popen("sudo pon gprs", shell=True)
                sleep(2)
                output2 = subprocess.check_output("cat /var/log/syslog | grep pppd | tail -1", shell=True)
                # print(f"Output2: {output2}")
                if b"script failed" not in output2:
                    print(f"PPPD connection opened - {True}")
                    return True
                    sleep(0.5)
                else:
                    print(f"Connect error")
                    sleep(0.5)

    def closeConnection(self):
        """
        Disconect from pppd network from /etc/ppp/pears/gprs
        """
        print(f"Closing PPPD connection ...")
        #  Stop GPRS process.
        subprocess.Popen('sudo poff gprs', shell=True)
        #  Chceck if connection is terminated.
        while True:
            output = subprocess.check_output("cat /var/log/syslog | grep pppd | tail -1", shell=True)

            if b'Exit' or b'None' in output:
                print(f"PPPD connection closed - {True}")
                sleep(0.5)
                return True


class GPS:
    """
    GPS module from HAT

    """

    def __init__(self, ser):
        self.ser = ser

    def get_gps_position(self):
        global FIX_ITERATIONS
        answer = 0
        i = 0
        rec_buff = ''

        send_at('AT+CGNSPWR=1', 'OK', 1, self.ser)
        sleep(1)

        while True:
            answer = send_at('AT+CGNSINF', '+CGNSINF: 1,1,', 1, self.ser)

            if '+CGNSINF: 1,1,' in answer[0]:
                array = answer[0].split(",")
                timeSplit = array[2].split(".")
                dateString = timeSplit[0]  # time
                latitudeFloat = float(array[3])  # latitude
                longitudeFloat = float(array[4])  # longitude
                speedString = float(array[6])  # speed
                print(f'Fix - {answer[1]}')

                return latitudeFloat, longitudeFloat, dateString, speedString

            if '+CGNSINF: 1,0,' in answer[0]:
                print(f'Fix - {answer[1]}')
                i += 1

                if i == FIX_ITERATIONS:
                    latitudeFloat = 0
                    longitudeFloat = 0
                    dateString = '0'
                    speedString = 0
                    return latitudeFloat, longitudeFloat, dateString, speedString

                sleep(1)
                continue

            if '+CGNSINF: 0,,,,' or '+CGNSINF: 0,0,' in answer[0]:
                send_at('AT+CGNSPWR=1', 'OK', 1, self.ser)
                sleep(1)
                continue


class GSM:
    """
    GSM module from HAT.
    """

    def __init__(self, serial_port):
        self.serial_port = serial_port

    def send_sms(self, PHONE_NUMBER, message):
        """
        Send SMS to phone_number
        """

        phone_number = f'"{PHONE_NUMBER}"'
        send_at('AT+CMGF=1', 'OK', 1, self.serial_port)
        send_at('AT+CMGS=' + phone_number, '', 1, self.serial_port)
        self.serial_port.write(message.encode() + b"\r")
        self.serial_port.write(bytes([26]))

        print(f"SMS send to {phone_number}")

    def read_sms(self):
        """
        Read income SMS, return message state on output:
        Start
        """

        send_at('AT+CMGF=1', 'OK', 1, self.serial_port)
        answer = send_at('AT+CMGL="REC UNREAD"', PHONE_NUMBER, 1, self.serial_port)
        sleep(5)
        self.serial_port.write(b'AT+CMGD=1,4\r')
        if PHONE_NUMBER in answer[0]:
            if 'Pozycja\r\n' in answer[0]:
                return 'Pozycja'

            if 'Sygnal\r\n' in answer[0]:
                return 'Sygnal'

            else:
                return 'None'

        return 'None'

    def read_signal_strength(self):
        """
        Return an integer between 1 and 99, representing the current
        signal strength of the GSM network, False if we don't know, or
        None if the modem can't report it.
        """

        while True:
            answer = send_at('AT+CSQ', 'CSQ', 1, self.serial_port)

            if "+CSQ: " in answer[0]:
                try:
                    answer_array = answer[0].split(",")
                    csq = int(answer_array[0].split()[2])
                    return csq if csq < 99 else False

                except IndexError as err:
                    print(err)


class Power:

    def __init__(self, serial_port):
        self.serial_port = serial_port

    def check_power(self):
        answer = send_at('AT', 'OK', 1, self.serial_port)

        if answer[1] is True:
            return True
        else:
            return False

    @staticmethod
    def power_up():
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.OUT)
        while True:
            GPIO.output(4, GPIO.LOW)
            sleep(4)
            GPIO.output(4, GPIO.HIGH)
            break
        GPIO.cleanup()
        sleep(10)

    @staticmethod
    def power_down():
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.OUT)
        while True:
            GPIO.output(4, GPIO.LOW)
            sleep(4)
            GPIO.output(4, GPIO.HIGH)
            break
        GPIO.cleanup()
        sleep(10)
        
    def show_information(self):
        """
        CGMI - zwraca nazwę producenta modułu GSM.
        :return:
        """
        answer = send_at('AT+CGMI', "CGMI", 1, self.serial_port)
        cgmi = answer[0].split(",")
        cgmi = cgmi[0].split()[1]

        """
        CGMM - zwraca nazwę modułu GSM.
        """
        answer = send_at('AT+CGMM', "CGMM", 1, self.serial_port)
        cgmm = answer[0].split(",")
        cgmm = cgmm[0].split()[1]

        """
        CGMR - zwraca numer wersi modułu.
        """
        answer = send_at('AT+CGMR', "CGMR", 1, self.serial_port)
        cgmr = answer[0].split(",")
        cgmr = cgmr[0].split()[1].replace("Revision:", "")

        """
        CNUM - zwraca numer abonenta karty SIM.
        """
        answer = send_at('AT+CNUM', "CNUM", 1, self.serial_port)
        cnum = answer[0].split(",")[1].replace('"', '')

        """
        CGSN - zwraca numer IMEI modułu.
        """
        answer = send_at('AT+CGSN', "CGSN", 1, self.serial_port)
        cgsn = answer[0].split(",")
        cgsn = cgsn[0].split()[1]

        print(f'Nazwa producenta: {cgmi}\n'
              f'Nazwa modułu: {cgmm}\n'
              f'Numer wersji: {cgmr}\n'
              f'Numer abonenta: {cnum}\n'
              f'Numer IMEI: {cgsn}\n')


def send_at(command, answer, timeout, serial_port):
    rec_buff = ''
    serial_port.write((command + '\r\n').encode())
    sleep(timeout)
    if serial_port.inWaiting():
        sleep(0.01)
        rec_buff = serial_port.read(serial_port.inWaiting())
        print(rec_buff)
    if rec_buff != '':
        if answer not in rec_buff.decode():
            # print(command + ' ERROR')
            # print(command + ' back:\t' + rec_buff.decode())
            return rec_buff.decode(), False
        else:
            return rec_buff.decode(), True
    else:
        return rec_buff, False
