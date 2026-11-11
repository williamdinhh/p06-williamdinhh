# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from tornado.testing import gen_test

from tests.base import FilterTestCase

CORNER = 60
TOLERANCE = 60


class RoundCornerTransparentFringeTestCase(FilterTestCase):
    @gen_test
    async def test_transparent_arc_uses_partial_alpha_and_keeps_color(self):
        image = await self.get_filtered(
            "source.jpg",
            "thumbor.filters.round_corner",
            "round_corner(60,255,255,255,1):format(png)",
            mode="RGBA",
        )
        rgba = image.convert("RGBA")
        px = rgba.load()
        width, _ = rgba.size

        partial = []
        for y in range(CORNER):
            for x in range(CORNER):
                r, g, b, a = px[x, y]
                if 0 < a < 255:
                    partial.append((x, y, r, g, b))

        assert partial, (
            "Expected partial-alpha pixels on the rounded corner arc, "
            "found none (the edge is opaque, which means a dark ring)"
        )

        for x, y, r, g, b in partial:
            interior_x = next(
                xx for xx in range(CORNER, width) if px[xx, y][3] == 255
            )
            ir, ig, ib, _ = px[interior_x, y]
            diff = max(abs(r - ir), abs(g - ig), abs(b - ib))
            assert diff < TOLERANCE, (
                f"Edge pixel at ({x},{y}) has color ({r},{g},{b}), "
                f"expected close to interior ({ir},{ig},{ib}); "
                "colors were darkened"
            )
