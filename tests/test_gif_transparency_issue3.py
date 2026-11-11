# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Regression test for issue #3: resizing a palette GIF with a transparent
# palette entry must keep those pixels transparent when the Pillow engine
# re-quantizes the image (PILLOW_PRESERVE_INDEXED_MODE enabled).

import os
from io import BytesIO
from unittest import TestCase

from PIL import Image

from thumbor.config import Config
from thumbor.context import Context
from thumbor.engines.pil import Engine

STICKER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "course",
    "images",
    "sticker.gif",
)


class GifTransparencyIssue3TestCase(TestCase):
    def setUp(self):
        self.config = Config(PILLOW_PRESERVE_INDEXED_MODE=True)
        self.context = Context(config=self.config)
        with open(STICKER, "rb") as handle:
            self.buffer = handle.read()

    def resize_gif(self, width, height):
        engine = Engine(self.context)
        engine.load(self.buffer, ".gif")
        engine.resize(width, height)
        return engine.read(".gif")

    def test_resized_palette_gif_keeps_transparent_background(self):
        result = self.resize_gif(240, 160)
        image = Image.open(BytesIO(result))
        rgba = image.convert("RGBA")

        self.assertIn(
            "transparency",
            image.info,
            "resized GIF lost its transparency index",
        )
        # Corner pixel is background in the source sticker.
        self.assertEqual(rgba.getpixel((0, 0))[3], 0)

    def test_opaque_palette_gif_stays_opaque(self):
        # Issue #3: a GIF with no transparency must stay opaque.
        image = Image.new("P", (40, 40), 0)
        image.putpalette([0, 0, 0, 255, 0, 0] + [0, 0, 0] * 254)
        buffer = BytesIO()
        image.save(buffer, "GIF")

        engine = Engine(self.context)
        engine.load(buffer.getvalue(), ".gif")
        engine.resize(20, 20)
        result = Image.open(BytesIO(engine.read(".gif")))

        self.assertNotIn("transparency", result.info)
