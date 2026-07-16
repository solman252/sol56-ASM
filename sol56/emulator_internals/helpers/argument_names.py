reg_keys = {
    '0001':'a',
    '0010':'b',
    '0011':'c',
    '0100':'d',
    '0101':'e',
    '0110':'f',
    '0111':'g',
    '1000':'h',
    '1001':'res',
}

flag_keys = {
    '0000':'s',
    '0001':'c',
    '0010':'z',
    '0011':'n',
    '0100':'o',
}

time_keys = {
    '0000':'uptime',
    '0001':'milli-second of second',
    '0010':'second of minute',
    '0011':'minute of hour',
    '0100':'hour of day',
    '0101':'day of the week',
    '0110':'day of the month',
    '0111':'day of the year',
    '1000':'month',
    '1001':'year',
}

intr_keys = {
    '00000000': 'all',
    '00010000': 'pc',
    '00100000': 'reg',
    '00100001': 'reg all',
    '00110000': 'flag',
    '00110001': 'flag all',
    '01000000': 'state',
}