"""Command-line interface for StreetRace Manager."""

import argparse

from streetrace_manager.system import StreetRaceSystem


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for simple demo operations."""
    parser = argparse.ArgumentParser(description="StreetRace Manager CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    reg = sub.add_parser("register", help="Register a new crew member")
    reg.add_argument("name")
    reg.add_argument("--role", default="unassigned")

    add_car = sub.add_parser("add-car", help="Add a car to inventory")
    add_car.add_argument("car_id")
    add_car.add_argument("model")

    cash = sub.add_parser("add-cash", help="Add cash to inventory")
    cash.add_argument("amount", type=int)

    list_members = sub.add_parser("list-members", help="List registered crew")

    return parser


def main() -> None:
    """Run CLI command handlers."""
    parser = build_parser()
    args = parser.parse_args()
    system = StreetRaceSystem()

    if args.cmd == "register":
        member = system.registration.register_member(args.name, args.role)
        print(f"Registered {member.name} as {member.role}.")
    elif args.cmd == "add-car":
        car = system.inventory.add_car(args.car_id, args.model)
        print(f"Added car {car.car_id} ({car.model}).")
    elif args.cmd == "add-cash":
        system.inventory.add_cash(args.amount)
        print(f"Cash balance is now {system.inventory.cash_balance()}.")
    elif args.cmd == "list-members":
        for member in system.registration.list_members():
            print(f"{member.name} ({member.role})")


if __name__ == "__main__":
    main()
