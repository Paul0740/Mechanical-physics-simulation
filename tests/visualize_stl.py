import numpy as np
from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Load STL file
your_stl_file = "BallCube.stl"  # Change this to your file name
stl_mesh = mesh.Mesh.from_file(your_stl_file)

# Extract vertices
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Create a list of faces
faces = stl_mesh.vectors
ax.add_collection3d(Poly3DCollection(faces, edgecolor="k"))

# Auto scale to the mesh size
scale = np.concatenate([stl_mesh.points]).flatten()
ax.auto_scale_xyz(scale, scale, scale)

plt.show()
