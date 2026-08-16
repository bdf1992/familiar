# Registry Domain

Registry owns identity, addressability, carriers, registration, exact resolution, provenance, Spellbooks, Libraries, and Registrar relations.

Knowledge/addressability may change here without attempting an Effect. Registration is not casting.

Current material already here:

- `core.py`
- `local.py` — optional restart-safe local persistence for existing Spellbook objects
- Scroll, Spellbook, and Library schemas

`LocalRegistry` is a storage adapter, not a publication mechanism. A personal book may remain entirely local. The adapter preserves exact declaration verification on reopen and uses atomic writes plus private POSIX permissions where the host supports them. Host disk encryption and account access control remain environment responsibilities; local persistence does not claim issuer authentication or a signature trust chain.

Registrar `.Binding` belongs to this domain when it answers where and how an artifact participates in registration. Technique Binding does not; Technique Binding belongs to Cast because it describes an execution path.
