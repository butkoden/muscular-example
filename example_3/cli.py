from __future__ import annotations

import sys
from typing import Any, cast

from muscles import ApplicationMeta, Context
from muscles.cli.cli import CliStrategy, cli


class CliApp(metaclass=ApplicationMeta):
    # RU: CLI тоже использует Context, только со стратегией CliStrategy.
    # EN: CLI uses Context too, but with the CliStrategy.
    context = Context(cast(Any, CliStrategy))

    def run(self, *args):
        # RU: expand_slash_args дает два равнозначных стиля: "a b" и "a/b".
        # EN: expand_slash_args supports two equivalent styles: "a b" and "a/b".
        return self.context.execute(*expand_slash_args(args), shutup=False)


def expand_slash_args(args):
    # RU: Разбиваем только первый аргумент, чтобы значения вроде "secret/value"
    # оставались обычными значениями, а не путями команд.
    # EN: Split only the first argument, so values like "secret/value" stay
    # normal values and do not become command paths.
    if not args:
        return tuple()
    first, *rest = args
    if "/" in first and not first.startswith("-"):
        return tuple(part for part in first.split("/") if part) + tuple(rest)
    return tuple(args)


@cli.group(command_name="example-3", description="Level 3 CLI examples")
def example_3_group(*args):
    # RU: Группа может вернуть True и затем передать управление дочерней команде.
    # EN: A group may return True and then dispatch to a child command.
    return True


@example_3_group.command(command_name="hello", description="Print a greeting")
def hello_command(*args):
    # RU: Позиционные аргументы приходят как *args.
    # EN: Positional CLI arguments arrive as *args.
    name = args[0] if args else "Student"
    print(f"Hello, {name}")
    return True


@example_3_group.group(command_name="tasks", description="Nested task commands")
def tasks_group(*args):
    return True


@tasks_group.command(command_name="list", description="List demo tasks")
def list_tasks_command(*args):
    print("1. Read example_1")
    print("2. Run example_2 API")
    print("3. Try example_4 full app")
    return True


def main():
    app = CliApp()
    return app.run(*sys.argv[1:])


if __name__ == "__main__":
    main()
