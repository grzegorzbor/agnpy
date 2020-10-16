# test on synchrotron module
import pytest
import numpy as np
from pathlib import Path
import astropy.units as u
from astropy.constants import m_e, c, h
from astropy.coordinates import Distance
from agnpy.emission_regions import Blob
from agnpy.synchrotron import Synchrotron, nu_synch_peak, epsilon_B
from .utils import (
    make_comparison_plot,
    extract_columns_sample_file,
    check_deviation_within_bounds,
)

mec2 = m_e.to("erg", equivalencies=u.mass_energy())
epsilon_equivalency = [
    (u.Hz, u.Unit(""), lambda x: h.cgs * x / mec2, lambda x: x * mec2 / h.cgs)
]
agnpy_dir = Path(__file__).parent.parent.parent
data_dir = f"{agnpy_dir}/data"

# variables with _test are global and meant to be used in all tests
# here as a default we use the same parameters of Figure 7.4 in Dermer Menon 2009
spectrum_norm_test = 1e48 * u.Unit("erg")
p_test = 2.8
gamma_min_test = 1e2
gamma_max_test = 1e5
pwl_dict_test = {
    "type": "PowerLaw",
    "parameters": {
        "p": p_test,
        "gamma_min": gamma_min_test,
        "gamma_max": gamma_max_test,
    },
}
# blob parameters
R_b_test = 1e16 * u.cm
B_test = 1 * u.G
z_test = Distance(1e27, unit=u.cm).z
delta_D_test = 10
Gamma_test = 10
pwl_blob_test = Blob(
    R_b_test,
    z_test,
    delta_D_test,
    Gamma_test,
    B_test,
    spectrum_norm_test,
    pwl_dict_test,
)


class TestSynchrotron:
    """class grouping all tests related to the Synchrotron class"""

    def test_synch_reference_sed(self):
        """test agnpy synchrotron SED against the one sampled from Figure
        7.4 of Dermer Menon 2009"""
        nu_ref, sed_ref = extract_columns_sample_file(
            f"{data_dir}/sampled_seds/synch_figure_7_4_dermer_menon_2009.txt",
            "Hz",
            "erg cm-2 s-1",
        )
        # recompute the SED at the same ordinates where the figure was sampled
        synch = Synchrotron(pwl_blob_test)
        sed_agnpy = synch.sed_flux(nu_ref)
        # sed comparison plot
        make_comparison_plot(
            nu_ref,
            sed_ref,
            sed_agnpy,
            "Figure 7.4, Dermer and Menon (2009)",
            "agnpy",
            "Synchrotron",
            f"{data_dir}/crosscheck_figures/synch_comparison_figure_7_4_dermer_menon_2009.png",
            "sed",
        )
        # requires that the SED points deviate less than 15% from the figure
        assert check_deviation_within_bounds(nu_ref, sed_ref, sed_agnpy, 0, 0.15)

    @pytest.mark.parametrize(
        "file_ref , spectrum_type, spectrum_parameters, figure_title, figure_path",
        [
            (
                f"{data_dir}/sampled_seds/synch_ssa_pwl_jetset_1.1.2.txt",
                "PowerLaw",
                {"p": 2, "gamma_min": 2, "gamma_max": 1e6},
                "Self-Absorbed Synchrotron, power-law electron distribution",
                f"{data_dir}/crosscheck_figures/ssa_pwl_comparison_jetset_1.1.2.png",
            ),
            (
                f"{data_dir}/sampled_seds/synch_ssa_bpwl_jetset_1.1.2.txt",
                "BrokenPowerLaw",
                {"p1": 2, "p2": 3, "gamma_b": 1e4, "gamma_min": 2, "gamma_max": 1e6},
                "Self-Absorbed Synchrotron, broken power-law electron distribution",
                f"{data_dir}/crosscheck_figures/ssa_bpwl_comparison_jetset_1.1.2.png",
            ),
            (
                f"{data_dir}/sampled_seds/synch_ssa_lp_jetset_1.1.2.txt",
                "LogParabola",
                {"p": 2, "q": 0.4, "gamma_0": 1e4, "gamma_min": 2, "gamma_max": 1e6},
                "Self-Absorbed Synchrotron, log-parabola electron distribution",
                f"{data_dir}/crosscheck_figures/ssa_lp_comparison_jetset_1.1.2.png",
            ),
        ],
    )
    def test_ssa_reference_sed(
        self, file_ref, spectrum_type, spectrum_parameters, figure_title, figure_path,
    ):
        """test SSA SED generated by a given electron distribution against the 
        ones generated with jetset version 1.1.2, via jetset_ssa_sed.py script"""
        nu_ref, sed_ref = extract_columns_sample_file(file_ref, "Hz", "erg cm-2 s-1")
        # same parameters used to produce the jetset SED
        spectrum_norm = 1e2 * u.Unit("cm-3")
        spectrum_dict = {"type": spectrum_type, "parameters": spectrum_parameters}
        blob = Blob(
            R_b=5e15 * u.cm,
            z=0.1,
            delta_D=10,
            Gamma=10,
            B=0.1 * u.G,
            spectrum_norm=spectrum_norm,
            spectrum_dict=spectrum_dict,
        )
        # recompute the SED at the same ordinates where the figure was sampled
        ssa = Synchrotron(blob, ssa=True)
        sed_agnpy = ssa.sed_flux(nu_ref)
        # sed comparison plot
        make_comparison_plot(
            nu_ref,
            sed_ref,
            sed_agnpy,
            "jetset 1.1.2",
            "agnpy",
            figure_title,
            figure_path,
            "sed",
        )
        # requires that the SED points deviate less than 5% from the figure
        # there are divergencies at very low and very high energies, therefore
        # we will check between 10^(11) and 10^(19) Hz
        nu_range = [1e11, 1e19] * u.Hz
        assert check_deviation_within_bounds(
            nu_ref, sed_ref, sed_agnpy, 0, 0.05, nu_range
        )

    def test_nu_synch_peak(self):
        gamma = 100
        nu_synch = nu_synch_peak(B_test, gamma).to_value("Hz")
        assert np.isclose(nu_synch, 27992489872.33304, atol=0)

    def test_epsilon_B(self):
        assert np.isclose(epsilon_B(B_test), 2.2655188038060715e-14, atol=0)
