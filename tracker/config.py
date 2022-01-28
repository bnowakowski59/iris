import os, sys
################
#  DO NOT EDIT #
################

#  Port szeregowy
PORT = '/dev/serial0'

#  Nazwa zadania
TASK_NAME = 'Test_20220123'

#  Sciezki do plikow.
TEMPORARY_COORDINATES_FILE = '/home/pi/iris/tracker/logs/__tmp_position.csv'
TEST_COORDINATES_FILE = '/home/pi/iris/tracker/logs/__test_position.csv'

# Numer id do BD.
DEVICE_ID = '123456'

#  Numer seryjny urzadzenia
serial_number = '867717033828212'


#############
#  EDITABLE #
#############

#  Wysylanie sms True/False
SMS_SENDER = True
SMS_BOOT = False
SMS_MPU = False

#  Numer telefonu na jaki beda wysylane wiadomosci.
PHONE_NUMBER = '572720038'

#  Liczba odczytow GNSS.
NUMBER_OF_GNSS_READS = 10

# Czas pomiedzy odczytami poozycji GNSS
SECONDS_BETWEEN_READS = 30

# Czas pomiędzy odczytami MPU.
TIMEOUT_MPU = 1

#  Liczba prob otrzymania prawidlowej pozycji GNSS.
FIX_ITERATIONS = 10

#  Wlaczenie modulu MPU True/False.
MPU_BOARD = True

#  Wyswietlanie print() - True/Fasle
print_status = True

if not print_status:
    sys.stdout = open(os.devnull, 'w')


