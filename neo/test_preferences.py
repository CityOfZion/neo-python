import json
from tempfile import NamedTemporaryFile
from json.decoder import JSONDecodeError
from neo.Utils.NeoTestCase import NeoTestCase
from neo.UserPreferences import UserPreferencesHolder, PREFERENCES_DEFAULT


class PreferencesTestCase(NeoTestCase):
    def test_prefs_json_nonexistant(self):
        prefs = UserPreferencesHolder("/this/does/not/exist.json")
        self.assertEqual(prefs._userprefs, {})
        self.assertEqual(prefs._prefs, PREFERENCES_DEFAULT)

    def test_prefs_json_invalid(self):
        with NamedTemporaryFile() as prefs_file:
            prefs_file.write(b"xxx")
            prefs_file.flush()
            print("This test expects an error message. Don't worry about the next line ;)")
            with self.assertRaises(JSONDecodeError):
                prefs = UserPreferencesHolder(prefs_file.name)

    def test_prefs_json_empty(self):
        with NamedTemporaryFile("w") as prefs_file:
            s = json.dumps({}, indent=4, sort_keys=True)
            prefs_file.write(s)
            prefs_file.flush()
            prefs = UserPreferencesHolder(prefs_file.name)
            self.assertEqual(prefs._userprefs, {})
            self.assertEqual(prefs._prefs, PREFERENCES_DEFAULT)

            # Make sure it's possible to get the theme prefs
            self.assertEqual(prefs.token_style, PREFERENCES_DEFAULT["themes"]["dark"])

            # Cannot set an invalid theme
            with self.assertRaises(ValueError):
                prefs.set_theme("invalid")

            # Can set a valid theme
            prefs.set_theme("light")
            self.assertEqual(prefs.token_style, PREFERENCES_DEFAULT["themes"]["light"])

            # Make sure it persists user-preferences to JSON file
            prefs2 = UserPreferencesHolder(prefs_file.name)
            self.assertEqual(prefs2._userprefs, {"theme": "light"})
            self.assertEqual(prefs2.token_style, PREFERENCES_DEFAULT["themes"]["light"])
