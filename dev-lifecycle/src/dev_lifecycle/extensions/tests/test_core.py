"""Tests for the umbrella CLI entry point (routing + not-implemented handlers)."""

import unittest

from dev_lifecycle import core


class TestCore(unittest.TestCase):

    def test_route_accepts_valid_and_rejects_invalid_providers(self):
        self.assertTrue(core.route("task", "github"))
        self.assertTrue(core.route("pr-feedback", "codex"))
        self.assertFalse(core.route("task", "codex"))
        self.assertFalse(core.route("pr-feedback", "github"))
        self.assertFalse(core.route("task", None))
        self.assertFalse(core.route("bogus", "github"))

    def test_handlers_raise_instead_of_faking_progress(self):
        for handler, arg in [(core.handle_task, "github"),
                             (core.handle_pr_feedback, "human"),
                             (core.handle_post_merge, "jira")]:
            with self.assertRaises(NotImplementedError):
                handler(arg)

    def test_main_exit_codes(self):
        self.assertEqual(core.main(["task", "github"]), 2)   # valid route, handler not implemented
        self.assertEqual(core.main(["task", "codex"]), 2)    # invalid provider
        self.assertEqual(core.main(["task"]), 2)             # missing provider


if __name__ == "__main__":
    unittest.main()
