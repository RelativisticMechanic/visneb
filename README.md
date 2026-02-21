## Visneb

This is a small set of Python scripts that allows you to visualize the result
of an NEB calculation. 

The purpose of the scripts is to create two files:

1. An image showing the evolution of molecular geometry across NEB images
2. An image showing energy curve

### Dependencies

- miniconda / conda
- vmd

The Python dependencies are in environment.yml. Once you have VMD and conda installed
switch to the directory with the Python files and run:

```
conda env create -f environment.yml
```

Next, you may want to relocate the ```visneb``` script in your bin folder. You just need
to modify the $VISNEB_ROOT variable in the script to where you have placed the *.py files.

### Usage

After you do an ASE NEB calculation, you get a *.traj file. Suppose you have done the NEB
calculation using 11 images and the file is called neb.traj, you run with:

```
visneb neb.traj 11
```

This will extract the last 11 images from the neb.traj and create a temporary folder where
each image will have a POSCAR and an XYZ saved. 

Next, *VMD* will be opened in this temporary directory with the first image. You can set the
style of the rendering, etc., and then you must SAVE the visualization state as *style.vmd* 
in the *SAME temporary directory* (vmd will open in this so you don't need to navigate).

One saved, the program will create a montage of all the NEB images and save it to your 
*current working directory* as ```neb-visualize.png``` (if filename is neb.traj).

The program will also save an image vs energy chart using matplotlib called ```neb-chart.png```.

### Psi4

By default the program uses ASE EMT to calculate the energy. This is fast but inaccurate. If
you want a more accurate energy calculation (but this will take a lot of time!), you can do:

```
visneb --psi4 neb.traj 11 
```

This will use Psi4 as the backend.