#!/bin/bash

# Konfiguration der Server
SERVERS=(
    "moodle=root@moodle.talent-factory.xyz"
)

# SSH Key Pfad
SSH_KEY="~/.ssh/id_ed25519"

check_session() {
    local session_name="$1"
    tmux has-session -t "$session_name" 2>/dev/null
    return $?
}

create_server_session() {
    local session_name="$1"
    local server="$2"
    
    # Prüfe ob Session bereits existiert
    if check_session "$session_name"; then
        echo "Session $session_name existiert bereits. Verwende bestehende Session..."
        return 0
    fi
    
    echo "Erstelle neue Session: $session_name für Server: $server"
    
    # Erstelle neue Session mit erstem Fenster
    tmux new-session -d -s "$session_name"
    sleep 1
    
    # Konfiguriere erstes Fenster
    tmux rename-window -t "$session_name" "main"
    tmux send-keys -t "$session_name" "ssh -t -i $SSH_KEY $server" C-m
    sleep 1
    
    # Erstelle Split
    tmux split-window -h -t "$session_name"
    tmux send-keys -t "$session_name" "ssh -t -i $SSH_KEY $server" C-m
    sleep 1
    
    # Erstelle Monitoring Fenster
    tmux new-window -t "$session_name" -n "monitoring"
    tmux send-keys -t "$session_name:monitoring" "ssh -t -i $SSH_KEY $server 'htop'" C-m
    
    # Zurück zum ersten Fenster
    tmux select-window -t "$session_name:main"
    
    echo "Session $session_name wurde erfolgreich erstellt"
}

list_sessions() {
    echo "Verfügbare Sessions:"
    tmux list-sessions
    
    # Zeige detaillierte Fensterinformationen für jede Session
    echo -e "\nFenster-Details:"
    for server in "${SERVERS[@]}"; do
        session_name="${server%%=*}"
        if check_session "$session_name"; then
            echo -e "\nSession: $session_name"
            tmux list-windows -t "$session_name"
        fi
    done
}

attach_session() {
    local session_name="$1"
    
    if [ -z "$TMUX" ]; then
        # Nicht in tmux - direkt verbinden
        echo "Verbinde mit Session $session_name..."
        tmux attach-session -t "$session_name"
    else
        # Bereits in tmux - zu Session wechseln
        echo "Wechsle zu Session $session_name..."
        tmux switch-client -t "$session_name"
    fi
}

main() {
    # Prüfe ob tmux installiert ist
    if ! command -v tmux >/dev/null 2>&1; then
        echo "Tmux ist nicht installiert."
        exit 1
    fi
    
    # Erstelle oder verwende Sessions
    for server in "${SERVERS[@]}"; do
        session_name="${server%%=*}"
        server_address="${server#*=}"
        create_server_session "$session_name" "$server_address"
    done
    
    # Zeige Status aller Sessions
    echo -e "\nStatus der Sessions:"
    list_sessions
    
    # Frage nach Session-Auswahl wenn mehrere verfügbar sind
    local session_count=$(tmux list-sessions 2>/dev/null | wc -l)
    
    if [ "$session_count" -gt 1 ]; then
        echo -e "\nMehrere Sessions verfügbar. Mit welcher Session möchten Sie sich verbinden?"
        select session in $(tmux list-sessions -F "#{session_name}"); do
            if [ -n "$session" ]; then
                attach_session "$session"
                break
            fi
        done
    else
        # Bei nur einer Session, direkt verbinden
        session_name="${SERVERS[0]%%=*}"
        attach_session "$session_name"
    fi
}

main "$@"
