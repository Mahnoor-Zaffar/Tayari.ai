"""Password management using bcrypt (Argon2-ready architecture).

Why Argon2 is preferred (and why we use bcrypt here)
──────────────────────────────────────────────────────

**Argon2** (specifically Argon2id) is the OWASP-recommended password hashing
algorithm and the winner of the PHC (Password Hashing Competition).  It
provides three tunable axes — **time cost**, **memory cost**, and **parallelism**
— that make it resistant against:

  * **GPU attacks** — high memory cost (64 MB+) prevents batch-cracking on GPU.
  * **ASIC/FPGA attacks** — the memory-hard property forces custom hardware
    to dedicate die area to memory rather than compute.
  * **Side-channel attacks** — Argon2id's hybrid approach uses data-independent
    memory access in the first pass, mitigating timing and cache-timing leaks.

**bcrypt** (used here) shares many of these properties: it is also adaptive
(via the log2 round count) and salt-included.  However it has only **one**
tunable parameter (rounds) and its memory footprint is fixed at ~4 KB, making
it strictly weaker than Argon2 against GPU farms.  The architecture is
identical — swap ``PasswordHasher`` for ``argon2.PasswordHasher`` when
``argon2-cffi`` is available, and no other code changes.
"""

import bcrypt


class PasswordService:
    """Hash, verify, and detect stale password hashes.

    Method names match the requirement: ``hash_password``, ``verify_password``,
    ``needs_rehash``.  The hash format is never exposed to callers.
    """

    def __init__(self, rounds: int = 12) -> None:
        """*rounds* is the log2 work factor (default 12 → 2¹² iterations).

        Increase this value as hardware improves.  Existing hashes with
        lower rounds will be detected by ``needs_rehash``.
        """
        self._rounds = rounds

    def hash_password(self, password: str) -> str:
        """Return a bcrypt hash string suitable for storage.

        The salt is generated internally by bcrypt — the caller never sees it.
        """
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=self._rounds),
        ).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Return ``True`` if *password* matches *password_hash*.

        Uses constant-time comparison (bcrypt guarantees this internally).
        Returns ``False`` (never raises) on any error to avoid oracle attacks.
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """Return ``True`` if *password_hash* uses a different work factor.

        Call this after ``verify_password`` succeeds.  If it returns ``True``,
        hash the password again with ``hash_password`` and store the new hash.
        This allows gradual work-factor upgrades without forcing password resets.
        """
        try:
            parts = password_hash.split("$")
            # Expected format: "$<prefix>$<rounds>$<salt+hash>"
            # e.g. "$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ12"
            prefix = parts[1]
            rounds = int(parts[2])
            if prefix not in ("2a", "2b", "2y"):
                return True
            return rounds != self._rounds
        except (IndexError, ValueError):
            return True
