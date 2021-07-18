import apps


class FramerateDMF(apps.DescriptiveMetricFormat):

    def __init__(self, unit: str, value, traits:list=[]):
        """Prefab for framerate"""
        super().__init__(name="framerate", unit=unit, value=value, traits=traits)


class RebufferTimeDMF(apps.DescriptiveMetricFormat):

    def __init__(self, unit: str, value, traits:list=[]):
        """Prefab for framerate"""
        super().__init__(name="rebuffer", unit=unit, value=value, traits=traits)
