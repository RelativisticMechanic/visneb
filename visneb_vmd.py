# visneb
# Siddharth Gautam, 2026

# This file is responsible for visualizing the NEB images using VMD. It expects a
# temporary directory containing the last N NEB images in XYZ format, VMD is opened
# for the user to set the style, and then the style is sanitized for batch rendering.

from utils import run
from pathlib import Path

def launchVMDforStyle(tmpdir, first_file):
    print("\n*** Launching VMD ***")
    
    print(("Edit representation, then SAVE VISUALIZATION STATE as 'style.vmd'"
            "\n\nNOTE: Make sure you save in the temporary directory created.\n"
            "The program will be started in the temporary directory, so you don't have to"
            " worry about navigating to the files.\n"""))
    
    print("Close VMD when done.\n")

    input("Press Enter to continue...")
    
    run(["vmd", first_file], cwd=tmpdir)

    style = Path(tmpdir) / "style.vmd"
    if not style.exists():
        raise RuntimeError("style.vmd not created")

    return style

def sanitizeStyleVMD(style_path):
    """
    Remove commands from the saved style that would interfere with batch rendering.
    Specifically, we want to remove any "mol new" or "mol delrep" commands that VMD saves,
    because we will be loading new files in a loop during batch rendering.  
    """

    banned_prefixes = (
        "mol new",
        "mol delrep"
    )

    cleaned = []
    with open(style_path) as f:
        for line in f:
            stripped = line.strip()

            if any(stripped.startswith(p) for p in banned_prefixes):
                continue

            cleaned.append(line)

    with open(style_path, "w") as f:
        f.writelines(cleaned)

def createVMDRenderScript(tmpdir, xyzs):
    """
    Creates a TCL script for VMD to render the NEB images in batch mode using the saved style.
     - tmpdir: The temporary directory where the POSCAR files and style.vmd are located
     - XYZ: A list of XYZ filenames corresponding to the NEB images to be rendered
    The script will load each XYZ file, apply the saved style, render it to a TGA image.
    The script will be saved as "render.tcl" in the temporary directory.
     - Returns the path to the created TCL script.
     - Note: The style.vmd file should already be sanitized before running this script.
     - Note: The output images will be named "frame_XX.tga" where XX is the index of the image.
    """

    tcl = Path(tmpdir) / "render.tcl"

    with open(tcl, "w") as f:
        f.write("""
            display projection Orthographic
            axes location Off
            color Display Background gray

            light 0 on
            light 1 on
            light 2 on
            light 3 off
            """)

        f.write("set files {\n")
        for i, file in enumerate(xyzs):
            f.write(f"    {file}\n")
        
        f.write("}\n")

        f.write("""
            set i 0
            foreach f $files {

                puts "Rendering $f"

                mol new $f type xyz waitfor all

                # Apply saved visual style
                source style.vmd

                # Render
                set out [format "frame_%02d.tga" $i]
                render TachyonInternal $out

                # Cleanup
                mol delete top
                incr i
            }
            quit
            """)

    return tcl

def runVMDScript(tmpdir, script):
    """
    Runs VMD in text mode to execute the given TCL script.
     - tmpdir: The temporary directory where the TCL script is located
     - script: The filename of the TCL script to execute (e.g., "render.tcl")
    """

    run(["vmd", "-dispdev", "text", "-e", script], cwd=tmpdir)