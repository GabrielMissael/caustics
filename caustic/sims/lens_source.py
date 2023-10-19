from .simulator import Simulator
from torch.nn.functional import avg_pool2d, conv2d
from typing import Tuple, Optional
import torch

__all__ = ("Lens_Source",)

class Lens_Source(Simulator):
    """Lens image of a source.
    
    Striaghtforward simulator to sample a lensed image of a source
    object. Constructs a sampling grid internally based on the
    pixelscale and gridding parameters. It can automatically upscale
    and fine sample an image. This is the most straightforward
    simulator to view the image if you aready have a lens and source
    chosen.

    Example usage::

       import matplotlib.pyplot as plt
       import caustic

       cosmo = caustic.FlatLambdaCDM()
       lens = caustic.lenses.SIS(cosmology = cosmo, x0 = 0., y0 = 0., th_ein = 1.)
       source = caustic.sources.Sersic(x0 = 0., y0 = 0., q = 0.5, phi = 0.4, n = 2., Re = 1., Ie = 1.)
       sim = caustic.sims.Lens_Source(lens, source, pixelscale = 0.05, gridx = 100, gridy = 100, upsample_factor = 2, z_s = 1.)
       
       img = sim()
       plt.imshow(img, origin = "lower")
       plt.show()

    Attributes:
      lens_mass: caustic lens mass model object
      source_light: caustic light object which defines the background source
      lens_light: caustic light object which defines the lensing object's light
      psf: An image to convolve with the scene. Note that if ``upsample_factor > 1`` the psf must also be at the higher resolution.
      pixelscale: pixelscale of the sampling grid.
      gridx: number of pixels on the x-axis for the sampling grid
      gridy: number of pixels on the y-axis for the sampling grid. If left as ``None`` then this will simply be equal to ``gridx``
      upsample_factor: Amount of upsampling to model the image. For example ``upsample_factor = 2`` indicates that the image will be sampled at double the resolution then summed back to the original resolution (given by pixelscale and gridx/y).
      psf_pad: If convolving the PSF it is important to sample the model in a larger FOV equal to half the PSF size in order to account for light that scatters from outside the requested FOV inwards. Internally this padding will be added before sampling, then cropped off before returning the final image to the user.
      z_s: redshift of the source
      name: a name for this simulator in the parameter DAG.

    """
    def __init__(
        self,
        lens_mass,
        source_light,
        lens_light = None,
        psf = None,
        pixelscale: float = 0.05,
        gridx: int = 100,
        gridy: Optional[int] = None,
        upsample_factor: int = 1,
        psf_pad = True,
        z_s = None,
        name: str = "sim",
    ):
        super().__init__(name)

        # Lensing models
        self.lens_mass = lens_mass
        self.source_light = source_light
        self.lens_light = lens_light
        self.psf = None if psf is None else torch.as_tensor(psf)
        self.add_param("z_s", z_s)

        # Image grid
        if gridy is None:
            gridy = gridx
        self.gridding = (gridx, gridy)

        # PSF padding if needed
        if psf_pad and self.psf is not None:
            self.psf_pad = (self.psf.shape[1]//2 + 1, self.psf.shape[0]//2 + 1)
        else:
            self.psf_pad = (0,0)

        # Build the imaging grid
        self.upsample_factor = upsample_factor
        npix = (self.gridding[0] + self.psf_pad[0]*2, self.gridding[1] + self.psf_pad[1]*2)
        tx = torch.linspace(-0.5 * (pixelscale * npix[0]), 0.5 * (pixelscale * npix[0]), npix[0]*upsample_factor)
        ty = torch.linspace(-0.5 * (pixelscale * npix[1]), 0.5 * (pixelscale * npix[1]), npix[1]*upsample_factor)
        self.grid = torch.meshgrid(tx, ty, indexing = "xy")
        
    def forward(self, params, sourcelight=True, lenslight=True, lenssource=True, psfconvolve=True):
        """
        params: Packed object
        sourcelight: when true the source light will be sampled
        lenslight: when true the lens light will be sampled
        lenssource: when true, the source light model will be lensed by the lens mass distribution 
        psfconvolve: when true the image will be convolved with the psf
        """
        z_s, = self.unpack(params)

        # Sample the source light
        if sourcelight:
            if lenssource:
                # Source is lensed by the lens mass distribution
                bx, by = self.lens_mass.raytrace(*self.grid, z_s, params)
                mu = self.source_light.brightness(bx, by, params)
            else:
                # Source is imaged without lensing
                mu = self.source_light.brightness(*self.grid, params)
        else:
            # Source is not added to the scene
            mu = torch.zeros_like(self.grid[0])

        # Sample the lens light
        if lenslight and self.lens_light is not None:
            mu += self.lens_light.brightness(*self.grid, params)

        # Convolve the PSF
        if psfconvolve and self.psf is not None:
            mu = conv2d(mu[None, None], self.psf[None, None], padding = "same").squeeze()

        # Return to the desired image
        mu_native_resolution = avg_pool2d(mu[None, None], self.upsample_factor, divisor_override = 1).squeeze()
        mu_clipped = mu_native_resolution[self.psf_pad[1]:self.gridding[1] + self.psf_pad[1], self.psf_pad[0]:self.gridding[0] + self.psf_pad[0]]
        return mu_clipped
