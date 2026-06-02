import sys

from muscles import ApplicationMeta, Context
from muscles.cli.cli import CliStrategy, cli

from .db import diagnostics, init_db, list_bookings, remove_booking, set_admin_password


class CliApp(metaclass=ApplicationMeta):
    context = Context(CliStrategy, transport="cli")

    def run(self, *args):
        return self.context.execute(*expand_slash_args(args), shutup=False)


def expand_slash_args(args):
    # Supports both "bookings remove 1" and "bookings/remove 1".
    if not args:
        return tuple()
    first, *rest = args
    if "/" in first and not first.startswith("-"):
        return tuple(part for part in first.split("/") if part) + tuple(rest)
    return tuple(args)


@cli.command(command_name="init-db", description="Initialize SQLite database")
def init_db_command(*args):
    init_db()
    print("Database initialized")
    return True


@cli.group(command_name="bookings", description="Manage slot bookings")
def bookings_group(*args):
    if args:
        return True
    return list_bookings_command()


@bookings_group.command(command_name="list", description="List latest bookings")
def list_bookings_command(*args):
    for booking in list_bookings():
        print("#{id} {starts_at} {name} <{email}> {title} [{status}]".format(**booking))
    return True


@bookings_group.command(command_name="remove", description="Remove booking by id")
def remove_booking_command(*args):
    if len(args) != 1:
        raise ValueError("Usage: bookings remove <id>")
    booking = remove_booking(int(args[0]))
    if booking is None:
        raise ValueError("Booking #%s not found" % args[0])
    print("Removed booking #{id}: {starts_at} {name} <{email}> {title}".format(**booking))
    return True


@cli.command(command_name="diagnostics", description="Print site diagnostics")
def diagnostics_command(*args):
    for key, value in diagnostics().items():
        print(f"{key}: {value}")
    return True


@cli.command(command_name="set-password", description="Change admin password")
@cli.argument("--password", short="-p", required=True, prompt="New password")
def set_password_command(*args, password):
    set_admin_password(password)
    print("Admin password changed")
    return True


def main():
    app = CliApp()
    return app.run(*sys.argv[1:])


if __name__ == "__main__":
    main()
