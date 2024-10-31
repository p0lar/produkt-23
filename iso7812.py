MII_DETAILS = {}
MII_DETAILS["0"]  = "Reserved for future use by ISO/TC 68."
MII_DETAILS["00"] = "Institutions other than card issuers."
MII_DETAILS["1"]  = "Airlines."
MII_DETAILS["2"]  = "Airlines and other future assignments."
MII_DETAILS["3"]  = "Travel and entertainment."
MII_DETAILS["4"]  = "Banking/financial."
MII_DETAILS["5"]  = "Banking/financial."
MII_DETAILS["59"] = "Financial institutions not registered by ISO."
MII_DETAILS["6"]  = "Merchandising and banking."
MII_DETAILS["7"]  = "Petroleum."
MII_DETAILS["8"]  = "Telecommunications and other future assignments."
MII_DETAILS["89"] = "Telecommunications administrations and private operating agencies."
MII_DETAILS["9"]  = "Reserved for national use."

PAN_DETAILS = {}

def print_pan_details(pan: str):
    MII = pan[0]
    CC = None
    offset = 0
    if (MII == "0" and pan[1] == "0") or (MII == "5" and pan[1] == "9") or (MII == "8" and pan[1] == "9"):
        MII += pan[1]
    offs = len(MII)
    if MII == "9":
        CC = pan[offs:offs+3]

    remaining = 8 - len(MII)
    if CC is not None:
        remaining -= 3
    II = pan[offs:offs+remaining]
    IAI = pan[offs+remaining:-1]
    CD = pan[-1:]

    print(f"  MII: {MII} -> {MII_DETAILS[MII]}")
    print(f"  IIN: {II} -> ?")
    print(f"  CC:  {CC} -> ?")
    print(f"  IAI:  {IAI}")
    print(f"  CD:  {CD}")
