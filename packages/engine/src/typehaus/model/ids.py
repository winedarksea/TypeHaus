"""Stable identity scheme: immutable uid + mutable tag + derived IFC GlobalId (→ 10)."""

from __future__ import annotations

import secrets
import uuid

# Crockford base32 alphabet (excludes I, L, O, U to avoid ambiguity).
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_UID_LEN = 10


def new_uid() -> str:
    """A fresh 10-char Crockford-base32 uid. Minted once, retained in source forever."""
    return "".join(secrets.choice(_CROCKFORD) for _ in range(_UID_LEN))


def derive_guid(project_uuid: uuid.UUID, uid: str) -> str:
    """IFC GlobalId derived from (project_uuid, uid) — never from position/path.

    Retagging or moving an element between storeys preserves its GlobalId (#16).
    """
    from ifcopenshell.guid import compress  # local import: heavy dep, emit path only

    return str(compress(uuid.uuid5(project_uuid, uid).hex))


def derive_child_guid(project_uuid: uuid.UUID, parent_uid: str, child_key: str) -> str:
    """GUID for a generated child member (stud, joist): stable under its parent."""
    from ifcopenshell.guid import compress

    return str(compress(uuid.uuid5(project_uuid, f"{parent_uid}/{child_key}").hex))
