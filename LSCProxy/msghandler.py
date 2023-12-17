"""
Handle the message from the server.
"""


def parse_error_number(n_err):
    """
    Parse the error number and print the error message.
    """
    if n_err == -1:
        print(f"[Error code: {n_err}]")
        print("Master doesn't respond.")
        print("Please check the network whether it could connect to the Internet.")
    elif n_err == -2:
        print(f"[Error code: {n_err}]")
        print("Can't resolve hostname.")
    elif n_err == -3:
        print(f"[Error code: {n_err}]")
        print("Already initialized.")
    elif n_err == -4:
        print(f"[Error code: {n_err}]")
        print("Can't create mutex.")
    elif n_err == -5:
        print(f"[Error code: {n_err}]")
        print("Can't create thread.")
    elif n_err == -10:
        print(f"[Error code: {n_err}]")
        print("This UID is unlicensed.")
        print("Check your UID.")
    elif n_err == -12:
        print(f"[Error code: {n_err}]")
        print("Please initialize the IOTCAPI first.")
    elif n_err == -14:
        print(f"[Error code: {n_err}]")
        print("This SID is invalid.")
        print("Please check it again.")
    elif n_err == -18:
        print(f"[Error code: {n_err}]")
        print("[Warning]")
        print("The amount of session reached the maximum.")
        print("It cannot be connected unless the session is released.")
    elif n_err == -19:
        print(f"[Error code: {n_err}]")
        print("Device didn't register on the server, so we can't find the device.")
        print("Please check the device again.")
        print("Retry...")
    elif n_err == -22:
        print(f"[Error code: {n_err}]")
        print("Session is closed by remote, so we can't access.")
        print("Please close it or establish the session again.")
    elif n_err == -23:
        print(f"[Error code: {n_err}]")
        print("We can't receive an acknowledgment character within a TIMEOUT.")
        print("It might be that the session is disconnected by remote.")
        print("Please check the network whether it is busy or not.")
        print("And check the device and user equipment work well.")
    elif n_err == -24:
        print(f"[Error code: {n_err}]")
        print("Device doesn't listen or the sessions of the device reached the maximum.")
        print("Please release the session and check the device whether it listens or not.")
    elif n_err == -26:
        print(f"[Error code: {n_err}]")
        print("Channel isn't on.")
        print("Please open it by IOTC_Session_Channel_ON() or IOTC_Session_Get_Free_Channel()")
        print("Retry...")
    elif n_err == -31:
        print(f"[Error code: {n_err}]")
        print("All channels are occupied.")
        print("Please release some channels.")
    elif n_err == -32:
        print(f"[Error code: {n_err}]")
        print("Device can't connect to the Master.")
        print("Don't let the device use a proxy.")
        print("Close the firewall of the device.")
        print("Or open the device's TCP ports 80, 443, 8080, 8000, 21047.")
    elif n_err == -33:
        print(f"[Error code: {n_err}]")
        print("Device can't connect to the server by TCP.")
        print("Don't let the server use a proxy.")
        print("Close the firewall of the server.")
        print("Or open the server's TCP ports 80, 443, 8080, 8000, 21047.")
        print("Retry...")
    elif n_err == -40:
        print(f"[Error code: {n_err}]")
        print("This UID's license doesn't support TCP.")
    elif n_err == -41:
        print(f"[Error code: {n_err}]")
        print("Network is unreachable.")
        print("Please check your network.")
        print("Retry...")
    elif n_err == -42:
        print(f"[Error code: {n_err}]")
        print("Client can't connect to a device via Lan, P2P, and Relay mode.")
    elif n_err == -43:
        print(f"[Error code: {n_err}]")
        print("Server doesn't support UDP relay mode.")
        print("So the client can't use UDP relay to connect to a device.")
    else:
        pass
