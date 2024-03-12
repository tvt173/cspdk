from __future__ import annotations

import inspect
from functools import cache, partial

import jax
import jax.numpy as jnp
import sax
from gplugins.sax.models import bend, grating_coupler, straight

from cspdk.tech import check_cross_section

nm = 1e-3

################
# PassThrus
################


@cache
def _2port(p1, p2):
    @jax.jit
    def _2port(wl=1.5) -> sax.SDict:
        wl = jnp.asarray(wl)
        return sax.reciprocal({(p1, p2): jnp.ones_like(wl)})

    return _2port


@cache
def _3port(p1, p2, p3):
    @jax.jit
    def _3port(wl=1.5) -> sax.SDict:
        wl = jnp.asarray(wl)
        thru = jnp.ones_like(wl) / jnp.sqrt(2)
        return sax.reciprocal(
            {
                (p1, p2): thru,
                (p1, p3): thru,
            }
        )

    return _3port


@cache
def _4port(p1, p2, p3, p4):
    @jax.jit
    def _4port(wl=1.5) -> sax.SDict:
        wl = jnp.asarray(wl)
        thru = jnp.ones_like(wl) / jnp.sqrt(2)
        cross = 1j * thru
        return sax.reciprocal(
            {
                (p1, p4): thru,
                (p2, p3): thru,
                (p1, p3): cross,
                (p2, p4): cross,
            }
        )

    return _4port


################
# Straights
################


def _straight(
    *,
    wl: float = 1.55,
    length: float = 10.0,
    loss: float = 0.0,
    cross_section="xs_sc",
) -> sax.SDict:
    if check_cross_section(cross_section) == "xs_sc":
        return straight_sc(wl=wl, length=length, loss=loss)
    elif check_cross_section(cross_section) == "xs_so":
        return straight_so(wl=wl, length=length, loss=loss)
    elif check_cross_section(cross_section) == "xs_rc":
        return straight_rc(wl=wl, length=length, loss=loss)
    elif check_cross_section(cross_section) == "xs_ro":
        return straight_ro(wl=wl, length=length, loss=loss)
    elif check_cross_section(cross_section) == "xs_nc":
        return straight_nc(wl=wl, length=length, loss=loss)
    elif check_cross_section(cross_section) == "xs_no":
        return straight_no(wl=wl, length=length, loss=loss)
    else:
        raise ValueError(f"Invalid cross section: Got: {cross_section}")


straight_sc = partial(straight, wl0=1.55, neff=2.4, ng=4.2)
straight_so = partial(straight, wl0=1.31, neff=2.4, ng=4.2)
straight_rc = partial(straight, wl0=1.55, neff=2.4, ng=4.2)
straight_ro = partial(straight, wl0=1.31, neff=2.4, ng=4.2)
straight_nc = partial(straight, wl0=1.55, neff=2.4, ng=4.2)
straight_no = partial(straight, wl0=1.31, neff=2.4, ng=4.2)

################
# Bends
################

_bend_s = _straight
_bend_euler = partial(bend, loss=0.03)
bend_sc = partial(_bend_euler, loss=0.03)
bend_so = partial(_bend_euler, loss=0.03)
bend_rc = partial(_bend_euler, loss=0.03)
bend_ro = partial(_bend_euler, loss=0.03)
bend_nc = partial(_bend_euler, loss=0.03)
bend_no = partial(_bend_euler, loss=0.03)

################
# Transitions
################

_taper = _straight
_taper_cross_section = _taper
trans_sc_rc10 = partial(_taper_cross_section, length=10.0)
trans_sc_rc20 = partial(_taper_cross_section, length=20.0)
trans_sc_rc50 = partial(_taper_cross_section, length=50.0)

################
# MMIs
################


def _mmi_amp(wl=1.55, wl0=1.55, fwhm=0.2, loss_dB=0.3):
    max_power = 10 ** (-abs(loss_dB) / 10)
    f = 1 / wl
    f0 = 1 / wl0
    f1 = 1 / (wl0 + fwhm / 2)
    f2 = 1 / (wl0 - fwhm / 2)
    _fwhm = f2 - f1

    sigma = _fwhm / (2 * jnp.sqrt(2 * jnp.log(2)))
    power = jnp.exp(-((f - f0) ** 2) / (2 * sigma**2))
    power = max_power * power / power.max() / 2
    amp = jnp.sqrt(power)
    return amp


def _mmi1x2(wl=1.55, wl0=1.55, fwhm=0.2, loss_dB=0.3) -> sax.SDict:
    thru = _mmi_amp(wl=wl, wl0=wl0, fwhm=fwhm, loss_dB=loss_dB)
    return sax.reciprocal(
        {
            ("o1", "o2"): thru,
            ("o1", "o3"): thru,
        }
    )


def _mmi2x2(wl=1.55, wl0=1.55, fwhm=0.2, loss_dB=0.3, shift=0.005) -> sax.SDict:
    thru = _mmi_amp(wl=wl, wl0=wl0, fwhm=fwhm, loss_dB=loss_dB)
    cross = 1j * _mmi_amp(wl=wl, wl0=wl0 + shift, fwhm=fwhm, loss_dB=loss_dB)
    return sax.reciprocal(
        {
            ("o1", "o3"): thru,
            ("o1", "o4"): cross,
            ("o2", "o3"): cross,
            ("o2", "o4"): thru,
        }
    )


_mmi1x2_o = partial(_mmi1x2, wl0=1.31)
_mmi1x2_c = partial(_mmi1x2, wl0=1.55)
_mmi2x2_o = partial(_mmi2x2, wl0=1.31)
_mmi2x2_c = partial(_mmi2x2, wl0=1.55)

mmi1x2_rc = _mmi1x2_c
mmi1x2_sc = _mmi1x2_c
mmi1x2_nc = _mmi1x2_c
mmi1x2_ro = _mmi1x2_o
mmi1x2_so = _mmi1x2_o
mmi1x2_no = _mmi1x2_o

mmi2x2_rc = _mmi2x2_c
mmi2x2_sc = _mmi2x2_c
mmi2x2_nc = _mmi2x2_c
mmi2x2_ro = _mmi2x2_o
mmi2x2_so = _mmi2x2_o
mmi2x2_no = _mmi2x2_o

##############################
# Evanescent couplers
##############################

_coupler = _mmi2x2
_coupler_o = partial(_coupler, wl0=1.31)
_coupler_c = partial(_coupler, wl0=1.55)
coupler_sc = _coupler_c
coupler_rc = _coupler_c
coupler_nc = _coupler_c
coupler_so = _coupler_o
coupler_ro = _coupler_o
coupler_no = _coupler_o

##############################
# grating couplers Rectangular
##############################


def _gc_rectangular(
    *,
    wl: float = 1.55,
    reflection: float = 0.0,
    reflection_fiber: float = 0.0,
    loss=0.0,
    wavelength=1.55,
    bandwidth: float = 40 * nm,
) -> sax.SDict:
    return grating_coupler(
        wl=wl,
        wl0=wavelength,
        reflection=reflection,
        reflection_fiber=reflection_fiber,
        loss=loss,
        bandwidth=bandwidth,
    )


_gcro = partial(_gc_rectangular, loss=6, bandwidth=35 * nm, wavelength=1.31)
_gcrc = partial(_gc_rectangular, loss=6, bandwidth=35 * nm, wavelength=1.55)
gc_rectangular_sc = _gcrc
gc_rectangular_so = _gcro
gc_rectangular_rc = _gcrc
gc_rectangular_ro = _gcro
gc_rectangular_nc = _gcrc
gc_rectangular_no = _gcro

##############################
# grating couplers Elliptical
##############################

_gc_elliptical = _gc_rectangular
_gceo = partial(_gc_elliptical, loss=6, bandwidth=35 * nm, wavelength=1.31)
_gcec = partial(_gc_elliptical, loss=6, bandwidth=35 * nm, wavelength=1.55)
gc_elliptical_sc = _gcec
gc_elliptical_so = _gceo
gc_elliptical_rc = _gcec
gc_elliptical_ro = _gceo
gc_elliptical_nc = _gcec
gc_elliptical_no = _gceo


################
# Crossings
################


@jax.jit
def _crossing(wl=1.5) -> sax.SDict:
    wl = jnp.asarray(wl)
    one = jnp.ones_like(wl)
    return sax.reciprocal(
        {
            ("o1", "o3"): one,
            ("o2", "o4"): one,
        }
    )


crossing_so = _crossing
crossing_rc = _crossing
crossing_sc = _crossing


################
# Models Dict
################


def get_models():
    models = {}
    for name, func in list(globals().items()):
        if not callable(func):
            continue
        _func = func
        while isinstance(_func, partial):
            _func = _func.func
        try:
            sig = inspect.signature(_func)
        except ValueError:
            continue
        if str(sig.return_annotation) == "sax.SDict":
            models[name] = func
    return models
