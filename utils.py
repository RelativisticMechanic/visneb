# visneb
# Siddharth Gautam, 2026

# This file contains utility functions.
import subprocess

from ase.io import read, write
from pathlib import Path
from PIL import Image

def extractMEPImages(traj, nimages, tmpdir):
    """
    Extract the last N images from a NEB trajectory file and save them in a temporary directory.
    The last N images are typically the ones that represent the MEP (Minimum Energy Path) after convergence.
    
     - traj: The filename of the NEB trajectory (e.g., "neb.traj")
     - nimages: The number of images to extract (e.g., 5)
     - tmpdir: The temporary directory to save the extracted images (e.g., "tmp/neb_images")
    
    The function reads the trajectory file, extracts the last N images, and saves each image in 
    both POSCAR and XYZ formats in the specified temporary directory. The files will be named 
    "image_000.POSCAR", "image_000.xyz", "image_001.POSCAR", "image_001.xyz", etc.
    """
    images = read(traj, ":")
    neb = images[-nimages:]

    poscars = []
    xyzs = []
    for i, atoms in enumerate(neb):
        path_POSCAR = Path(tmpdir) / f"image_{i:03d}.POSCAR"
        path_XYZ = Path(tmpdir) / f"image_{i:03d}.xyz"
        write(path_POSCAR, atoms, format="vasp")
        write(path_XYZ, atoms, format="xyz")
        poscars.append(path_POSCAR.name)
        xyzs.append(path_XYZ.name)

    return poscars, xyzs

def run(cmd, cwd=None, quiet=False):
    """
    Run a command as a subprocess, optionally in a specific working directory and with quiet output.
    
     - cmd: A list of command arguments (e.g., ["vmd", "-dispdev", "text", "-e", "render.tcl"])
     - cwd: The working directory to run the command in (optional)
     - quiet: If True, suppress stdout and stderr (optional)
    """

    printable = [str(c) for c in cmd]

    if not quiet:
        print(">>", " ".join(printable))

    stdout = subprocess.DEVNULL if quiet else None
    stderr = subprocess.DEVNULL if quiet else None

    subprocess.check_call(
        printable,
        cwd=str(cwd) if cwd else None,
        stdout=stdout,
        stderr=stderr
    )

def tga2png(tmpdir):
    
    """
    Convert all TGA images in the specified temporary directory to PNG format.
    
     - tmpdir: The temporary directory containing the TGA images (e.g., "tmp/neb_images")
    The function looks for files named "frame_XXX.tga", converts them to "frame_XXX.png", and saves them in the same directory.
     - Returns a list of the PNG filenames that were created.
     - Note: The original TGA files are not deleted, but the new PNG files will be created with the same base name.
    """

    tmpdir = Path(tmpdir)
    pngs = []

    for tga in sorted(tmpdir.glob("frame_*.tga")):
        png = tga.with_suffix(".png")

        with Image.open(tga) as im:
            # Normalize pixel format (important for some TGA variants)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA")
            else:
                im = im.copy()

            im.save(png, format="PNG", compress_level=6)

        pngs.append(png.name)

    return pngs


def createPNGmontage(tmpdir, pngs, output):
    """
    Combine multiple PNG images into a single montage image.
    
     - tmpdir: The temporary directory where the PNG images are located
     - pngs: A list of PNG filenames to combine (e.g., ["frame_00.png", "frame_01.png", "frame_02.png"])
     - output: The filename for the combined montage image (e.g., "montage.png")
    
    The function loads each PNG image, normalizes their heights (to account for any off-by-1 pixel issues from VMD), 
    and combines them horizontally into a single image. The combined image is saved in the same temporary directory 
    with the specified output filename.

     - Note: The original PNG files are not deleted, but the new montage image will be created with the specified name.
    """
    images = [Image.open(Path(tmpdir)/p).convert("RGBA") for p in pngs]

    # normalize height (important - VMD sometimes outputs off-by-1 pixels)
    max_h = max(img.height for img in images)

    normalized = []
    for img in images:
        if img.height != max_h:
            canvas = Image.new("RGBA", (img.width, max_h), (255,255,255,0))
            canvas.paste(img, (0, (max_h - img.height)//2))
            normalized.append(canvas)
        else:
            normalized.append(img)

    total_w = sum(img.width for img in normalized)

    combined = Image.new("RGBA", (total_w, max_h), (255,255,255,0))

    x = 0
    for img in normalized:
        combined.paste(img, (x, 0))
        x += img.width

    combined.save(Path(tmpdir)/output)