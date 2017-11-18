"""
These are the user-preferences. For the network and system preferences, take a
look at `Settings.py`. Use it like this example:

    from neo.UserPreferences import preferences
    print(preferences.token_style)
    preferences.set_theme("light")

"""
import json
import os
import sys

from json.decoder import JSONDecodeError
from logzero import logger
from neo.Settings import FILENAME_PREFERENCES

PREFERENCES_DEFAULT = {
    "theme": "dark",
    "themes": {
        "dark": {
            "Command": "#ff0066",
            "Default": "#00ee00",
            "Neo": "#0000ee",
            "Number": "#ffffff"
        },
        "light": {
            "Command": "#ff0066",
            "Default": "#008800",
            "Neo": "#0000ee",
            "Number": "#000000"
        }
    }
}


class UserPreferencesHolder:
    # Merged default preferences with user-specific overrides
    _prefs = {}

    # Only the user-specific preferences
    _userprefs = {}

    # Remember the potentially custom filename
    _preferences_filename = None

    def __init__(self, preferences_filename=FILENAME_PREFERENCES):
        self._preferences_filename = preferences_filename
        self._prefs = PREFERENCES_DEFAULT

        try:
            with open(self._preferences_filename) as data_file:
                self._userprefs = json.load(data_file)
                self._prefs.update(self._userprefs)

        except FileNotFoundError as e:
            # No user-specific overrides, which is ok
            pass

        except JSONDecodeError as e:
            logger.error("JSONDecodeError: {} in {}".format(e.msg, self._preferences_filename))
            raise

    def _save_userprefs(self):
        with open(self._preferences_filename, "w") as data_file:
            data_file.write(json.dumps(self._userprefs, indent=4, sort_keys=True))

    def set_theme(self, theme_name):
        if theme_name not in self._prefs["themes"].keys():
            raise ValueError("Error: cannot set theme_name '%s', no theme with this name" % theme_name)

        self._userprefs["theme"] = theme_name
        self._prefs.update(self._userprefs)
        self._save_userprefs()

    @property
    def token_style(self):
        return self._prefs["themes"][self._prefs["theme"]]


preferences = UserPreferencesHolder()
