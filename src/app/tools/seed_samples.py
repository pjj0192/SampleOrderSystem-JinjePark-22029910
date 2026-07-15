import argparse
import random
import sys

from app.repositories.sample_repository import JsonSampleRepository
from app.tools.dummy_data_generator import generate_and_store


def _force_utf8_stdout() -> None:
    """Windows terminals often default to a legacy codepage (e.g. cp949),
    which mangles the Korean text this tool prints. reconfigure() raises
    on streams that don't support it (e.g. some redirected/piped setups),
    so guard defensively."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed dummy Sample data into the console app's JSON repository "
        "(manual-testing convenience; not part of the graded feature set)."
    )
    parser.add_argument("--count", type=int, default=10, help="number of samples to generate")
    parser.add_argument(
        "--file", type=str, default="data/samples.json", help="target JSON repository file"
    )
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    _force_utf8_stdout()
    args = parse_args(argv)
    repository = JsonSampleRepository(args.file)
    rng = random.Random(args.seed)
    created = generate_and_store(repository, count=args.count, rng=rng)
    print(f"{len(created)}개의 더미 시료를 '{args.file}'에 저장했습니다.")


if __name__ == "__main__":
    main()
