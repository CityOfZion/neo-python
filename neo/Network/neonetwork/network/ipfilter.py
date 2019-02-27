from ipaddress import IPv4Network
from contextlib import suppress

"""
 A class for filtering IPs.

 * The whitelist has precedence over the blacklist settings
 * Host masks can be applied
 * When using host masks do not set host bits (leave them to 0) or an exception will occur

 Common scenario examples:

 1) Accept only specific trusted IPs
    {
            'blacklist': [
                '0.0.0.0/0'
            ],
            'whitelist': [
                '10.10.10.10',
                '15.15.15.15'
            ]
    } 
2) Accept only a range of trusted IPs
    # accepts any IP in the range of 10.10.10.0 - 10.10.10.255
    {
            'blacklist': [
                '0.0.0.0/0'
            ],
            'whitelist': [
                '10.10.10.0/24',
            ]
    } 

3 ) Accept everybody except specific IPs
    # can be used for banning bad actors
        {
            'blacklist': [
                '12.12.12.12',
                '13.13.13.13'
            ],
            'whitelist': [
            ]
    } 


"""


class IPFilter():
    config = {'blacklist': [], 'whitelist': []}

    def is_allowed(self, host_address) -> bool:
        address = IPv4Network(host_address)

        is_allowed = True

        for ip in self.config['blacklist']:
            disallowed = IPv4Network(ip)
            if disallowed.overlaps(address):
                is_allowed = False
                break
        else:
            return is_allowed

        # can override blacklist
        for ip in self.config['whitelist']:
            allowed = IPv4Network(ip)
            if allowed.overlaps(address):
                is_allowed = True

        return is_allowed

    def blacklist_add(self, address) -> None:
        self.config['blacklist'].append(address)

    def blacklist_remove(self, address) -> None:
        with suppress(ValueError):
            self.config['blacklist'].remove(address)

    def whitelist_add(self, address) -> None:
        self.config['whitelist'].append(address)

    def whitelist_remove(self, address) -> None:
        with suppress(ValueError):
            self.config['whitelist'].remove(address)


ipfilter = IPFilter()
