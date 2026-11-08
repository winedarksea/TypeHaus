"""An endpoint derivation that failed, as data: cause, the element it names, the fix.

The finders still take a ``problems`` list and still leave a rendered line in it, so any
caller that passes a plain list keeps working. A :class:`MissLog` also keeps the structure,
which is what ``route_propose`` builds its ``EndpointRefusal`` from (no sentence parsing)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Miss:
    """Why ``target``'s terminals are not derivable. ``element`` is the missing or
    offending thing (the riser, the pump); empty means the target itself."""

    target: str
    cause: str
    element: str = ""
    fix: str = ""

    def render(self) -> str:
        return f"{self.target}: {self.cause}" + (f". {self.fix}" if self.fix else "")


class MissLog(list):
    """A ``problems`` list that also records each :func:`miss` as a :class:`Miss`."""

    def __init__(self, *args: str) -> None:
        super().__init__(*args)
        self.misses: list[Miss] = []

    @property
    def first(self) -> Miss | None:
        return self.misses[0] if self.misses else None


def log(problems: list[str], record: Miss) -> None:
    """Append the rendered line to ``problems``; a :class:`MissLog` keeps the record too."""
    problems.append(record.render())
    if isinstance(problems, MissLog):
        problems.misses.append(record)


def miss(problems: list[str], target: str, cause: str, element: str = "",
         fix: str = "") -> None:
    log(problems, Miss(target, cause, element, fix))
