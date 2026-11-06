from dataclasses import dataclass
from typing import Callable, Optional

from mapmaker.maps import cog


@dataclass(frozen=True)
class VariantSpec:
    name: str
    singleband: bool
    colormap: Optional[str]
    build: Callable


VARIANTS = {
    "rgb": [
        VariantSpec("rgb", singleband=False, colormap=None, build=cog.build_rgb),
        VariantSpec("grayscale", singleband=True, colormap="greys_r", build=cog.build_grayscale),
    ],
    "multispectral": [
        VariantSpec("rgb", singleband=False, colormap=None, build=cog.build_rgb),
        VariantSpec("grayscale", singleband=True, colormap="greys_r", build=cog.build_grayscale),
        VariantSpec("ndvi", singleband=True, colormap="rdylgn", build=cog.build_ndvi),
    ],
    "dem": [
        VariantSpec("hillshade", singleband=True, colormap="greys_r", build=cog.build_hillshade),
        VariantSpec("color-relief", singleband=False, colormap=None, build=cog.build_color_relief),
        VariantSpec("slope", singleband=True, colormap="magma", build=cog.build_slope),
    ],
}
