
# visneb.py
# Siddharth Gautam, 2026

# This is the main driver file for visneb. It orchestrates the entire process of
# visualizing the NEB trajectory. The workflow is commented in the code.

# Execute with:
# python visneb.py neb.traj 5

# VMD will open for you to set the style, save it as style.vmd, then it will render 
# the last 5 images of neb.traj in batch mode, and create a PNG montage of the rendered 
# images. Finally, it will create an energy profile chart from the same images using Psi4.

# The result will be "neb-visualize.png" and "neb-chart.png" in the current directory.

import argparse
import re
import tempfile
import shutil

from pathlib import Path

from visneb_vmd import launchVMDforStyle, sanitizeStyleVMD, createVMDRenderScript, runVMDScript
from visneb_chart import bandPlotChart, computeEnergyPsi4, computeEnergyEMT
from utils import extractMEPImages, run, tga2png, createPNGmontage

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("traj", type=str, help="The NEB trajectory file (e.g., neb.traj) from ASE.")
    parser.add_argument("nimages", type=int, 
                    help="Number of images used in NEB calculation. Last N from the trajectory file will be extracted.")
    parser.add_argument("--psi4", action="store_true",
                    help="Use Psi4 instead of EMT potential")
    
    args = parser.parse_args()

    traj = Path(args.traj).resolve()
    outname = traj.with_suffix("").name + "-visualize.png"
    outname_chart = traj.with_suffix("").name + "-chart.png"

    if args.psi4:
        print("Using Psi4 for energy calculations (this may take a while)...")
        energy_func = computeEnergyPsi4
    else:
        print("Using EMT for energy calculations (fast, but less accurate)...")
        energy_func = computeEnergyEMT

    with tempfile.TemporaryDirectory(prefix="nebvis_") as tmpdir:

        print("Temporary directory:", tmpdir)

        # 1) Extract NEB
        poscars, xyzs = extractMEPImages(traj, args.nimages, tmpdir)

        # 2) User style setup
        style = launchVMDforStyle(tmpdir, xyzs[0])

        # 3) Clean style
        sanitizeStyleVMD(style)

        # 4) Render script
        render = createVMDRenderScript(tmpdir, xyzs)

        # 5) Batch render
        runVMDScript(tmpdir, render)

        # 6) Convert
        pngs = tga2png(tmpdir)

        # 7) Stitch
        createPNGmontage(tmpdir, pngs, outname)
        shutil.move(Path(tmpdir)/outname, Path.cwd()/outname)
        print("\nOutput:", outname)
        
        # 8) Energy profile chart
        bandPlotChart(tmpdir, outname_chart, energy_func=energy_func)

if __name__ == "__main__":
    main()