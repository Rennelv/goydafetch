from __future__ import annotations

from typing import Iterable

from .color_util import RGB
from .constants import GLOBAL_CFG
from .types import LightDark, ColorSpacing


def remove_duplicates(seq: Iterable) -> list:
    """
    Remove duplicate items from a sequence while preserving the order
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


class ColorProfile:
    raw: list[str]
    colors: list[RGB]
    spacing: ColorSpacing = 'equal'

    def __init__(self, colors: list[str] | list[RGB]):
        if isinstance(colors[0], str):
            self.raw = colors
            self.colors = [RGB.from_hex(c) for c in colors]
        else:
            self.colors = colors

    def with_weights(self, weights: list[int]) -> list[RGB]:
        """
        Map colors based on weights

        :param weights: Weights of each color (weights[i] = how many times color[i] appears)
        :return:
        """
        return [c for i, w in enumerate(weights) for c in [self.colors[i]] * w]

    def with_length(self, length: int) -> list[RGB]:
        """
        Spread to a specific length of text

        :param length: Length of text
        :return: List of RGBs of the length
        """
        preset_len = len(self.colors)
        center_i = preset_len // 2

        # How many copies of each color should be displayed at least?
        repeats = length // preset_len
        weights = [repeats] * preset_len

        # How many extra space left?
        extras = length % preset_len

        # If there is an even space left, extend the center by one space
        if extras % 2 == 1:
            extras -= 1
            weights[center_i] += 1

        # Add weight to border until there's no space left (extras must be even at this point)
        border_i = 0
        while extras > 0:
            extras -= 2
            weights[border_i] += 1
            weights[-(border_i + 1)] += 1
            border_i += 1

        return self.with_weights(weights)

    def color_text(self, txt: str, foreground: bool = True, space_only: bool = False) -> str:
        """
        Color a text

        :param txt: Text
        :param foreground: Whether the foreground text show the color or the background block
        :param space_only: Whether to only color spaces
        :return: Colored text
        """
        colors = self.with_length(len(txt))
        result = ''
        for i, t in enumerate(txt):
            if space_only and t != ' ':
                if i > 0 and txt[i - 1] == ' ':
                    result += '\033[39;49m'
                result += t
            else:
                result += colors[i].to_ansi(foreground=foreground) + t

        result += '\033[39;49m'
        return result

    def lighten(self, multiplier: float) -> ColorProfile:
        """
        Lighten the color profile by a multiplier

        :param multiplier: Multiplier
        :return: Lightened color profile (original isn't modified)
        """
        return ColorProfile([c.lighten(multiplier) for c in self.colors])

    def set_light_raw(self, light: float, at_least: bool | None = None, at_most: bool | None = None) -> 'ColorProfile':
        """
        Set HSL lightness value

        :param light: Lightness value (0-1)
        :param at_least: Set the lightness to at least this value (no change if greater)
        :param at_most: Set the lightness to at most this value (no change if lesser)
        :return: New color profile (original isn't modified)
        """
        return ColorProfile([c.set_light(light, at_least, at_most) for c in self.colors])

    def set_light_dl(self, light: float, term: LightDark | None = None):
        """
        Set HSL lightness value with respect to dark/light terminals

        :param light: Lightness value (0-1)
        :param term: Terminal color (can be "dark" or "light")
        :return: New color profile (original isn't modified)
        """
        if GLOBAL_CFG.use_overlay:
            return self.overlay_dl(light, term)

        term = term or GLOBAL_CFG.light_dark()
        assert term.lower() in ['light', 'dark']
        at_least, at_most = (True, None) if term.lower() == 'dark' else (None, True)
        return self.set_light_raw(light, at_least, at_most)

    def overlay_raw(self, color: RGB, alpha: float) -> 'ColorProfile':
        """
        Overlay a color on top of the color profile

        :param color: Color to overlay
        :param alpha: Alpha value (0-1)
        :return: New color profile (original isn't modified)
        """
        return ColorProfile([c.overlay(color, alpha) for c in self.colors])

    def overlay_dl(self, light: float, term: LightDark | None = None):
        """
        Same as set_light_dl except that this function uses RGB overlaying instead of HSL lightness change
        """
        term = term or GLOBAL_CFG.light_dark()
        assert term.lower() in ['light', 'dark']

        # If it's light bg, overlay black, else overlay white
        overlay_color = RGB.from_hex('#000000' if term.lower() == 'light' else '#FFFFFF')
        return self.overlay_raw(overlay_color, abs(light - 0.5) * 2)

    def set_light_dl_def(self, term: LightDark | None = None):
        """
        Set default lightness with respect to dark/light terminals

        :param term: Terminal color (can be "dark" or "light")
        :return: New color profile (original isn't modified)
        """
        return self.set_light_dl(GLOBAL_CFG.default_lightness(term), term)

    def unique_colors(self) -> ColorProfile:
        """
        Create another color profile with only the unique colors
        """
        return ColorProfile(remove_duplicates(self.colors))


PRESETS: dict[str, ColorProfile] = {
    'rainbow': ColorProfile([
        '#FFFFFF',
        '#0000FF',
        '#FF0000'
    ]),
    'goyda': ColorProfile([
        '#FFFFFF',
        '#0000FF',
        '#FF0000'
    ]),
}
