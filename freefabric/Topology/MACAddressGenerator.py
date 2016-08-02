print "Script executed!"

class MacAddress(object):
    pointer = 5
    mac_address = []
    def __init__(self):
        self.pointer = 5;
        self.mac_address = [0x02, 0xFF, 0xFF, 0xFF, 0xFF, 0xFE]

    def generate_next_mac_address(self):
        while (self.mac_address[self.pointer] == 0xFF):
            if self.pointer != 1:
                self.mac_address[self.pointer] = 0x00
                self.pointer -= 1
            else:
                raise ValueError('Exhaust')
                # Or throw exception

        self.mac_address[self.pointer] += 1
        self.pointer = 5
        return self.mac_address

    def generate_nth_mac_address(self, n):
        for address in range(n):
            self.generate_next_mac_address()
        return self.mac_address

if __name__ == '__main__':
    mac = MacAddress()
    try:
        mac_lst = mac.generate_next_mac_address()
        print mac_lst
    except ValueError as err:
        print (err)

    try:
        mac_lst = mac.generate_next_mac_address()
        print mac_lst
    except ValueError as err:
        print (err)

