# =====================
# General Action Format
# =====================


class GeneralActionFormat():

    def __init__(self, name:str, value):
        """Some standardization enforcement for the GAF structures"""
        self.Name = name
        self.Value = value

    def ToDict(self) -> dict:
        """"""
        return {self.Name: self.Value}


# Some Core Actions

class TCPCongestionControlGAF(GeneralActionFormat):

    def __init__(self):
        """"""
        super().__init__("-tcp-congestion-control", "cubic")