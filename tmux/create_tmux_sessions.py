#!/usr/bin/env python3

import os
import subprocess

# Konfiguration der Server
SERVERS = [
    "moodle=root@moodle.talent-factory.xyz"
]

# SSH Key Pfad
SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519")


def check_session(session_name):
    """
    Checks if a tmux session with the given name exists.

    This function uses `subprocess.run` to execute the `tmux has-session` command,
    checking for the existence of a session with the specified name. It suppresses
    any error output and returns a boolean indicating whether the session exists.

    :param session_name: The name of the tmux session to check.
    :type session_name: str
    :return: True if the session exists, otherwise False.
    :rtype: bool
    """
    result = subprocess.run(["tmux", "has-session", "-t", session_name], stderr=subprocess.DEVNULL)
    return result.returncode == 0


def create_server_session(session_name, server):
    """
    Creates a new tmux session for a given server, if the session does not already exist. If the
    session does exist, it uses the existing session.

    The function will:
       - Check if the session already exists.
       - Create a new tmux session and window named "main".
       - SSH into the provided server in the main window.
       - Split the window and SSH into the server in both halves.
       - Create a new window named "monitoring" and SSH into the server to run 'htop'.
       - Return to the main window.

    :param session_name: Name of the tmux session to be created or checked for existence
    :type session_name: str
    :param server: Server address to connect via SSH
    :type server: str
    :return: 0 if the session already exists, otherwise None
    :rtype: int
    """

    # Prüfe ob Session bereits existiert
    if check_session(session_name):
        print(f"Session {session_name} existiert bereits. Verwende bestehende Session...")
        return 0

    print(f"Erstelle neue Session: {session_name} für Server: {server}")

    # Erstelle neue Session mit erstem Fenster
    subprocess.run(["tmux", "new-session", "-d", "-s", session_name])

    # Konfiguriere erstes Fenster
    subprocess.run(["tmux", "rename-window", "-t", session_name, "main"])
    subprocess.run(["tmux", "send-keys", "-t", session_name, f"ssh -t -i {SSH_KEY} {server}", "C-m"])

    # Erstelle Split
    subprocess.run(["tmux", "split-window", "-h", "-t", session_name])
    subprocess.run(["tmux", "send-keys", "-t", session_name, f"ssh -t -i {SSH_KEY} {server}", "C-m"])

    # Erstelle Monitoring Fenster
    subprocess.run(["tmux", "new-window", "-t", session_name, "-n", "monitoring"])
    subprocess.run(
        ["tmux", "send-keys", "-t", f"{session_name}:monitoring", f"ssh -t -i {SSH_KEY} {server} 'htop'", "C-m"])

    # Zurück zum ersten Fenster
    subprocess.run(["tmux", "select-window", "-t", f"{session_name}:main"])

    print(f"Session {session_name} wurde erfolgreich erstellt")


def list_sessions():
    """
    Prints the available tmux sessions and detailed window information
    for each session. The function first prints a list of all available
    tmux sessions. Then, for each server in the SERVERS list, it checks
    if the session exists and prints detailed window information
    for that session.

    :return: None
    :rtype: None
    """

    print("Verfügbare Sessions:")
    subprocess.run(["tmux", "list-sessions"])

    # Zeige detaillierte Fensterinformationen für jede Session
    print("\nFenster-Details:")
    for server in SERVERS:
        session_name = server.split('=')[0]
        if check_session(session_name):
            print(f"\nSession: {session_name}")
            subprocess.run(["tmux", "list-windows", "-t", session_name])


def attach_session(session_name):
    """
    Attaches or switches to the specified tmux session based on the current
    environment. If not in a tmux session, it attaches to the given session.
    If already in a tmux session, it switches to the specified session.

    :param session_name: The name of the tmux session to attach or switch to.
    :type session_name: str
    :return: None
    """

    if not os.environ.get("TMUX"):
        # Nicht in tmux - direkt verbinden
        print(f"Verbinde mit Session {session_name}...")
        subprocess.run(["tmux", "attach-session", "-t", session_name])
    else:
        # Bereits in tmux - zu Session wechseln
        print(f"Wechsle zu Session {session_name}...")
        subprocess.run(["tmux", "switch-client", "-t", session_name])


def main():
    """
    Main function to manage tmux sessions. This function checks if tmux is installed,
    creates or uses existing sessions for the given servers, shows the status of
    all sessions, and prompts the user to select a session if multiple are available.

    :raises SystemExit: If tmux is not installed.
    """

    # Prüfe ob tmux installiert ist
    if subprocess.run(["command", "-v", "tmux"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        print("Tmux ist nicht installiert.")
        exit(1)

    # Erstelle oder verwende Sessions
    for server in SERVERS:
        session_name = server.split('=')[0]
        server_address = server.split('=')[1]
        create_server_session(session_name, server_address)

    # Zeige Status aller Sessions
    print("\nStatus der Sessions:")
    list_sessions()

    # Frage nach Session-Auswahl wenn mehrere verfügbar sind
    session_count = int(
        subprocess.run(["tmux", "list-sessions"], capture_output=True, text=True).stdout.strip().count('\n')) + 1

    if session_count > 1:
        print("\nMehrere Sessions verfügbar. Mit welcher Session möchten Sie sich verbinden?")
        sessions = subprocess.run(["tmux", "list-sessions", "-F", "#{session_name}"], capture_output=True,
                                  text=True).stdout.strip().split('\n')
        for i, session in enumerate(sessions, 1):
            print(f"{i}) {session}")
        selected_session = int(input("Auswahl: ")) - 1
        if 0 <= selected_session < len(sessions):
            attach_session(sessions[selected_session])
    else:
        # Bei nur einer Session, direkt verbinden
        session_name = SERVERS[0].split('=')[0]
        attach_session(session_name)


if __name__ == "__main__":
    main()
