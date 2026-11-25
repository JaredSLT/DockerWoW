"""Account creation reads a per-realm flag and does not insert when it is off."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wowweb import accounts
from wowweb.catalog import resolve
from wowweb.lab import LabConfig


class AccountCreateFlagTests(unittest.TestCase):
    def test_off_does_not_insert_and_on_reaches_insert(self):
        exp = resolve("vanilla")
        cfg = LabConfig(root=Path("/tmp"))
        old = os.environ.get("WOW_ACCOUNT_CREATE_FILE")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                flag = Path(tmp) / "account-create"
                flag.write_text("off\n", encoding="utf-8")
                os.environ["WOW_ACCOUNT_CREATE_FILE"] = str(flag)
                with patch.object(accounts, "_create_username", side_effect=AssertionError("inserted")):
                    ok, msg, _name = accounts.create_account(cfg, exp, "Aldrea", "secret12", "", "")
                self.assertFalse(ok)
                self.assertEqual(msg, accounts.CLOSED_ACCOUNT)

                flag.write_text("on\n", encoding="utf-8")
                with patch.object(
                    accounts, "_create_username", return_value=(True, "created", "ALDREA")
                ) as spy:
                    ok, msg, name = accounts.create_account(cfg, exp, "Aldrea", "secret12", "", "")
                self.assertTrue(ok)
                self.assertEqual(msg, "created")
                self.assertEqual(name, "ALDREA")
                spy.assert_called_once()
        finally:
            if old is None:
                os.environ.pop("WOW_ACCOUNT_CREATE_FILE", None)
            else:
                os.environ["WOW_ACCOUNT_CREATE_FILE"] = old


if __name__ == "__main__":
    unittest.main()
