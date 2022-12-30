import can
import time


# Basic usage of Python-can API to control the engine.
# Before trying it, familiarize yourself with the engine documentation, operating modes and user`s guide.


def send(bus, id, data)->can.Message:
    """send a single message and return a reply."""
    # creating Message type instance with COB-ID 0x601 (SDO message)
    msg = can.Message(arbitration_id=id, data=data, is_extended_id=False)

    try: 
        bus.send(msg)       # sending an SDO message
        return bus.recv()   # receiving the reply
    except can.CanError:
        print("CanError! Message doesn`t sent")


def basic_usage():
    # creating CAN bus type instance with VCP 4 and speed 1 Mb/s (defoult speed)
    bus = can.interface.Bus(bustype='seeedstudio', channel='COM4', bitrate=1000000)

    work_mode =      [0x2F, 0x60, 0x60, 0x00, 0x01]                     # Work mode value "1" corresponds with Absolute position mode
    control_word =   [0x2B, 0x40, 0x60, 0x00, 0x2F, 0x00]               # Control word "2F". New position will be executed immediately.
    location_cash =  [0x23, 0x7A, 0x60, 0x00, 0x20, 0xA1, 0x07, 0x00]   # Location cash 500 000
    
    # send SDO message work mode
    reply = send(bus=bus, id=0x601, data=work_mode)
    print("full reply: ", reply)

    # send SDO message control world
    reply = send(bus=bus, id=0x601, data=control_word)
    print("full reply: ", reply)

    # send SDO message Location cash
    reply = send(bus=bus, id=0x601, data=location_cash)
    print("full reply: ", reply)
    
    # here the engine must execute the absolute position 500 000.
    # if the position has not been executed yet - 
    # we need to transmit the message until the position is ready.



if __name__ == "__main__":
    basic_usage() 
