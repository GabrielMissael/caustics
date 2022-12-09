from abc import abstractmethod
from typing import Any, List, Tuple

import torch
from torch import Tensor

from .base import AbstractThickLens, AbstractThinLens


class MultiplaneLens(AbstractThickLens):
    def __init__(self, lenses: List[AbstractThinLens], device=torch.device("cpu")):
        """
        Args:
            lenses: list of instances of thin lenses.
        """
        super().__init__(device)
        self.lenses = lenses

    def raytrace(
        self, thx, thy, z_s, cosmology, z_ls: Tensor, lens_args: List[Tuple[Any, ...]]
    ) -> Tuple[Tensor, Tensor]:
        """
        Reduced deflection angle [arcsec].

        Args:
            z_ls: lens redshifts
            lens_arg_list: list of args to pass to each lens.
        """
        # TODO: implement
        for z_l, i in zip(torch.sort(z_ls)):
            lens = self.lenses[i]
            # Should be able to get physical deflection field with:
            #     lens.alpha_hat(thx, thy, z_l, z_l_next, cosmology, *lens_args[i])

        ...

    def alpha(
        self, thx, thy, z_s, cosmology, z_ls: Tensor, lens_args: List[Tuple[Any, ...]]
    ) -> Tuple[Tensor, Tensor]:
        """
        Reduced deflection angle [arcsec].
        """
        bx, by = self.raytrace(thx, thy, z_s, cosmology, z_ls, lens_args)
        return thx - bx, thy - by

    @abstractmethod
    def Sigma(self, thx, thy, z_s, cosmology, *args, **kwargs) -> Tensor:
        """
        Projected mass density.

        Returns:
            [solMass / Mpc^2]
        """
        # TODO: rescale mass densities of each lens and sum
        ...

    @abstractmethod
    def time_delay(self, thx, thy, z_s, cosmology, *args, **kwargs):
        # TODO: figure out how to compute this
        ...


# class MultiplaneLens(Base):
#     def __init__(self, lenses: List[AbstractThinLens], cosmology, device):
#         super().__init__(cosmology, device)
#         self.lenses = sorted(lenses, key=lambda lens: lens.z_l)
#
#     def _raytrace_to(self, thx_0, thy_0, ahx_sum, ahy_sum, ahx_chi_sum, ahy_chi_sum, z):
#         chi = self.cosmology.comoving_dist(z)
#         d_l = chi / (1 + z)  # angular diameter distance
#         # Apply recursion relation
#         xix = (chi * (thx_0 - ahx_sum) + ahx_chi_sum) / (1 + z) * arcsec_to_rad
#         xiy = (chi * (thy_0 - ahy_sum) + ahy_chi_sum) / (1 + z) * arcsec_to_rad
#         # Convert to angular coordinates to compute deflection field from lens i
#         thx = xix / d_l * rad_to_arcsec
#         thy = xiy / d_l * rad_to_arcsec
#         return thx, thy
#
#     def raytrace(self, thx, thy, z_ss):
#         assert thx.shape == thy.shape
#         thxy_final_shape = (*z_ss.shape, *thx.shape)
#         z_ss = torch.atleast_1d(z_ss)
#
#         thxs = torch.zeros_like(thx).repeat((len(z_ss), *(1 for _ in range(thx.ndim))))
#         thys = torch.zeros_like(thy).repeat((len(z_ss), *(1 for _ in range(thy.ndim))))
#         thx_0 = thx
#         thy_0 = thy
#
#         # Initial conditions
#         ahx_sum = torch.zeros_like(thx)
#         ahy_sum = torch.zeros_like(thy)
#         ahx_chi_sum = torch.zeros_like(thx)
#         ahy_chi_sum = torch.zeros_like(thy)
#         idx_cur_source = 0
#         z_s = z_ss[idx_cur_source]
#
#         for lens in self.lenses:
#             # Multiple sources can lie between lens planes
#             while z_s <= lens.z_l:
#                 # Ray-trace to current sources' redshift
#                 thx, thy = self._raytrace_to(
#                     thx_0, thy_0, ahx_sum, ahy_sum, ahx_chi_sum, ahy_chi_sum, z_s
#                 )
#                 thxs[idx_cur_source] = thx
#                 thys[idx_cur_source] = thy
#
#                 idx_cur_source += 1
#                 z_s = z_ss[idx_cur_source]
#
#                 if idx_cur_source == len(z_ss) - 1:
#                     return thxs, thys
#
#             # Ray-trace to current lens plane
#             thx, thy = self._raytrace_to(
#                 thx_0, thy_0, ahx_sum, ahy_sum, ahx_chi_sum, ahy_chi_sum, lens.z_l
#             )
#             ahx, ahy = lens.alpha_hat(thx, thy, z_s)
#
#             # Update sums
#             ahx_sum += ahx
#             ahy_sum += ahy
#             chi = self.cosmology.comoving_dist(lens.z_l)
#             ahx_chi_sum += chi * ahx
#             ahy_chi_sum += chi * ahy
#
#         # Multiple sources can lie beyond the last lens plane
#         for idx in range(idx_cur_source, len(z_ss)):
#             z_s = z_ss[idx]
#             thx, thy = self._raytrace_to(
#                 thx_0, thy_0, ahx_sum, ahy_sum, ahx_chi_sum, ahy_chi_sum, z_s
#             )
#             thxs[idx_cur_source] = thx
#             thys[idx_cur_source] = thy
#
#         return thxs.reshape(thxy_final_shape), thys.reshape(thxy_final_shape)
#
#     def Sigma(self, thx, thy, z_s):
#         ...
#
#     def kappa(self, thx, thy, z_s):
#         ...
#
#     def Psi(self, thx, thy, z_s):
#         ...
