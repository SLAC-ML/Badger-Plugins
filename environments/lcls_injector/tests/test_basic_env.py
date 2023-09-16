import pytest

from environments.lcls_injector import Environment
from interfaces.epics import Interface


class TestLCLSInjectorEnvironment:
    def test_basic(self):
        diagnostic = "OTR3"
        env = Environment(interface=Interface(testing=True), diagnostic=diagnostic)
        env.diagnostic.testing = True
        assert env.diagnostic.screen_name == "OTRS:IN20:621"

        # try to get a variable value
        result = env._get_variables(["SOLN:IN20:121:BCTRL"])
        assert "SOLN:IN20:121:BCTRL" in result

        # try to set a variable value
        env._set_variables({"QUAD:IN20:525:BCTRL": -4.0})

        # try to set a bad variable value
        with pytest.raises(ValueError):
            env._set_variables({"QUAD:IN20:525:BCTRL": 5.0})

        # try to set a bad variable name
        with pytest.raises(ValueError):
            env._set_variables({"bad_name": 5.0})

        # try to make a measurement using screen keys
        screen_meas_set = {
            "Cx", "Sx", "Cy", "Sy", "bb_penalty", "total_intensity",
            "log10_total_intensity"
        }
        for ele in ["Cx", "Sx", "Cy", "Sy"]:
            screen_result = env._get_observables([ele])
            assert screen_meas_set == set(screen_result.keys())
            assert len(screen_meas_set) == len(set(screen_result.keys()))

        # test measurement with duplicate keys for images
        screen_result = env._get_observables(["Cx", "Sx"])
        assert screen_meas_set == set(screen_result.keys())
        assert len(screen_meas_set) == len(set(screen_result.keys()))

        # test measurement with one image key and one other key
        mixed_result = env._get_observables(["Cx", "charge"])
        assert len(set(mixed_result.keys())) == len(screen_meas_set) + 1


