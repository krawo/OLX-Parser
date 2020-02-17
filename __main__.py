from olx_parser import *

if __name__ == '__main__':
    print("Podaj URL z olx")
    url = input()
    print("Podaj nazwe pliku xls")
    file = input()
    parse_olx(url, file)
    print("Wcisnij ENTER aby wyjsc")
    input()