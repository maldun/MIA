    @mark.req("IF-102", "REQ-DB-004")
    @each_provider(IF)
    def test_values_no_backend_can_keep_alike_are_refused(self, store):
        """TC-IF-102-11 (A-65, D-168): a NUL character, a number that is not finite and an id that is not text are refused with invalid/schema.
        Example: put("memos", "m", {"text": "a\\x00b"}, "anna") -> StorageError("invalid", rule="schema"); ids("memos") stays []."""
        # Given: a NUL in a text, NaN, inf, and ids that are not text
        calls = [lambda: store.put("memos", "m", {"text": "a\x00b"}, "anna"), lambda: store.put("memos", "m", {"text": "a", "n": float("nan")}, "anna"),
                 lambda: store.put("memos", "m", {"text": "a", "n": [float("inf")]}, "anna"), lambda: store.put("memos", 7, {"text": "a"}, "anna"),
                 lambda: store.put("memos", None, {"text": "a"}, "anna")]
        # When / Then: each is refused with the rule schema, and nothing is stored
        for call in calls:
            with self.assertRaises(StorageError) as caught:
                call()
            self.assertEqual((caught.exception.code, caught.exception.rule), ("invalid", "schema"))
        self.assertEqual(store.ids("memos"), [])

