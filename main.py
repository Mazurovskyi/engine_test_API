import can
import time
import basic


# Extended usage of Python-can API to control the engine. 
# Before trying it, familiarize yourself with the engine documentation, operating modes and user`s guide.


def send_sdo(id, dataframe, bus, sender_idx)->list:
    """Sends a single SDO message into CAN bus until the response contains the desired COB-ID and index. 
    Returns a motor reply dataframe in a list form. 
    If transferring was not success returns None.\n

    Example:
    data = location_cash(300000)\n
    reply = send_sdo(id=601, dataframe=data, bus=bus)\n
    print(reply)    # [60 7A 60 00]"""

    msg = can.Message(arbitration_id=id, data=dataframe, is_extended_id=False)

    try:
        bus.send(msg)
        reply = bus.recv()

        # we send the position and receive a response until the response 
        # contains the desired COB-ID and inside object address index of the sender specified in "kind" parameter:
        while (reply.arbitration_id != 0x581) or (list(reply.data)[1:3] != sender_idx):
            bus.send(msg)
            reply = bus.recv()

        print("reply.data: ",list(reply.data),  "reply.arbitration_id: ",hex(reply.arbitration_id))
        return list(reply.data)

    except can.CanError:
        print("CanError! Message doesn`t sent")
        return None


def location_cash(val:int)->list:
    """Creates a location dataframe from decimal value.
    This returned list can be used as dataframe parametr in send_sdo() function.\n

    Example:\n
    x = location_cash(300000)\n
    print(x)    # [35, 122, 96, 0, 224 147 04 00]"""

    location_cash = [35, 122, 96, 0]    # the number of bytes, index and sub-index of inside oject address [0x23, 0x7A, 0x60, 0x00]
    location_cash.extend(list(val.to_bytes(length=4,byteorder='little')))
    return location_cash


def location(data: list)->int:
    """Converts a location dataframe into decimal value.\n

    Example:
    x = location_cash(300000)\n
    print(x)             # [35, 122, 96, 0, 224 147 04 00]\n
    print(location(x))   # 300000"""

    location = data[4:]
    location.reverse()
    sum = 0
    for el in location:
        sum = (sum << 8) + el
    
    return sum


def is_equal(current:int, exp:int)->bool:
    """Checks if the current position differs from the expected position
    by no more than 18 units - returns False. It applies to compare current and expected position
    because positioning accuracy allows a backlash of up to 18 units\n 
    
    Example:\n
    a = 10;
    b = 19;
    print(is_equal(a,b))    #True\n
    a = 10;
    b = -30;
    print(is_equal(a,b))    #False"""

    if abs(current - exp) > 18: return False
    return True


def test_engine():
    work_mode =         [0x2F, 0x60, 0x60, 0x00, 0x01]                    # work mode = "1". Absolute position mode
    control_word_2F =   [0x2B, 0x40, 0x60, 0x00, 0x2F, 0x00]              # control world "2F". New position execute immediately
    actual_position =   [0x40, 0x64, 0x60, 0x00]                          # actual position request
    acceleration_fast = [0x23, 0x83, 0x60, 0x00, 0x20, 0x4E, 0x00, 0x00]  # fast acceleration "20 000"
    acceleration_slow = [0x23, 0x83, 0x60, 0x00, 0xE8, 0x03, 0x00, 0x00]  # slow acceleration "1 000"

    bus = can.interface.Bus(bustype='seeedstudio', channel='COM4', bitrate=1000000)

    # indexes of inside object address. 
    idx_actual_position = list(actual_position[1:3])    # [0x64, 0x60]
    idx_location =        [122, 96]                     # [0x7A, 0x60]
    idx_acceleration =    list(acceleration_fast[1:3])  # [0x83, 0x60]
    idx_control_word =    list(control_word_2F[1:3])    # [0x40, 0x60]
    idx_work_mode =       list(work_mode[1:3])          # [0x60, 0x60]

    try:
        # set work mode in absolute position
        send_sdo(0x601,work_mode,bus,sender_idx=idx_work_mode)

        # set control world to "2F". New position execute immediately
        send_sdo(0x601,control_word_2F,bus,sender_idx=idx_control_word)

        target_position = 0     # it will be incremented to "3 000 000" value

        while True:
            # set slow acceleration
            send_sdo(0x601,acceleration_slow,bus,sender_idx=idx_acceleration)
            
            while target_position < 3000000:
                
                target_position+=500000

                # send the position until the actual position equals the specified one.
                # positioning accuracy allows a backlash of up to 18 units. That`s why we use is_equal().
                while not is_equal(location(send_sdo(0x601,actual_position,bus,sender_idx=idx_actual_position)), target_position):

                    print("Send target_position: ",target_position)
                    send_sdo(0x601,location_cash(target_position),bus,sender_idx=idx_location)
                    print("\n")

                time.sleep(1)

            
            # Here the actual position is equal 3 000 000.
            # set fast acceleration
            send_sdo(0x601,acceleration_fast,bus,sender_idx=idx_acceleration)

            target_position = 0

            while not is_equal(location(send_sdo(0x601,actual_position,bus,sender_idx=idx_actual_position)), target_position):
                
                print("Send target_position:", target_position)
                send_sdo(0x601,location_cash(target_position),bus,sender_idx=idx_location)
                print("\n")
  
            time.sleep(2)

    except KeyboardInterrupt:
        print("KeyboardInterrupt accepted! Moving to the origin...")

        target_position = 0

        while not is_equal(location(send_sdo(0x601,actual_position,bus,sender_idx=idx_actual_position)), target_position):

            print("Send target_position:", target_position)
            send_sdo(0x601,location_cash(target_position),bus,sender_idx=idx_location)



if __name__ == "__main__":
    #basic.basic_usage() 
    test_engine()