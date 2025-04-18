import torch

from ...constants import arcsec_to_rad, G_over_c2
from ...utils import translate_rotate


def convergence_0_pseudo_jaffe(mass, Rc, Rs, d_l, critical_surface_density):
    """
    Compute the convergence (dimensionless surface mass density). This is
    rearranged from Eliasdottir et al 2007 equation A11.

    Parameters
    ----------
    mass: Tensor
        Total mass of the lens (Msun).

        *Unit: Msun*

    Rc: Tensor
        Core radius of the lens.

        *Unit: arcsec*

    Rs: Tensor
        Scaling radius of the lens.

        *Unit: arcsec*

    d_l: Tensor
        Distance to the lens.

        *Unit: Mpc*

    critical_surface_density: Tensor
        Critical surface density of the universe at the lens redshift.

        *Unit: Msun / Mpc^2*

    Returns
    --------
    Tensor
        The convergence (dimensionless surface mass density) at the center of
        the pseudo jaffe.

        *Unit: unitless*

    """
    return mass / (2 * torch.pi * critical_surface_density * Rc * Rs * (d_l * arcsec_to_rad) ** 2)  # fmt: skip


def mass_enclosed_2d_pseudo_jaffe(radius, mass, Rc, Rs, s=0.0):
    """
    Compute the mass enclosed within a given radius. See Eliasdottir et al 2007 equation A10.

    Parameters
    ----------
    radius: Optional[Tensor]
        Radius at which to calculate enclosed mass (arcsec).

            *Unit: arcsec*

    mass: Tensor
        Total mass of the lens

        *Unit: Msun*

    Rc: Tensor
        Core radius of the lens.

        *Unit: arcsec*

    Rs: Tensor
        Scaling radius of the lens.

        *Unit: arcsec*

    """
    theta = radius + s
    frac_enclosed_num = (
        (Rc**2 + theta**2).sqrt() - Rc - (Rs**2 + theta**2).sqrt() + Rs
    )  # arcsec
    frac_enclosed_denom = Rs - Rc  # arcsec
    return mass * frac_enclosed_num / frac_enclosed_denom


def reduced_deflection_angle_pseudo_jaffe(
    x0, y0, mass, Rc, Rs, x, y, d_l, critical_surface_density, s=0.0
):
    """
    Compute the reduced deflection angle. See Eliasdottir et al 2007 equation A19.

    Parameters
    ----------
    x0: Tensor
        x-coordinate of the center of the lens.

        *Unit: arcsec*

    y0: Tensor
        y-coordinate of the center of the lens.

        *Unit: arcsec*

    mass: Tensor
        Total mass of the lens

        *Unit: Msun*

    Rc: Tensor
        Core radius of the lens.

        *Unit: arcsec*

    Rs: Tensor
        Scaling radius of the lens.

        *Unit: arcsec*

    x: Tensor
        x-coordinates in the lens plane.

        *Unit: arcsec*

    y: Tensor
        y-coordinates in the lens plane.

        *Unit: arcsec*

    d_l: Tensor
        Distance to the lens.

        *Unit: Mpc*

    critical_surface_density: Tensor
        Critical surface density of the universe at the lens redshift.

        *Unit: Msun / Mpc^2*

    s: float
        Softening parameter to prevent numerical instabilities.

        *Unit: arcsec*

    """
    x, y = translate_rotate(x, y, x0, y0)
    R = (x**2 + y**2).sqrt() + s
    f = R / Rc / (1 + (1 + (R / Rc) ** 2).sqrt()) - R / (Rs * (1 + (1 + (R / Rs) ** 2).sqrt()))  # fmt: skip
    alpha = 2 * convergence_0_pseudo_jaffe(mass, Rc, Rs, d_l, critical_surface_density) * Rc * Rs / (Rs - Rc) * f  # fmt: skip
    ax = alpha * x / R
    ay = alpha * y / R
    return ax, ay


def potential_pseudo_jaffe(x0, y0, mass, Rc, Rs, x, y, d_l, d_s, d_ls, s=0.0):
    """
    Compute the lensing potential for the pseudo jaffe lens. See Eliasdottir et
    al 2007 equation A18.

    Parameters
    ----------
    x0: Tensor
        x-coordinate of the center of the lens.

        *Unit: arcsec*

    y0: Tensor
        y-coordinate of the center of the lens.

        *Unit: arcsec*

    mass: Tensor
        Total mass of the lens

        *Unit: Msun*

    Rc: Tensor
        Core radius of the lens.

        *Unit: arcsec*

    Rs: Tensor
        Scaling radius of the lens.

        *Unit: arcsec*

    x: Tensor
        x-coordinates in the lens plane.

        *Unit: arcsec*

    y: Tensor
        y-coordinates in the lens plane.

        *Unit: arcsec*

    d_l: Tensor
        Distance to the lens.

        *Unit: Mpc*

    d_s: Tensor
        Distance to the source.

        *Unit: Mpc*

    d_ls: Tensor
        Distance from the lens to the source.

        *Unit: Mpc*

    s: float
        Softening parameter to prevent numerical instabilities.

        *Unit: arcsec*
    """
    x, y = translate_rotate(x, y, x0, y0)

    R_squared = x**2 + y**2 + s  # arcsec^2
    surface_density_0 = convergence_0_pseudo_jaffe(
        mass, Rc, Rs, d_l, 1.0
    )  # Msun / Mpc^2

    coeff = -(
        8
        * torch.pi
        * G_over_c2
        * surface_density_0
        * (d_l * d_ls / d_s)
        * Rc
        * Rs
        / (Rs - Rc)
    )  # arcsec

    scale_a = (Rs**2 + R_squared).sqrt()  # arcsec
    scale_b = (Rc**2 + R_squared).sqrt()  # arcsec
    scale_c = Rc * (Rc + (Rc**2 + R_squared).sqrt()).log()  # arcsec
    scale_d = Rs * (Rs + (Rs**2 + R_squared).sqrt()).log()  # arcsec
    scale_factor = scale_a - scale_b + scale_c - scale_d  # arcsec
    return coeff * scale_factor


def convergence_pseudo_jaffe(
    x0, y0, mass, Rc, Rs, x, y, d_l, critical_surface_density, s=0.0
):
    """
    Compute the convergence (dimensionless surface mass density). See Eliasdottir et al 2007 Equation A3.

    Parameters
    ----------
    x0: Tensor
        x-coordinate of the center of the lens.

        *Unit: arcsec*

    y0: Tensor
        y-coordinate of the center of the lens.

        *Unit: arcsec*

    mass: Tensor
        Total mass of the lens

        *Unit: Msun*

    Rc: Tensor
        Core radius of the lens.

        *Unit: arcsec*

    Rs: Tensor
        Scaling radius of the lens.

        *Unit: arcsec*

    x: Tensor
        x-coordinates in the lens plane.

        *Unit: arcsec*

    y: Tensor
        y-coordinates in the lens plane.

        *Unit: arcsec*

    d_l: Tensor
        Distance to the lens.

        *Unit: Mpc*

    critical_surface_density: Tensor
        Critical surface density of the universe at the lens redshift.

        *Unit: Msun / Mpc^2*

    s: float
        Softening parameter to prevent numerical instabilities.

        *Unit: arcsec*
    """

    x, y = translate_rotate(x, y, x0, y0)
    R_squared = x**2 + y**2 + s
    coeff = convergence_0_pseudo_jaffe(mass, Rc, Rs, d_l, critical_surface_density) * Rc * Rs / (Rs - Rc)  # fmt: skip
    return coeff * (1 / (Rc**2 + R_squared).sqrt() - 1 / (Rs**2 + R_squared).sqrt())  # fmt: skip
