import unittest

from wowweb import forums, html as H
from wowweb.catalog import ORDER, resolve

BANNED = ("recreation", "private server", "mariadb")


def _threads(n: int) -> list[dict]:
    return [
        {
            "id": i,
            "title": f"Thread {i:02d}",
            "author": "Ada",
            "replies": i,
            "created": 1_700_000_000 + i,
            "last": 1_700_000_000 + i,
        }
        for i in range(1, n + 1)
    ]


class ForumPageTests(unittest.TestCase):
    def test_board_paginates_twenty_rows(self):
        html = H.forum_board("General Discussion", "general", _threads(25), None)
        self.assertEqual(html.count("class='thread-row'"), 20)
        self.assertIn("href='?page=2'", html)
        self.assertIn("Thread 01", html)
        self.assertIn("Thread 20", html)
        self.assertNotIn("Thread 21", html)
        page2 = H.forum_board("General Discussion", "general", _threads(25), None, 2)
        self.assertEqual(page2.count("class='thread-row'"), 5)
        self.assertIn("Thread 21", page2)
        self.assertIn("Thread 25", page2)
        self.assertNotIn("Thread 20", page2)

    def test_blizzard_author_is_a_blue_post(self):
        html = H.forum_thread(
            "general",
            {
                "id": 3,
                "title": "Notice",
                "posts": [
                    {"author": "Blizzard", "body": "Official word.", "created": 1_000},
                    {"author": "Blizzard Poster", "body": "Not a blue post.", "created": 1_001},
                    {"author": "blizzard", "body": "Wrong case.", "created": 1_002},
                    {"author": "Blizzard Entertainment", "body": "Company name.", "created": 1_003},
                ],
            },
            None,
        )
        self.assertEqual(html.count("blizzard-post"), 1)
        self.assertIn("class='post blizzard-post'", html)
        board = H.forum_board(
            "General Discussion",
            "general",
            [
                {
                    "id": 1,
                    "title": "Hello",
                    "author": "Blizzard",
                    "replies": 1,
                    "created": 50,
                    "last": 50,
                }
            ],
            None,
        )
        self.assertNotIn("blizzard-post", board)

    def test_visitor_copy_avoids_lab_language(self):
        chunks = []
        for era in ORDER:
            exp = resolve(era)
            chunks.append(H.forum_index(exp, forums.boards_for(exp)))
        chunks.append(H.forum_board("General Discussion", "general", _threads(3), "Ada"))
        chunks.append(
            H.forum_thread(
                "general",
                {
                    "id": 1,
                    "title": "Hello",
                    "posts": [{"author": "Ada", "body": "See you in the tavern.", "created": 10}],
                },
                None,
            )
        )
        blob = "\n".join(chunks).casefold()
        for phrase in BANNED:
            self.assertNotIn(phrase, blob, msg=phrase)


if __name__ == "__main__":
    unittest.main()
