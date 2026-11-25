#!/usr/bin/env python3
"""Numbered menu for setup.sh. Every action runs setup.sh again with flags."""

from __future__ import annotations

import getpass
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "setup.sh"


def run(args: list[str]) -> int:
    print()
    print(">", " ".join(args))
    print("Compile and map extraction stay in this terminal and can take hours.")
    return subprocess.call([str(SETUP), *args])


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        return ""


def confirm(expected: str) -> str:
    typed = ask(f"Type {expected} to confirm: ")
    if typed != expected:
        print("Not confirmed.")
        return ""
    return typed


def pause() -> None:
    ask("Press Enter. ")


def realms() -> None:
    while True:
        print(
            "\nRealms\n"
            "  1) Status\n"
            "  2) Set up one realm (compile, database, extract, start)\n"
            "  3) Start\n"
            "  4) Stop\n"
            "  5) Restart\n"
            "  6) Logs\n"
            "  7) List cores\n"
            "  0) Back"
        )
        choice = ask("> ")
        if choice in {"", "0"}:
            return
        if choice == "1":
            run(["status"])
        elif choice == "2":
            short = ask("Realm short (vanilla, tbc, wotlk, … or all): ")
            if short:
                run(["setup", short])
        elif choice == "3":
            short = ask("Realm short, or Enter for every built realm: ")
            run(["up", short] if short else ["up"])
        elif choice == "4":
            short = ask("Realm short, or Enter to stop the stack: ")
            run(["down", short] if short else ["down"])
        elif choice == "5":
            short = ask("Realm short: ")
            if short:
                run(["restart", short])
        elif choice == "6":
            short = ask("Realm short: ")
            if short:
                run(["logs", short])
        elif choice == "7":
            run(["list"])
        pause()


def access() -> None:
    print(
        "\nHow players connect\n"
        "  1) This machine (vanilla.local and the other loopback names)\n"
        "  2) One public address, a unique port for each realm\n"
        "  3) A DNS name and its own address for each realm (stock ports)\n"
        "  4) Show the current choice\n"
        "  5) Open the firewall for the current choice\n"
        "  0) Back"
    )
    choice = ask("> ")
    if choice == "1":
        run(["access", "set", "loopback"])
    elif choice == "2":
        address = ask("Public IPv4 address: ")
        if address:
            run(["access", "set", "ports", "--address", address])
    elif choice == "3":
        print("One line per realm: short=hostname,ip")
        print("Two realms cannot share an address. Stock ports bind once per address.")
        print("An empty line finishes the list.")
        args = ["access", "set", "public"]
        while True:
            line = ask("realm: ")
            if not line:
                break
            args.extend(["--realm", line])
        if len(args) > 4:
            run(args)
    elif choice == "4":
        run(["access", "show"])
    elif choice == "5":
        typed = confirm("open")
        if typed:
            run(["access", "firewall", "--confirm", "open"])
    pause()


def cores() -> None:
    run(["list"])
    short = ask("Realm short: ")
    project = ask("Project id (the CORE column): ")
    if not short or not project:
        return
    code = subprocess.call([str(SETUP), "core", "set", short, project])
    if code == 2:
        print("refuse leaves the realm alone.")
        print("reimport dumps that realm, then drops its databases.")
        print("keep replaces the world database when the new core can open the accounts.")
        policy = ask("On existing players [refuse/reimport/keep]: ")
        if policy in {"refuse", "reimport", "keep"}:
            run(["core", "set", short, project, "--on-data", policy])
    modules = ask("Modules separated by spaces, or Enter to leave them: ")
    if modules:
        run(["core", "modules", short, *modules.split()])
    pause()


def updates() -> None:
    print(
        "\nUpdates\n"
        "  1) Rebuild every built core whose source moved\n"
        "  2) Check one realm (does not build)\n"
        "  3) Apply one realm"
    )
    choice = ask("> ")
    if choice == "1":
        print("This compiles in the foreground and can take hours.")
        run(["update"])
        pause()
        return
    short = ask("Realm short, or all: ")
    if not short:
        return
    if choice == "2":
        run(["update", "check", short])
    elif choice == "3":
        print("skip leaves MariaDB alone. world replaces the world database.")
        print("full dumps and drops that realm's databases.")
        db = ask("Database action [skip/world/full]: ")
        if db not in {"skip", "world", "full"}:
            print("Not applied.")
            return
        args = ["update", "apply", short, "--db", db]
        if db != "skip":
            typed = confirm(short)
            if not typed:
                return
            args.extend(["--confirm", typed])
        run(args)
    pause()


def erase() -> None:
    print(
        "\nErase\n"
        "  1) Container only\n"
        "  2) That realm's databases\n"
        "  3) Characters only\n"
        "  4) Maps, vmaps, and mmaps\n"
        "  5) Compiled install\n"
        "  6) The whole realm\n"
        "  7) The shared MariaDB volume (every realm)\n"
        "  0) Back"
    )
    scopes = {
        "1": "container",
        "2": "databases",
        "3": "characters",
        "4": "maps",
        "5": "install",
        "6": "realm",
        "7": "volume",
    }
    choice = ask("> ")
    scope = scopes.get(choice)
    if not scope:
        return
    if scope == "volume":
        print("This deletes every account and character on every realm.")
        typed = confirm("wow_wow-mariadb")
        if typed:
            run(["erase", "volume", "--confirm", typed])
        return
    short = ask("Realm short: ")
    if not short:
        return
    typed = confirm(short)
    if typed:
        run(["erase", scope, short, "--confirm", typed])
    pause()


def backups() -> None:
    print(
        "\nBackups\n"
        "  1) Set the backup directory\n"
        "  2) Dump now\n"
        "  3) List dumps and disk use\n"
        "  4) Delete one dump\n"
        "  5) Restore one dump\n"
        "  6) Schedule a daily dump\n"
        "  7) Turn the schedule off\n"
        "  0) Back"
    )
    choice = ask("> ")
    if choice == "1":
        path = ask("Directory (another disk is safer): ")
        if path:
            run(["backup", "path", path])
    elif choice == "2":
        short = ask("Realm short, or Enter for every realm: ")
        run(["backup", "now", short] if short else ["backup", "now"])
    elif choice == "3":
        run(["backup", "list"])
    elif choice == "4":
        short = ask("Realm short: ")
        stamp = ask("Stamp: ")
        if short and stamp and confirm(stamp):
            run(["backup", "delete", short, stamp, "--confirm", stamp])
    elif choice == "5":
        short = ask("Realm short: ")
        stamp = ask("Stamp: ")
        if short and stamp and confirm(short):
            run(["backup", "restore", short, stamp, "--confirm", short])
    elif choice == "6":
        hour = ask("Hour 00-23 [04]: ") or "04"
        run(["backup", "schedule", "on", "--hour", hour])
    elif choice == "7":
        run(["backup", "schedule", "off"])
    pause()


def password() -> None:
    short = ask("Realm short: ")
    if not short:
        return
    first = getpass.getpass("New GM password: ")
    second = getpass.getpass("Again: ")
    if not first or first != second:
        print("The passwords did not match.")
        return
    save = ask("Save it in .env as well? [y/N]: ").lower() == "y"
    args = ["password", short]
    if save:
        args.append("--save-env")
    print()
    subprocess.run([str(SETUP), *args], input=first + "\n", text=True, check=False)
    pause()


def website() -> None:
    short = ask("Realm short: ")
    state = ask("Account creation on or off: ")
    if short and state in {"on", "off"}:
        run(["website", short, "create", state])
    pause()


def boot() -> None:
    print("  1) Start these realms after boot\n  2) Do not start realms after boot")
    choice = ask("> ")
    if choice == "1":
        shorts = ask("Realm shorts, comma-separated: ")
        if shorts:
            run(["boot", "enable", shorts])
    elif choice == "2":
        run(["boot", "disable"])
    pause()


def main() -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("The menu needs a terminal. Run ./setup.sh help", file=sys.stderr)
        return 2
    actions = {
        "1": lambda: run(["doctor"]),
        "2": lambda: run(["host"]),
        "3": access,
        "4": realms,
        "5": cores,
        "6": updates,
        "7": erase,
        "8": backups,
        "9": password,
        "10": website,
        "11": boot,
        "12": lambda: run(["clients"]),
    }
    while True:
        print(
            "\nWoW setup\n"
            "  1) Doctor\n"
            "  2) Install packages and host setup\n"
            "  3) How players connect\n"
            "  4) Realms\n"
            "  5) Core and modules\n"
            "  6) Updates\n"
            "  7) Databases and erase\n"
            "  8) Backups\n"
            "  9) GM password\n"
            "  10) Website account creation\n"
            "  11) Start on boot\n"
            "  12) Client folders\n"
            "  0) Exit"
        )
        choice = ask("> ")
        if choice in {"", "0", "q"}:
            return 0
        action = actions.get(choice)
        if action is None:
            print("Unknown choice.")
            continue
        action()


if __name__ == "__main__":
    sys.exit(main())
