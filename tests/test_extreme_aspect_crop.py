# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

# Regression tests for issue #4 (extreme-aspect-crop): zero-sized crops
# and fit-in dimension rounding.

import asyncio
import io
from os.path import abspath, dirname, join

from PIL import Image

from thumbor.config import Config
from thumbor.context import Context, RequestParameters, ServerParameters
from thumbor.importer import Importer
from thumbor.transformer import Transformer

FIXTURES = abspath(join(dirname(__file__), "fixtures/images/"))


def _rainbow_png(width=16, height=16):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    colors = [
        (255, 0, 0, 255),
        (255, 165, 0, 255),
        (255, 255, 0, 255),
        (0, 128, 0, 255),
        (0, 0, 255, 255),
        (75, 0, 130, 255),
        (238, 130, 238, 255),
        (255, 255, 255, 255),
    ]
    band = width // len(colors)
    for x in range(width):
        color = colors[min(x // band, len(colors) - 1)]
        for y in range(height):
            img.putpixel((x, y), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _file_bytes(name):
    with open(join(FIXTURES, name), "rb") as handle:
        return handle.read()


def _transform(buffer, ext, **request_args):
    cfg = Config(SECURITY_KEY="ACME-SEC")
    cfg.LOADER = "thumbor.loaders.file_loader"
    cfg.FILE_LOADER_ROOT_PATH = FIXTURES
    cfg.STORAGE = "thumbor.storages.no_storage"
    importer = Importer(cfg)
    importer.import_modules()
    server = ServerParameters(
        8889, "localhost", "thumbor.conf", None, "info", None
    )
    server.security_key = "ACME-SEC"
    context = Context(server, cfg, importer)
    engine = context.modules.engine
    engine.load(buffer, ext)
    context.request = RequestParameters(**request_args)
    context.request.engine = engine
    asyncio.run(Transformer(context).transform())
    return engine


class TestExtremeAspectCrop:
    def test_square_transparent_png_at_800x20_is_visible(self):
        engine = _transform(
            _rainbow_png(), ".png", width=800, height=20
        )
        assert engine.size == (800, 20)
        # The output must contain visible pixels, not an all-transparent image.
        alpha_max = engine.image.getchannel("A").getextrema()[1]
        assert alpha_max > 0

    def test_fit_in_1x1_of_940x2_is_1x1(self):
        engine = _transform(
            _file_bytes("940x2.png"),
            ".png",
            width=1,
            height=1,
            fit_in=True,
        )
        assert engine.size == (1, 1)

    def test_fit_in_width_only_100x0_of_940x2_is_100x1(self):
        engine = _transform(
            _file_bytes("940x2.png"),
            ".png",
            width=100,
            height=0,
            fit_in=True,
        )
        assert engine.size == (100, 1)
