"""Seed data for coding problems.

Single source of truth used by the ``0011`` migration (Postgres) and by
application/tests seeding. Each test case follows the judging contract:

- ``input``: raw text written to the program's stdin
- ``expected_output``: the exact text the program must print to stdout
  (trailing whitespace is ignored, numeric outputs allow float tolerance)
- ``is_hidden``: hidden tests never have their input/output returned to the client

Starter templates are intentionally NOT stored per problem — the shared per-language
templates pass the whole stdin string to ``solve(data)`` so any problem works.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.code.models import Problem


def _pid(seed: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"tayari/problems/{seed}")


TWO_SUM = {
    "id": _pid("two-sum"),
    "slug": "two-sum",
    "title": "Two Sum",
    "difficulty": "medium",
    "description": (
        "Given an array of integers nums and an integer target, return the indices of the two "
        "numbers that add up to target. You may assume each input has exactly one solution, "
        "and you may not use the same element twice. Return the indices separated by a single "
        "space, in the order they appear in the input.\n\n"
        "Input format: the first line contains the integer n (the length of nums), the second "
        "line contains n space-separated integers, and the third line contains the target."
    ),
    "examples": [
        {
            "input": "4\n2 7 11 15\n9",
            "output": "0 1",
            "explanation": "Because nums[0] + nums[1] == 9, we return 0 1.",
        },
        {
            "input": "3\n3 2 4\n6",
            "output": "1 2",
            "explanation": "Because nums[1] + nums[2] == 6, we return 1 2.",
        },
    ],
    "constraints": [
        "2 <= nums.length <= 10^4",
        "-10^9 <= nums[i] <= 10^9",
        "-10^9 <= target <= 10^9",
        "Exactly one valid answer exists.",
    ],
    "test_cases": [
        {"id": "two-sum-1", "input": "4\n2 7 11 15\n9", "expected_output": "0 1", "is_hidden": False},
        {"id": "two-sum-2", "input": "3\n3 2 4\n6", "expected_output": "1 2", "is_hidden": False},
        {"id": "two-sum-3", "input": "2\n3 3\n6", "expected_output": "0 1", "is_hidden": True},
        {"id": "two-sum-4", "input": "4\n1 2 3 4\n7", "expected_output": "2 3", "is_hidden": True},
        {"id": "two-sum-5", "input": "5\n-1 -2 -3 -4 -5\n-8", "expected_output": "2 4", "is_hidden": True},
        {"id": "two-sum-6", "input": "6\n1 2 3 4 5 6\n11", "expected_output": "4 5", "is_hidden": True},
        {
            "id": "two-sum-7",
            "input": "2\n1000000000 1000000000\n2000000000",
            "expected_output": "0 1",
            "is_hidden": True,
        },
    ],
}

REVERSE_STRING = {
    "id": _pid("reverse-string"),
    "slug": "reverse-string",
    "title": "Reverse String",
    "difficulty": "easy",
    "description": (
        "Given a string s, return the string reversed. The input is a single line of text "
        "(spaces are allowed). Print the reversed characters."
    ),
    "examples": [
        {"input": "hello", "output": "olleh", "explanation": "Reversing 'hello' yields 'olleh'."},
        {"input": "OpenAI", "output": "IAnepO", "explanation": "Reversing 'OpenAI' yields 'IAnepO'."},
    ],
    "constraints": [
        "0 <= s.length <= 10^4",
        "s consists of printable ASCII characters.",
    ],
    "test_cases": [
        {"id": "reverse-1", "input": "hello", "expected_output": "olleh", "is_hidden": False},
        {"id": "reverse-2", "input": "OpenAI", "expected_output": "IAnepO", "is_hidden": False},
        {"id": "reverse-3", "input": "", "expected_output": "", "is_hidden": True},
        {"id": "reverse-4", "input": "racecar", "expected_output": "racecar", "is_hidden": True},
        {"id": "reverse-5", "input": "A man", "expected_output": "nam A", "is_hidden": True},
        {"id": "reverse-6", "input": "12345", "expected_output": "54321", "is_hidden": True},
    ],
}

FIZZ_BUZZ = {
    "id": _pid("fizz-buzz"),
    "slug": "fizz-buzz",
    "title": "Fizz Buzz",
    "difficulty": "easy",
    "description": (
        "Given an integer n, print the numbers from 1 to n (space-separated, single line). "
        "For multiples of three print 'Fizz' instead of the number, for multiples of five "
        "print 'Buzz', and for multiples of both three and five print 'FizzBuzz'."
    ),
    "examples": [
        {
            "input": "15",
            "output": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz",
            "explanation": "The classic FizzBuzz sequence up to 15.",
        },
    ],
    "constraints": [
        "1 <= n <= 100",
    ],
    "test_cases": [
        {
            "id": "fizz-1",
            "input": "15",
            "expected_output": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz",
            "is_hidden": False,
        },
        {"id": "fizz-2", "input": "5", "expected_output": "1 2 Fizz 4 Buzz", "is_hidden": False},
        {"id": "fizz-3", "input": "1", "expected_output": "1", "is_hidden": True},
        {"id": "fizz-4", "input": "3", "expected_output": "1 2 Fizz", "is_hidden": True},
        {
            "id": "fizz-5",
            "input": "30",
            "expected_output": (
                "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz "
                "16 17 Fizz 19 Buzz Fizz 22 23 Fizz Buzz 26 Fizz 28 29 FizzBuzz"
            ),
            "is_hidden": True,
        },
        {
            "id": "fizz-6",
            "input": "100",
            "expected_output": (
                "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz "
                "16 17 Fizz 19 Buzz Fizz 22 23 Fizz Buzz 26 Fizz 28 29 FizzBuzz "
                "31 32 Fizz 34 Buzz Fizz 37 38 Fizz Buzz 41 Fizz 43 44 FizzBuzz "
                "46 47 Fizz 49 Buzz Fizz 52 53 Fizz Buzz 56 Fizz 58 59 FizzBuzz "
                "61 62 Fizz 64 Buzz Fizz 67 68 Fizz Buzz 71 Fizz 73 74 FizzBuzz "
                "76 77 Fizz 79 Buzz Fizz 82 83 Fizz Buzz 86 Fizz 88 89 FizzBuzz "
                "91 92 Fizz 94 Buzz Fizz 97 98 Fizz Buzz"
            ),
            "is_hidden": True,
        },
    ],
}

SEED_PROBLEMS: list[dict] = [TWO_SUM, REVERSE_STRING, FIZZ_BUZZ]


async def seed_problems(session: AsyncSession) -> None:
    """Upsert all seed problems into the database (idempotent)."""
    existing_ids = set((await session.execute(select(Problem.id))).scalars().all())
    for data in SEED_PROBLEMS:
        if data["id"] not in existing_ids:
            session.add(Problem(**data))
    await session.flush()
