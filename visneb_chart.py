# visneb 
# Siddharth Gautam, 2026

# This file creates an energy curve from the NEB output
# and saves it as a PNG image. Styling is done professionally
# automatically.
import psi4
import re

import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from scipy.interpolate import CubicSpline
from ase.io import read
from ase.data import chemical_symbols
from ase.calculators.emt import EMT

def computeEnergyEMT(atoms):
    """
    Compute potential energy using the ASE EMT potential.
    Energy is returned in electronvolts (eV), same convention as Psi4 wrapper.
    """

    # attach calculator (overwrite safely)
    atoms.calc = EMT()

    # ASE returns energy in eV
    energy = atoms.get_potential_energy()

    return energy

def computeEnergyPsi4(atoms, basis="def2-SVP", scf_type="df", reference="rhf"):
    """
    Compute the energy of a given ASE Atoms object using Psi4.
    Energy is returned in electronvolts (eV).
    """

    # build psi4 geometry string
    geom = []
    for Z, pos in zip(atoms.numbers, atoms.positions):
        sym = chemical_symbols[Z]
        geom.append(f"{sym} {pos[0]} {pos[1]} {pos[2]}")

    molstr = "0 1\n" + "\n".join(geom)

    mol = psi4.geometry(molstr)

    psi4.core.set_output_file("/dev/null", False)

    psi4.set_options({
        "basis": basis,
        "scf_type": scf_type,
        "reference": reference,
        "e_convergence": 1e-8,
        "d_convergence": 1e-8
    })

    energy = psi4.energy("scf", molecule=mol)

    # Hartree -> eV
    return energy * 27.211386245988

def bandPlotChart(tmpdir, outname, energy_func=computeEnergyEMT):
    """
    Generate a band energy plot from NEB image files in a temporary directory.
    This function looks for files named "image_XXX.POSCAR" in the specified directory,
    computes their energies using Psi4, and creates a smooth energy profile plot.

    The outname parameter specifies the filename for the saved energy profile plot (PNG format).
    It will be saved in the current working directory.
    """
    
    tmpdir = Path(tmpdir)

    # Find all POSCAR files matching the pattern "image_XXX.POSCAR"
    regex = re.compile(r"image_(\d{3})\.POSCAR")
    files = []

    for f in tmpdir.iterdir():
        m = regex.match(f.name)
        if m:
            files.append((int(m.group(1)), f))

    if not files:
        raise RuntimeError("No image_XXX.POSCAR files found")

    files.sort(key=lambda x: x[0])
    indices = []
    energies = []

    print("\nComputing energies:")
    for i, path in files:
        atoms = read(path)
        E = energy_func(atoms)

        print(f"  image {i:03d} : {E:.6f} eV")

        indices.append(i)
        energies.append(E)

    indices = np.array(indices)
    energies = np.array(energies)

    # shift minimum to zero (standard NEB plotting convention)
    energies -= energies.min()

    # Plotting
    plt.figure(figsize=(7.2,4.2), dpi=220)

    bg = "white"
    linecolor = "#1f77b4"

    # reaction coordinate (normalized distance)
    x = np.arange(len(energies))

    # smooth interpolation
    x_dense = np.linspace(x.min(), x.max(), 400)
    cs = CubicSpline(x, energies, bc_type="natural")
    y_smooth = cs(x_dense)

    # smooth curve
    plt.plot(
        x_dense,
        y_smooth,
        color=linecolor,
        linewidth=2.6,
        zorder=2
    )

    # actual computed images
    plt.scatter(
        x,
        energies,
        s=44,
        facecolor=linecolor,
        edgecolor=bg,
        linewidth=1.6,
        zorder=3
    )

    # styling
    plt.grid(True, linestyle=(0,(4,4)), linewidth=0.7, alpha=0.6)
    plt.xlabel("Reaction Coordinate", fontsize=13)
    plt.ylabel("Relative Energy (eV)", fontsize=13)

    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)

    for spine in ["top","right"]:
        plt.gca().spines[spine].set_visible(False)

    plt.gca().spines["left"].set_linewidth(1.2)
    plt.gca().spines["bottom"].set_linewidth(1.2)

    plt.tight_layout()
    plt.savefig(outname, dpi=200)
    plt.close()

    print(f"\nSaved energy profile: {outname}!")