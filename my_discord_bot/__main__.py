from .bot import MyBot
from .db import db
from .settings import TOKEN


def main() -> None:
    db.setup()
    MyBot().run(TOKEN)


if __name__ == "__main__":
    main()
